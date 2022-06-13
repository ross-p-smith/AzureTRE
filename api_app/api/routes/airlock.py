import logging

from fastapi import APIRouter, Depends, HTTPException, status

from jsonschema.exceptions import ValidationError

from api.dependencies.database import get_repository
from api.dependencies.workspaces import get_workspace_by_id_from_path, get_deployed_workspace_by_id_from_path
from api.dependencies.airlock import get_airlock_request_by_id_from_path
from models.domain.airlock_resource import AirlockRequestStatus

from db.repositories.airlock_requests import AirlockRequestRepository
from models.schemas.airlock_request import AirlockRequestInCreate, AirlockRequestInResponse
from resources import strings
from services.authentication import get_current_workspace_owner_or_researcher_user

from .airlock_resource_helpers import save_and_publish_event_airlock_request, update_status_and_publish_event_airlock_request

airlock_workspace_router = APIRouter(dependencies=[Depends(get_current_workspace_owner_or_researcher_user)])


# airlock
@airlock_workspace_router.post("/workspaces/{workspace_id}/requests", status_code=status.HTTP_201_CREATED, response_model=AirlockRequestInResponse, name=strings.API_CREATE_AIRLOCK_REQUEST, dependencies=[Depends(get_workspace_by_id_from_path)])
async def create_draft_request(airlock_request_input: AirlockRequestInCreate, user=Depends(get_current_workspace_owner_or_researcher_user), airlock_request_repo=Depends(get_repository(AirlockRequestRepository)), workspace=Depends(get_deployed_workspace_by_id_from_path)) -> AirlockRequestInResponse:
    try:
        airlock_request = airlock_request_repo.create_airlock_request_item(airlock_request_input, workspace.id)
    except (ValidationError, ValueError) as e:
        logging.error(f"Failed create air lock request model instance: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    await save_and_publish_event_airlock_request(airlock_request, airlock_request_repo, user)
    return AirlockRequestInResponse(airlock_request=airlock_request)


@airlock_workspace_router.post("/workspaces/{workspace_id}/requests/{airlock_request_id}/submit", status_code=status.HTTP_200_OK, response_model=AirlockRequestInResponse, name=strings.API_SUBMIT_AIRLOCK_REQUEST, dependencies=[Depends(get_workspace_by_id_from_path)])
async def create_submit_request(airlock_request=Depends(get_airlock_request_by_id_from_path), user=Depends(get_current_workspace_owner_or_researcher_user), airlock_request_repo=Depends(get_repository(AirlockRequestRepository))) -> AirlockRequestInResponse:
    updated_resource = await update_status_and_publish_event_airlock_request(airlock_request, airlock_request_repo, user, AirlockRequestStatus.Submitted)
    return AirlockRequestInResponse(airlock_request=updated_resource)
