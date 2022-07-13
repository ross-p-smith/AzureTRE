import logging

from httpx import Timeout
from e2e_tests.helpers import get_full_endpoint
from e2e_tests.resources import strings

LOGGER = logging.getLogger(__name__)
TIMEOUT = Timeout(10, read=30)


async def delete_done(client, operation_endpoint, headers):
    delete_terminal_states = [strings.RESOURCE_STATUS_DELETED, strings.RESOURCE_STATUS_DELETING_FAILED]
    deployment_status, message = await check_deployment(client, operation_endpoint, headers)
    return (True, deployment_status, message) if deployment_status in delete_terminal_states else (False, deployment_status, message)


async def install_done(client, operation_endpoint, headers):
    install_terminal_states = [strings.RESOURCE_STATUS_DEPLOYED, strings.RESOURCE_STATUS_DEPLOYMENT_FAILED]
    deployment_status, message = await check_deployment(client, operation_endpoint, headers)
    return (True, deployment_status, message) if deployment_status in install_terminal_states else (False, deployment_status, message)


async def patch_done(client, operation_endpoint, headers):
    install_terminal_states = [strings.RESOURCE_STATUS_UPDATED, strings.RESOURCE_STATUS_UPDATING_FAILED]
    deployment_status, message = await check_deployment(client, operation_endpoint, headers)
    return (True, deployment_status, message) if deployment_status in install_terminal_states else (False, deployment_status, message)


async def check_deployment(client, operation_endpoint, headers):
    full_endpoint = get_full_endpoint(operation_endpoint)

    response = await client.get(full_endpoint, headers=headers, timeout=TIMEOUT)
    if response.status_code == 200:
        deployment_status = response.json()["operation"]["status"]
        message = response.json()["operation"]["message"]
        return deployment_status, message
    else:
        LOGGER.error(f"Non 200 response in check_deployment: {response.status_code}")
        LOGGER.error(f"Full response: {response}")
        raise Exception("Non 200 response in check_deployment")
