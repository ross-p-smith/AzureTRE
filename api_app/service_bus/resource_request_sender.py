import json


from db.repositories.resources import ResourceRepository
from db.repositories.resource_templates import ResourceTemplateRepository
from service_bus.helpers import send_deployment_message, update_resource_for_step
from models.domain.resource_template import ResourceTemplate

from models.domain.authentication import User

from models.domain.request_action import RequestAction
from models.domain.resource import Resource
from models.domain.operation import Operation

from db.repositories.operations import OperationRepository


async def send_resource_request_message(resource: Resource, operations_repo: OperationRepository, resource_repo: ResourceRepository, user: User, resource_template: ResourceTemplate, resource_template_repo: ResourceTemplateRepository, action: RequestAction = RequestAction.Install) -> Operation:
    """
    Creates and sends a resource request message for the resource to the Service Bus.
    The resource ID is added to the message to serve as an correlation ID for the deployment process.

    :param resource: The resource to deploy.
    :param action: install, uninstall etc.
    """

    # add the operation to the db - this will create all the steps needed (if any are defined in the template)
    operation = operations_repo.create_operation_item(
        resource_id=resource.id,
        action=action,
        resource_path=resource.resourcePath,
        resource_version=resource.resourceVersion,
        user=user,
        resource_template=resource_template,
        resource_repo=resource_repo)

    # prep the first step to send in SB
    first_step = operation.steps[0]
    resource_to_send = update_resource_for_step(
        operation_step=first_step,
        resource_repo=resource_repo,
        resource_template_repo=resource_template_repo,
        primary_resource=resource,
        resource_to_update_id=first_step.resourceId,
        primary_action=action,
        user=user)

    # create + send the message
    content = json.dumps(resource_to_send.get_resource_request_message_payload(operation_id=operation.id, step_id=first_step.stepId, action=first_step.resourceAction))
    await send_deployment_message(content=content, correlation_id=operation.id, session_id=first_step.resourceId, action=first_step.resourceAction)

    return operation
