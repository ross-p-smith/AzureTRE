import logging
from azure.eventgrid import EventGridEvent
from models.domain.events import StatusChangedData, AirlockNotificationData
from event_grid.helpers import publish_event
from core import config
from models.domain.airlock_request import AirlockRequest


async def send_status_changed_event(airlock_request: AirlockRequest):
    request_id = airlock_request.id
    status = airlock_request.status.value
    request_type = airlock_request.requestType.value
    short_workspace_id = airlock_request.workspaceId[-4:]

    status_changed_event = EventGridEvent(
        event_type="statusChanged",
        data=StatusChangedData(request_id=request_id, status=status, type=request_type, workspace_id=short_workspace_id).__dict__,
        subject=f"{request_id}/statusChanged",
        data_version="2.0"
    )
    logging.info(f"Sending status changed event with request ID {request_id}, status: {status}")
    await publish_event(status_changed_event, config.EVENT_GRID_STATUS_CHANGED_TOPIC_ENDPOINT)


async def send_airlock_notification_event(airlock_request: AirlockRequest, researchers_emails, owners_emails):
    request_id = airlock_request.id
    status = airlock_request.status.value
    short_workspace_id = airlock_request.workspaceId[-4:]

    airlock_notification = EventGridEvent(
        event_type="airlockNotification",
        data=AirlockNotificationData(request_id=request_id, event_type="status_changed", event_value=status, researchers_emails=researchers_emails, owners_emails=owners_emails, workspace_id=short_workspace_id).__dict__,
        subject=f"{request_id}/airlockNotification",
        data_version="2.0"
    )
    logging.info(f"Sending airlock notification event with request ID {request_id}, status: {status}")
    await publish_event(airlock_notification, config.EVENT_GRID_AIRLOCK_NOTIFICATION_TOPIC_ENDPOINT)
