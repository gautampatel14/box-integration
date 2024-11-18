import import_declare_test
import logging
import logging.handlers


from datetime import datetime, timedelta
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
from splunktaucclib.rest_handler.error import RestError
from utils import get_logger, get_log_level


def get_datetime(logger: logging.Logger, date):
    """
    Get the datetime
    Args:
        logger (logging.Logger):
        date (str): created_after date from input fields

    Raises:
        ValueError: if date formate is not valid.
        ValueError: if date is in future.

    Returns:
        str: date if no exception
    """
    # get date before 90 day if input create_after is null
    const_date = datetime.utcnow() - timedelta(days=90)
    const_date = datetime.strftime(const_date, "%Y-%m-%dT%H:%M:%S")

    if not date:
        logger.warn(
            '''action=get_date message="{}, after which to collect data. The default is last 90 days."'''.format(
                const_date
            )
        )
        return const_date
    try:
        datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        logger.error("{} invalid date formate. Required YYYY-MM-DDTHH:mm:ss.")
        raise ValueError("{}: invalid date formate. Required YYYY-MM-DDTHH:mm:ss.")

    date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")

    if date_obj > datetime.utcnow():
        logger.error("{} future date is not allowed for data collection.".format(date))
        raise ValueError(
            "{} future date is not allowed for data collection.".format(date)
        )

    return date


def validate_groups_users(logger: logging.Logger, payload):
    pass


def validate_folder(logger: logging.Logger, payload):
    pass


def validate_endpoint(logger: logging.Logger, payload: dict) -> dict:
    """
    Validate the all endpoint(events, users, folders, groups)

    Args:
        logger (logging.Logger): logger
        payload (dict): contain the input fields

    Returns:
        dict: return dict with containg information about response
    """
    try:
        response = {}
        logger.info("inside the validate endpoint")

        if payload.get("rest_endpoint") == "events":
            duration = int(payload.get("duration", 0))
            event_delay = int(payload.get("event_delay", 0))

            if event_delay > duration:
                event_delay = max((duration - 10), (event_delay % duration))
                logger.warn(
                    "{}, event_delay is greater than {} interval. The default is 0.".format(
                        payload.get("event_delay"), duration
                    )
                )
            response["event_delay"] = event_delay
            response["created_after"] = get_datetime(
                logger, payload.get("created_after")
            )

        elif payload.get("rest_endpoint") == "folder":
            validate_folder(logger, payload)

        elif payload.get("rest_endpoint") in ("groups", "users"):
            validate_groups_users(logger, payload)

        response["message"] = "validate inputs"
        response["state"] = True
        return response

    except Exception as e:
        return {"state": False, "error": str(e)}


class BoxInpuHandler(AdminExternalHandler):
    def __init__(self, *args, **kwargs):
        AdminExternalHandler.__init__(self, *args, **kwargs)
        self.logger = get_logger("account")
        session_key = self.getSessionKey()
        self.logger.setLevel(get_log_level(self.logger, session_key))
        AdminExternalHandler.__init__(self, *args, **kwargs)

    def handleList(self, confInfo):
        AdminExternalHandler.handleList(self, confInfo)

    def handleEdit(self, confInfo):
        response = validate_endpoint(self.logger, self.payload)

        if not response.get("state", False):
            self.logger.error(
                """name={} action=create message={}""".format(
                    self.callerArgs.id, response.get("error")
                )
            )
            raise RestError(400, response.get("error"))

        self.payload["created_after"] = response.get("created_after")
        self.logger.info("""created_after: {}""".format(response.get("created_after")))
        self.logger.info("""CallerArgs: {}""".format(dict(self.callerArgs)))
        self.logger.info(
            """name={}, action=edit, message={}""".format(
                self.callerArgs.id, response.get("message")
            )
        )

        AdminExternalHandler.handleEdit(self, confInfo)

    def handleCreate(self, confInfo):
        response = validate_endpoint(self.logger, self.payload)

        if not response.get("state", False):
            self.logger.error(
                """name={} action=create message={}""".format(
                    self.callerArgs.id, response.get("error")
                )
            )
            raise RestError(400, response.get("error"))
        self.payload["created_after"] = response.get("created_after")
        self.logger.info(
            """name={}, action=create, message={}""".format(
                self.callerArgs.id, response.get("message")
            )
        )
        AdminExternalHandler.handleCreate(self, confInfo)

    def handleRemove(self, confInfo):
        # Add your code here to delete the checkpoint!
        AdminExternalHandler.handleRemove(self, confInfo)
