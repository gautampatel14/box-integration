import logging
import logging.handlers
import traceback

from box_client import BoxClient
from box_helper import flatten_json_obj, get_delayed
from box_input_loader import BoxLoadData
from checkpoint import CustomCheckpointer, hanlde_folder_comments_ckpt
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from consts import USER_FIELDS, COLLABORATION_FIELDS, COMMENT_FIELDS, TASK_FIELDS


MAX_WORKERS = 10


class BoxBase:
    def __init__(
        self, logger, client, account_name, input_name, input_items, ckpt_name
    ) -> None:
        self.logger = logger
        self.client = client
        self.account_name = account_name
        self.input_name = input_name
        self.ckpt_name = ckpt_name
        self.input_items = input_items

    def collect_endpoint_data(self, uri, method, params):
        return self.client.make_api_request(uri, method, params)


class BoxEvents(BoxBase):
    def __init__(
        self, logger, client, account_name, input_name, input_items, ckpt_name
    ) -> None:
        super().__init__(
            logger, client, account_name, input_name, input_items, ckpt_name
        )
        self.uri = "events"
        self.method = "GET"
        self.params = {
            "stream_type": "admin_logs",
            "stream_position": 0,
            "created_after": f"{input_items.get('created_after')}-00:00",
            "limit": 100,
        }

    def collect_data(self):
        """
        Collect the events(admin_logs) from the box API

        Returns:
            dict: response of the API call
        """
        event_delay = self.input_items.get("event_delay", 0)
        self.logger.info(
            "Start collecting data for {}: {}".format(self.ckpt_name, self.input_name)
        )
        while True:
            checkpoint_obj = CustomCheckpointer(
                self.logger, self.account_name, self.input_name, self.ckpt_name
            )
            status, ckpt_value = checkpoint_obj.get_file_checkpoint()

            # If checkpoint value exist in file
            if status:
                self.logger.info(
                    "Stream position in checkpoint: {}".format(
                        ckpt_value.get("next_stream_position")
                    )
                )

                next_stream_position = ckpt_value.get("next_stream_position")

                self.params.update({"created_after": ckpt_value.get("created_at")})
                self.params.update({"stream_position": next_stream_position})

            response = super().collect_endpoint_data(self.uri, self.method, self.params)

            if response.status_code == 200:
                data = response.json()
                next_stream_position = data.get("next_stream_position")

                if len(data.get("entries")) == 0:
                    self.logger.info(
                        "No data found for {}: {}".format(
                            self.ckpt_name, self.input_name
                        )
                    )
                    ckpt_value = {
                        "created_at": get_delayed(
                            self.logger, ckpt_value.get("created_at"), event_delay
                        ),
                        "next_stream_position": next_stream_position,
                    }
                    checkpoint_obj.update_file_checkpoint(ckpt_value)
                    break

                last_created_at = data.get("entries")[-1].get("created_at")
                yield data

                ckpt_value = {
                    "created_at": get_delayed(
                        self.logger, last_created_at, event_delay
                    ),
                    "next_stream_position": next_stream_position,
                }
                checkpoint_obj.update_file_checkpoint(ckpt_value)


class BoxFolders(BoxBase):
    def __init__(
        self, logger, client, account_name, input_name, input_items, ckpt_name
    ) -> None:
        super().__init__(
            logger, client, account_name, input_name, input_items, ckpt_name
        )
        self.uri = ""
        self.method = "GET"
        self.params = {}
        self.folders_id_list = []
        self.files_id_list = []

    def get_file_folder_ids(self, folder_id):
        """
        This function is used to get the folder and file ids from the box API
        Args:
            folder_id (str): folder id to get the data
        """

        self.uri = f"folders/{folder_id}/items"
        response = super().collect_endpoint_data(self.uri, self.method, self.params)
        data = response.json()
        if "entries" in data:
            for item in data["entries"]:
                if item["type"] == "folder":
                    self.folders_id_list.append(item["id"])
                    self.get_file_folder_ids(item["id"])
                elif item["type"] == "file":
                    self.files_id_list.append(item["id"])

    def collect_data(self):
        """
        Collect the folders and files from the box API

        Returns:
            dict: response of the API call
        """
        self.logger.info(
            "Start collecting data for {}: {}".format(self.ckpt_name, self.input_name)
        )

        if all(value == "0" for value in self.input_items.values()):
            self.logger.warn(
                "No input items selected for {}: {}".format(
                    self.ckpt_name, self.input_name
                )
            )
        else:
            # Generate IDs starting from ROOT
            self.get_file_folder_ids(0)
            self.logger.info(
                "Folder ID list: {} \n File ID list: {}".format(
                    self.folders_id_list, self.files_id_list
                )
            )

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                tasks = [
                    executor.submit(self.generate_data, "folders")
                    if self.input_items.get("collect_folder") == "1"
                    else None,
                    executor.submit(self.generate_data, "files")
                    if self.input_items.get("collect_file") == "1"
                    else None,
                    executor.submit(self.generate_data, "comments")
                    if self.input_items.get("collect_task") == "1"
                    else None,
                    executor.submit(self.generate_data, "collaborations")
                    if self.input_items.get("collect_collaboration") == "1"
                    else None,
                ]
                for future in tasks:
                    if future:
                        yield from future.result()

    def generate_data(self, types):
        """
        This function is used to generate data for the given types
        Args:
            types (str): describe the types of data

        Returns:
            dict: return response from BOX API.
        """
        with ThreadPoolExecutor(max_workers=4) as executor:
            if types == "comments":
                futures = [
                    executor.submit(self.fetch_data, id, "files", "comments")
                    for id in self.files_id_list
                ]
                futures = [
                    executor.submit(self.fetch_data, id, "files", "task")
                    for id in self.files_id_list
                ]

            elif types == "collaborations":
                futures = [
                    executor.submit(self.fetch_data, id, "folders", "collaborations")
                    for id in self.folders_id_list
                ]
            else:
                futures = [
                    executor.submit(self.fetch_data, id, types, "metadata")
                    for id in (
                        self.folders_id_list
                        if types == "folders"
                        else self.files_id_list
                    )
                ]

            for future in futures:
                result = future.result()
                if result.get("entries"):
                    yield result

    def fetch_data(self, id, types, data_type):
        """
        This functino is used to fetch data from BOX API

        Args:
            id (str): either file or folder ids to fetch data.
            types (str): prefix of the uri
            data_type (str): describe the types of data

        Returns:
            dict: return response from BOX API.
        """
        if data_type == "metadata":
            uri = f"{types}/{id}/metadata"
            logger_info = "Generating metadata for {} ID: {}".format(types, id)

        elif data_type == "comments":
            self.params.update({"fields": COMMENT_FIELDS})
            uri = f"files/{id}/comments"
            logger_info = "Generating comments for file ID: {}".format(id)
            self.logger.info(logger_info)

        elif data_type == "task":
            self.params.update({"fields": TASK_FIELDS})
            uri = f"files/{id}/tasks"
            logger_info = "Generating tasks for file ID: {}".format(id)

        elif data_type == "collaborations":
            self.params.update({"fields": COLLABORATION_FIELDS})
            uri = f"folders/{id}/collaborations"
            logger_info = "Generating collaborations for folder ID: {}".format(id)

        self.logger.info(logger_info)
        response = super().collect_endpoint_data(uri, self.method, self.params)
        output = response.json()

        # handle checkpointing if data_type in ("comments", "collaborations")
        if data_type in ("collaborations", "comments", "task"):
            if output.get("entries"):
                ckpt_field_name = (
                    "modified_at" if data_type == "collaborations" else "created_at"
                )
                details = {
                    "account_name": self.account_name,
                    "input_name": self.input_name,
                    "ckpt_name": self.ckpt_name + f"_{data_type}",
                }
                output_res = hanlde_folder_comments_ckpt(
                    self.logger, id, ckpt_field_name, output, **details
                )
                output.update(output_res)

        return output


class BoxUsers(BoxBase):
    def __init__(
        self, logger, client, account_name, input_name, input_items, ckpt_name
    ) -> None:
        super().__init__(
            logger, client, account_name, input_name, input_items, ckpt_name
        )
        self.uri = "users"
        self.method = "GET"
        self.params = {"limit": 50, "offset": 0, "fields": USER_FIELDS}

    def collect_data(self):
        """
        Collect the users data from the Box API
        """

        self.logger.info(
            "Start collecting data for {}: {}".format(self.ckpt_name, self.input_name)
        )
        try:
            result = []
            while True:
                chunk_response = super().collect_endpoint_data(
                    self.uri, self.method, self.params
                )
                chunk_response = chunk_response.json()
                result.extend(chunk_response.get("entries"))
                self.params["offset"] += self.params["limit"]

                if chunk_response.get("total_count") <= self.params.get("offset"):
                    self.logger.info(
                        "All users data collected Successfully: {}".format(
                            self.input_name
                        )
                    )
                    break

            result = self.user_checkpoint(result)
            ckpt_response = {"entries": result, "total_count": len(result)}
            # contain updated response.
            yield ckpt_response

            self.logger.info(
                "Data collection completed for {} endpoint: {}".format(
                    self.ckpt_name, self.input_name
                )
            )

        except Exception as e:
            self.logger.error(
                "Error occured while collecting data for {} endpoint: {}".format(
                    self.ckpt_name, self.input_name
                )
            )
            raise e

    def user_checkpoint(self, response: list) -> list:
        """
        Checkpoint function for the user list

        Args:
            response (list): list of user dict

        Returns:
            list: user list after checkpointing
        """
        self.logger.info(
            "Start checkpointing the data for {}: {}".format(
                self.ckpt_name, self.input_name
            )
        )
        try:
            checkpoint = CustomCheckpointer(
                self.logger, self.account_name, self.input_name, self.ckpt_name
            )
            status, ckpt_value = checkpoint.get_file_checkpoint()

            if not status:
                last_modified_at = response[0].get("modified_at")
                last_modified_at = datetime.strptime(
                    last_modified_at, "%Y-%m-%dT%H:%M:%S%z"
                )
                for user in response:
                    user_modified_at = datetime.strptime(
                        user.get("modified_at"), "%Y-%m-%dT%H:%M:%S%z"
                    )
                    if user_modified_at > last_modified_at:
                        last_modified_at = user_modified_at

                last_modified_at = last_modified_at.strftime("%Y-%m-%dT%H:%M:%S%z")
                ckpt_value = {"modified_at": last_modified_at}
                checkpoint.update_file_checkpoint(ckpt_value)
                return response

            ckpt_response = []
            last_modified_at = datetime.strptime(
                ckpt_value.get("modified_at"), "%Y-%m-%dT%H:%M:%S%z"
            )
            latest_modified_at = last_modified_at
            for user in response:
                user_modified_at = datetime.strptime(
                    user.get("modified_at"), "%Y-%m-%dT%H:%M:%S%z"
                )
                if user_modified_at > latest_modified_at:
                    latest_modified_at = user_modified_at
                if user_modified_at > last_modified_at:
                    ckpt_response.append(user)

            last_modified_at = latest_modified_at.strftime("%Y-%m-%dT%H:%M:%S%z")
            ckpt_value.update({"modified_at": last_modified_at})
            checkpoint.update_file_checkpoint(ckpt_value)
            self.logger.info(
                "Successfully completed the checkpoint of {}: {}".format(
                    self.ckpt_name, self.input_name
                )
            )
            return ckpt_response
        except Exception as e:
            self.logger.error(
                "Error occured while checkpointing the data for {}: {} \n Traceback: {}".format(
                    self.ckpt_name, self.input_name, traceback.format_exc()
                )
            )
            raise e


class BoxCollector:
    def __init__(
        self,
        logger: logging.Logger,
        box_credential: dict,
        context,
        input_name: str,
        input_items: dict,
        event_write,
    ) -> None:
        self.logger = logger
        self._box_credential = box_credential
        self._context = context
        self.input_name = input_name
        self.input_items = input_items
        self.event_write = event_write

    def collect_data(self):
        """
        This method is collect the events from different endpoint.

        Returns:
            tuple: Returns status of the API call, collected data and dict
            containing of index, sourcetype
        """
        try:
            endpoint = self.input_items.get("rest_endpoint")
            account_name = self._context.get("account")
            ckpt_key = endpoint
            self.logger.info(
                "Collecting the data for endpoint {}, input_name: {}, input_items: {}".format(
                    endpoint, self.input_name, self.input_items
                )
            )
            # defining the BoxLoadData for event write.
            data_loader = BoxLoadData(self.logger, self.event_write)
            others = {
                "index": self.input_items.get("index"),
                "sourcetype": f"box:{endpoint}",
                "inputname": self.input_name,
            }

            client = BoxClient(
                self.logger,
                self._box_credential.get("client_id"),
                self._box_credential.get("client_secret"),
                self._box_credential.get("access_token"),
                self._box_credential.get("refresh_token"),
                self._context,
            )

            if endpoint == "events":
                self.logger.info("Fetching Events(admin_logs) data")
                events = BoxEvents(
                    self.logger,
                    client,
                    account_name,
                    self.input_name,
                    self.input_items,
                    ckpt_key,
                )
                response = events.collect_data()

            elif endpoint == "folders":
                self.logger.info("Fetching Folders data")
                folders = BoxFolders(
                    self.logger,
                    client,
                    account_name,
                    self.input_name,
                    self.input_items,
                    ckpt_key,
                )
                response = folders.collect_data()

            elif endpoint == "users":
                self.logger.info("Fetching Users data")
                users = BoxUsers(
                    self.logger,
                    client,
                    account_name,
                    self.input_name,
                    self.input_items,
                    ckpt_key,
                )
                response = users.collect_data()

            for res in response:
                self.logger.info(
                    """Start flattening the data for input: {}""".format(
                        self.input_name
                    )
                )
                result = flatten_json_obj(res)
                self.logger.info(
                    """Flattening the data completed for input: {}""".format(
                        self.input_name
                    )
                )
                # write the event to splunk instance.
                data_loader.write_event(result, others)

        except Exception as e:
            self.logger.error(
                "message={} \n Traceback: {}".format(e, traceback.format_exc())
            )
