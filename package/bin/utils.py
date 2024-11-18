import logging
import logging.handlers
import os.path

from consts import ADDON_NAME
from solnlib import conf_manager, log


def get_logger_for_input(input_name: str) -> logging.Logger:
    """
    Get the logger for the input
    Args:
        input_name (str)

    Returns:
        logging.Logger:
    """
    return log.Logs().get_logger(f"{ADDON_NAME.lower()}_{input_name}")


def get_logger(name: str) -> logging.Logger:
    """
    Get the logger for the addon
    Args:
        name (str): name of the file

    Returns:
        logging.Logger: create a log file for `name`
    """
    return log.Logs().get_logger(f"{ADDON_NAME.lower()}_{name}")


def get_log_level(logger, session_key):
    """
    Get log level of add-on.

    :param logger: Logger object
    :param session_key: Session key of splunk instance
    :return: log_level
    """
    log_level = conf_manager.get_log_level(
        logger=logger,
        session_key=session_key,
        app_name=ADDON_NAME,
        conf_name=f"{ADDON_NAME}_settings",
    )
    return log_level
