import datetime
import logging
import logging.handlers

from splunklib import modularinput as smi


class BoxLoadData():

    def __init__(self, logger: logging.Logger, event_writer) -> None:
        self.logger = logger
        self.ew = event_writer

    def write_event(self, collected_data, others:dict):
        """
        This function is write the event to splunk.

        Args:
            collected_data (list): Data collected from the API endpoints.
            others (dict): contain index and sourcetype for events.
        """ 
        try:
            self.logger.info("Start writing the events.")  
            for event in collected_data:
                self.ew.write_event(
                    smi.Event(
                            data=event,
                            index=others["index"],
                            sourcetype=others["sourcetype"],
                            source="box_historical_service::"
                            + others["sourcetype"]
                            + "::"
                            + others["inputname"],
                            time=datetime.datetime.now().isoformat()
                        )
                    )
            self.logger.info("Events written successfully.")
        except Exception as e:
            self.logger.error("Error while writing the event, message={}".format(e))
