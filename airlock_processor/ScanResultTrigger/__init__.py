from distutils.util import strtobool
import logging

import azure.functions as func
import datetime
import uuid
import json
import re
import os
from shared_code import constants


def main(msg: func.ServiceBusMessage,
         outputEvent: func.Out[func.EventGridOutputEvent]):

    logging.info("Python ServiceBus queue trigger processed message - Malware scan result arrived!")
    body = msg.get_body().decode('utf-8')
    logging.info('Python ServiceBus queue trigger processed message: %s', body)

    try:
        enable_malware_scanning = strtobool(os.environ["ENABLE_MALWARE_SCANNING"])
    except KeyError as e:
        logging.error("environment variable 'ENABLE_MALWARE_SCANNING' does not exists. cannot continue.")
        raise e

    # Sanity
    if not enable_malware_scanning:
        # A scan result arrived despite the fact malware scanning should be disabled. This may result in unexpected behaviour.
        # Raise an exception and stop
        error_msg = "Malware scanning is disabled, however a malware scan result arrived. Ignoring it."
        logging.error(error_msg)
        raise Exception(error_msg)

    try:
        json_body = json.loads(body)
        blob_uri = json_body["data"]["blobUri"]
        verdict = json_body["data"]["verdict"]
    except KeyError as e:
        logging.error("body was not as expected {}", e)
        raise e

    # Extract request id
    regex = re.search(r'https://(.*?).blob.core.windows.net/(.*?)/(.*?)', blob_uri)
    request_id = regex.group(2)

    # If clean, we can continue and move the request to the review stage
    # Otherwise, move the request to the blocked stage
    completed_step = constants.STAGE_SUBMITTED
    if verdict == constants.NO_THREATS:
        logging.info('No malware were found in request id %s, moving to %s stage', request_id, constants.STAGE_IN_REVIEW)
        new_status = constants.STAGE_IN_REVIEW
    else:
        logging.info('Malware was found in request id %s, moving to %s stage', request_id, constants.STAGE_BLOCKING_INPROGRESS)
        new_status = constants.STAGE_BLOCKING_INPROGRESS

    # Send the event to indicate this step is done (and to request a new status change)
    outputEvent.set(
        func.EventGridOutputEvent(
            id=str(uuid.uuid4()),
            data={"completed_step": completed_step, "new_status": new_status, "request_id": request_id},
            subject=request_id,
            event_type="Airlock.StepResult",
            event_time=datetime.datetime.utcnow(),
            data_version="1.0"))
