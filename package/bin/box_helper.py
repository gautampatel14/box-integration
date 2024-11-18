import logging
import logging.handlers
import os.path
import traceback

from consts import ACCOUNT_CONF, ADDON_NAME
from datetime import datetime, timedelta
from solnlib import conf_manager


def get_conf_account(logger: logging.Logger, session_key: str):
    """
    This function is get the account configuration details.

    Args:
        logger (logging.Logger): logger object.
        session_key (str): session key of splunk instance.

    Raises:
        Exception: if account conf file not found.
        Exception: _description_

    Returns:
        account conf object.
    """
    try:
        # check if the box account conf file present in the local
        # path: with same directory level, finding the local directory.
        if not os.path.isfile(
            os.path.join(
                os.path.dirname(os.path.realpath(os.path.dirname(__file__))),
                "local",
                ACCOUNT_CONF,
            )
        ):
            logger.error("config file: {} is not found".format(ACCOUNT_CONF))
            raise Exception(
                """action=fecth_credential message="{} is not found".""".format(
                    ACCOUNT_CONF
                )
            )

        # confManager is used to get the account conf file for the addon.
        account_conf = conf_manager.ConfManager(
            session_key,
            ADDON_NAME,
            realm="__REST_CREDENTIAL__#{}#configs/conf-box_integration_for_splunk_account".format(
                ADDON_NAME
            ),
        )

        # used to get specific account.conf file for it's credential.
        conf_account = account_conf.get_conf("box_integration_for_splunk_account")
        logger.info(
            '''action=fetch_credential message="{} file fetched"'''.format(ACCOUNT_CONF)
        )
        return conf_account
    except:
        logger.exception(
            '''action=fetch_credential message="Error while getting account details"'''
        )
        raise Exception("Error while getting account details")


def get_delayed(logger, created_after, event_delay):
    """
    This function return calculated event_delayed.

    Args:
        logger: logger of input.
        created_after (str)
        event_delay (str)

    Returns:
        str: return delayed timestamp.
    """
    try:
        logger.info("Converting into delayed timestamp.")
        delayed_timestamp = datetime.strptime(created_after, "%Y-%m-%dT%H:%M:%S%z")
        logger.debug("Delayed timestamp after conversion: {}".format(delayed_timestamp))
    except Exception:
        logger.error(
            "Failed to convert timestamp:{}. \nTraceback: {}".format(
                created_after, traceback.format_exc()
            )
        )
    else:
        logger.info("Start calculating event delay.")
        delay = int(event_delay)
        delayed_timestamp = delayed_timestamp - timedelta(seconds=delay)
        delayed_timestamp = datetime.strftime(delayed_timestamp, "%Y-%m-%dT%H:%M:%S%z")
        logger.debug("Delayed timestamp after conversion: {}".format(delayed_timestamp))
        return delayed_timestamp


def get_location(entity_sequence) -> str:
    """
    This function is generate the location of the path collection.
    Args:
        entity_sequence (list): entity_sequence contain the list of dictionary.
    Returns:
        str: return the location string.
    """
    entity_names = []
    for entity in entity_sequence:
        if entity["name"]:
            entity_names.append(entity["name"])
    # generating hierarchical location
    location_string = "/".join(entity_names)
    location_string = str(location_string).replace('"', '\\"')
    return location_string


def flatten_object_data(prefix, obj) -> list:
    """
    This function is used to flatten the object data.
    Args:
        prefix (str): parent key of the nested dictionary.
        obj (dict): value (if we have nested dict) or json response.
    Returns:
        list
    """
    template = '%s_{}="{}"' % prefix if prefix else '{}="{}"'
    results = []
    for k, v in obj.items():
        if k == "path_collection":
            if "entries" in v:
                res = 'location="{}"'.format(get_location(v["entries"]))
        elif isinstance(v, dict):
            if prefix:
                k = f"{prefix}_{k}"

            res = flatten_object_data(k, v)
            if res:
                res = ",".join(res)
        elif isinstance(v, list):
            res = template.format(k, v)
        else:
            if v:
                v = str(v).replace('"', '\\"')
            res = template.format(k, v if v is not None else "")
        results.append(res)

    return results


def flatten_json_obj(obj) -> list:
    """
    This method is used to iterate box json object
    and return converted flatten list.
    Args:
        obj (_type_): JSON object from API response
    Returns:
        list: return list of flatten data.
    """
    results = []
    if "entries" in obj:
        for obj in obj["entries"]:
            res = flatten_object_data(None, obj)
            if res:
                results.append(",".join(res))
    else:
        if isinstance(obj, dict):
            res = flatten_object_data(None, obj)
            if res:
                results.append(",".join(res))

    return results
