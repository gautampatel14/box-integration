import os
import os.path as op

from solnlib.modular_input import checkpointer
from datetime import datetime

SPLUNK_HOME = os.environ["HOME"]


class CustomCheckpointer:
    """
    Checkpoint Class
    """

    def __init__(self, logger, account_name, input_name, ckpt_name):
        self.logger = logger
        self.account_name = account_name
        self.input_name = input_name
        self.ckpt_name = ckpt_name
        self.checkpoint_dir = op.join(
            SPLUNK_HOME,
            "splunk",
            "var",
            "lib",
            "splunk",
            "modinputs",
            "box_input_logs",
            f"{self.account_name}",
        )
        self.ckpt_object = checkpointer.FileCheckpointer(
            checkpoint_dir=self.checkpoint_dir
        )
        self.ckpt_key = self.input_name + "_" + self.ckpt_name

    def get_file_checkpoint(self) -> dict:
        """
        Check for the stored value in file

        Raises:
            e: raise exception if error occurs

        Returns:
            dict: key-value pairs of chcekpoint parameter from file if any else {}
        """
        try:
            if not op.exists(self.checkpoint_dir):
                os.makedirs(self.checkpoint_dir)
            ckpt_value = self.ckpt_object.get(self.ckpt_key)
            self.logger.info(
                "Succesfully get the data for the {} checkpoint: {}".format(
                    self.ckpt_name, self.input_name
                )
            )
            if ckpt_value:
                return True, ckpt_value
        except Exception as e:
            self.logger.error(
                "Error occured while getting the file checkpoint for {} endpoint: {}".format(
                    self.ckpt_name, self.input_name
                )
            )
            raise e

        return False, {}

    def delete_file_checkpoint(self) -> None:
        """
        Delete the checkpoint file

        Raises:
            e: raise exception if error occurs
        """
        try:
            self.ckpt_object.delete(self.ckpt_key)
            self.logger.info(
                "Successfully deleted the {} checkpoint file: {}".format(
                    self.ckpt_name, self.input_name
                )
            )
        except Exception as e:
            self.logger.error(
                "Error occured while deleting the file checkpoint for {} endpoint: {}".format(
                    self.ckpt_name, self.input_name
                )
            )
            raise e

    def update_file_checkpoint(self, ckpt_value: dict) -> None:
        """
        Save the last checkpoint value

        Args:
            checkpoint_value (dict): date-time of latest event

        Raises:
            e: raise exception if error occurs
        """
        try:
            self.ckpt_object.update(self.ckpt_key, ckpt_value)
            self.logger.info(
                "Succesfully updated the checkpoint data for {}: {}".format(
                    self.ckpt_name, self.input_name
                )
            )
        except Exception as e:
            self.logger.error(
                "Error occured while updating the file checkpoint for {} endpoint: {}".format(
                    self.ckpt_name, self.input_name
                )
            )
            raise e


def hanlde_folder_comments_ckpt(logger, id, ckpt_field_name, output, **details) -> dict:
    """
    This fun

    Args:
        logger(Logger) : logger object
        id (str): _description_
        ckpt_field_name (str): checkpoint field name
        output (list): contain entries for response.

    Returns:
        dict: update response  containing the new entries.
    """
    ckpt_field_name = f"{ckpt_field_name}"
    ckpt_response = folders_checkpoint(
        logger, str(id), ckpt_field_name, output.get("entries"), **details
    )
    output = {"entries": ckpt_response, "total_count": len(ckpt_response)}
    return output


def folders_checkpoint(
    logger, id: str, field_name: str, response: list, **details
) -> list:
    """
    This folder is used to handle the folder checkpoiting.

    Args:
        logger (Logger): logger object
        id (str): contain file or folder ids
        field_name (str): checkpoint field name.
        response (list): containg list of entries.
    Returns:
        list: return the updated entries after checkpointing.
    """
    ckpt_name = details.get("ckpt_name")
    input_name = details.get("input_name")
    logger.info("Start checkpointing the data for {}: {}".format(ckpt_name, input_name))
    try:
        checkpoint = CustomCheckpointer(logger, **details)
        status, ckpt_value = checkpoint.get_file_checkpoint()

        if not ckpt_value.get(id):
            last_modified_at = response[0].get(field_name)
            last_modified_at = datetime.strptime(
                last_modified_at, "%Y-%m-%dT%H:%M:%S%z"
            )
            for item in response:
                item_modified_at = datetime.strptime(
                    item.get(field_name), "%Y-%m-%dT%H:%M:%S%z"
                )
                if item_modified_at > last_modified_at:
                    last_modified_at = item_modified_at

            last_modified_at = last_modified_at.strftime("%Y-%m-%dT%H:%M:%S%z")
            ckpt_value.update({id: last_modified_at})
            checkpoint.update_file_checkpoint(ckpt_value)
            return response

        ckpt_response = []
        last_modified_at = datetime.strptime(ckpt_value.get(id), "%Y-%m-%dT%H:%M:%S%z")
        latest_modified_at = last_modified_at
        for item in response:
            item_modified_at = datetime.strptime(
                item.get(field_name), "%Y-%m-%dT%H:%M:%S%z"
            )
            if item_modified_at > latest_modified_at:
                latest_modified_at = item_modified_at
            if item_modified_at > last_modified_at:
                ckpt_response.append(item)

        last_modified_at = latest_modified_at.strftime("%Y-%m-%dT%H:%M:%S%z")
        ckpt_value.update({id: last_modified_at})
        checkpoint.update_file_checkpoint(ckpt_value)
        logger.info("Completed the checkpoint for {}: {}".format(ckpt_name, input_name))
        return ckpt_response

    except Exception as e:
        logger.error(
            "Error occurred while checkpointing the data for {}: {}".format(
                ckpt_name, input_name
            )
        )
        raise e
