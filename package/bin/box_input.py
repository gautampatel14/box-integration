import import_declare_test
import sys
import json

from box_client import BoxClient
from box_helper import get_conf_account
from box_input_collector import BoxCollector
from box_input_loader import BoxLoadData
from consts import ADDON_NAME
from solnlib import conf_manager
from splunk import rest
from splunklib import modularinput as smi
from utils import get_logger_for_input


class BOX_INPUT(smi.Script):
    def __init__(self):
        super(BOX_INPUT, self).__init__()

    def get_scheme(self):
        scheme = smi.Scheme("box_input")
        scheme.description = "box_input"
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True
        scheme.use_single_instance = False

        scheme.add_argument(
            smi.Argument(
                "name", title="Name", description="Name", required_on_create=True
            )
        )

        scheme.add_argument(
            smi.Argument(
                "input_name",
                required_on_create=False,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "account",
                required_on_create=True,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "rest_endpoint",
                required_on_create=True,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "collect_folder",
                required_on_create=False,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "collect_collaboration",
                required_on_create=False,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "collect_file",
                required_on_create=False,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "collect_task",
                required_on_create=False,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "created_after",
                required_on_create=False,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "event_delay",
                required_on_create=False,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "duration",
                required_on_create=False,
            )
        )

        return scheme

    def validate_input(self, definition):
        return

    def stream_events(self, inputs, ew):
        input_items = [{"count": len(inputs.inputs)}]
        for input_name, input_item in inputs.inputs.items():
            # if account field  value is not found.
            if "account" not in input_item:
                rest.simpleRequest(
                    message="Account configurations are missing in Box integration for Splunk",
                    method="POST",
                )

        try:
            for input_name, input_item in inputs.inputs.items():
                normalized_input_name = input_name.split("/")[-1]
                logger = get_logger_for_input(normalized_input_name)
                session_key = self._input_definition.metadata["session_key"]

                # getting log leven from conf file.
                log_level = conf_manager.get_log_level(
                    logger=logger,
                    session_key=session_key,
                    app_name=ADDON_NAME,
                    conf_name=f"{ADDON_NAME}_settings",
                )
                # setting up log
                logger.setLevel(log_level)
                input_item["name"] = input_name
                account_name = input_item.get("account")

                conf_account = get_conf_account(logger, session_key)
                if not conf_account:
                    logger.exception(
                        '''action=fecth_credential message="No account configuration found"'''
                    )
                    raise Exception("No account configuration found")

                logger.info(
                    '''action=fetch_credential message="Account credential for {} fetch successfully."'''.format(
                        account_name
                    )
                )
                box_credential = conf_account.get(account_name)

                if box_credential:
                    context = {"account": account_name, "session_key": session_key}

                    box_collector = BoxCollector(
                        logger,
                        box_credential,
                        context,
                        normalized_input_name,
                        input_item,
                        ew,
                    )

                    box_collector.collect_data()

        except Exception as e:
            logger.exception(
                """action=event_ingest message="Error in box mod input" """.format(e)
            )
            raise Exception("Error in box mod input")
        finally:
            logger.info("action=ended input_name={}".format(normalized_input_name))


if __name__ == "__main__":
    exit_code = BOX_INPUT().run(sys.argv)
    sys.exit(exit_code)
