import logging
import logging.handlers
import requests as req
import traceback

from box_helper import get_conf_account
from consts import REST_URL, URL, TIMEOUT, RETRYS


class BoxClient:
    """
    Box Client

    """

    def __init__(
        self,
        logger: logging.Logger,
        client_id,
        client_secret,
        access_token,
        refresh_token,
        context,
    ):
        self.logger = logger
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._context = context
        self.headers = {"Authorization": f"Bearer {self._access_token}"}

    def refresh_access_token(self):
        """
        This function refresh the access token and make
        function call to update the account conf file

        Returns:
            bool: return the update status of the new tokens.
        """
        try:
            account = self._context.get("account")
            token_url = f"{URL}/oauth2/token"
            data = {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": self._refresh_token,
                "grant_type": "refresh_token",
            }

            self.logger.debug(
                '''action=refresh_access_token message="Refreshing access token started"'''
            )

            response = req.post(token_url, data=data, timeout=TIMEOUT)

            if response.status_code not in (200, 201):
                self.logger.error(
                    """Error occurred while regenerating the access token \n"""
                    """ with account {}. To fix this issue, reconfigure the account. \n"""
                    """ action=refresh_access_token Status={}, message={}""".format(
                        account, response.status_code, response.text
                    )
                )
                return False

            self.logger.info(
                '''action="refresh_access_token" message="Access token refresh successfully."'''
            )

            response = response.json()
            update_status = self.update_conf(response, account)

            # if box account conf updated then set the new values of tokens
            if update_status:
                self.logger.info(
                    "Updated account stanza- '{}' with new values of access_token and refresh_token".format(
                        account
                    )
                )

                # initialize the new values of the both tokens to the BoxClient.
                self._access_token = response.get("access_token")
                self._refresh_token = response.get("refresh_token")
                return update_status
            return False
        except Exception as e:
            self.logger.error(
                """Failure occurred while generating new access token. messgae={} \n"""
                """Traceback: {}""".format(e, traceback.format_exc())
            )
            return False

    def update_conf(self, content, account):
        """
        This function updates the account conf file with new
        value of the access token and refresh token.

        Args:
            content (dict): new tokens.
            account (str): name of the account stanza.

        Returns:
            bool: rturn update status of the account conf.
        """
        new_access_token = content.get("access_token")
        new_refresh_token = content.get("refresh_token")

        # tokens that should be updated in the account conf.
        tokens = {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "client_secret": self._client_secret,
        }

        self.logger.info("Start updating the tokens in staza: {}".format(account))

        # getting the box conf account to update the stanza.
        box_conf_account = get_conf_account(self.logger, self._context["session_key"])
        try:
            box_conf_account.update(
                stanza_name=account,
                stanza=tokens,
                encrypt_keys=tokens.keys(),
            )
            return True
        except Exception as e:
            self.logger.error("Failed to store tokens in conf. message='{}".format(e))
            return False

    def make_api_request(self, uri, method="GET", params=None):
        """
        This function makes API call to box servers.

        Args:
            uri (str): url to get the data
            method (str, optional):Defaults to "GET".
            params (dict, optional): parameters for the API call. Defaults to None.
            headers (dict, optional): headers for the API call. Defaults to None.

        Returns:
            response obj: response from API.
        """
        url = f"{REST_URL}/{uri}"
        self.logger.info("URI: {}".format(url))
        headers = self.headers
        self.logger.debug("Start sending request to uri={}".format(url))
        self.logger.info("Params: {}".format(params))

        for retry in range(RETRYS):
            try:
                if retry > 0:
                    self.logger.info(
                        "Retrying to fetch events, retry count:{}".format(retry)
                    )

                result = {}
                response = req.get(url, headers=headers, params=params)
                result = response
                if response.status_code not in (200, 201):
                    # 401 status code is for invalid grant due to the invalid access token.
                    if response.status_code in (401, 403):
                        if response.status_code == 401:
                            self.logger.warn(
                                """Error while making an api call."""
                                '''status_code: {}, message="Due to expired access token"'''.format(
                                    response.status_code
                                )
                            )
                        else:
                            self.logger.error(
                                """status_code: {},  
                                    messgae: "Error due to the out of scope Box Server."
                                    """.format(
                                    response.status_code
                                )
                            )
                            return result

                        self.logger.info("Refreshing the access token.")
                        access_token_updated_status = self.refresh_access_token()

                        # erro in refreshing access token
                        if not access_token_updated_status:
                            return result

                        headers.update(
                            {"Authorization": f"Bearer {self._access_token}"}
                        )
                        continue
                    # if any throttling error.
                    elif response.status_code == 429:
                        self.logger.warn(
                            '''Throttling error occurred: The server has limited the number of requests you can 
                            make within a certain time period. Please wait a moment and try again later"'''
                            '''status_code: {}, message="Due to expired access token"'''.format(
                                response.status_code
                            )
                        )
                        continue
                    else:
                        # unexpected error.
                        self.logger.error(
                            '''status_code: {}, message="Unexpected error while retrieving Box events"'''
                            """error={}, \n Traceback: {}""".format(
                                response.status_code,
                                response.text,
                                traceback.format_exc(),
                            )
                        )

                return result

            except Exception as e:
                self.logger.error(
                    "Unexpected error while retrieving Box events: {}".format(e)
                )
                self.logger.error("Traceback: {}".format(traceback.format_exc()))

            return result
