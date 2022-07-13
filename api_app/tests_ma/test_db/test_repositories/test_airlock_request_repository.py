from fastapi import HTTPException
from mock import patch, MagicMock
import pytest
from tests_ma.test_api.conftest import create_test_user
from models.schemas.airlock_request import AirlockRequestInCreate
from models.domain.airlock_resource import AirlockResourceType
from models.domain.airlock_request import AirlockRequest, AirlockRequestStatus, AirlockRequestType
from db.repositories.airlock_requests import AirlockRequestRepository

from db.errors import EntityDoesNotExist
from azure.cosmos.exceptions import CosmosResourceNotFoundError


WORKSPACE_ID = "abc000d3-82da-4bfc-b6e9-9a7853ef753e"
AIRLOCK_REQUEST_ID = "ce45d43a-e734-469a-88a0-109faf4a611f"
DRAFT = AirlockRequestStatus.Draft
SUBMITTED = AirlockRequestStatus.Submitted
IN_REVIEW = AirlockRequestStatus.InReview
APPROVED_IN_PROGRESS = AirlockRequestStatus.ApprovalInProgress
APPROVED = AirlockRequestStatus.Approved
REJECTION_IN_PROGRESS = AirlockRequestStatus.RejectionInProgress
REJECTED = AirlockRequestStatus.Rejected
CANCELLED = AirlockRequestStatus.Cancelled
BLOCKING_IN_PROGRESS = AirlockRequestStatus.BlockingInProgress
BLOCKED = AirlockRequestStatus.Blocked

ALL_STATUSES = [enum.value for enum in AirlockRequestStatus]

ALLOWED_STATUS_CHANGES = {
    DRAFT: [SUBMITTED, CANCELLED],
    SUBMITTED: [IN_REVIEW, BLOCKING_IN_PROGRESS],
    IN_REVIEW: [APPROVED_IN_PROGRESS, REJECTION_IN_PROGRESS, CANCELLED],
    APPROVED_IN_PROGRESS: [APPROVED],
    APPROVED: [],
    REJECTION_IN_PROGRESS: [REJECTED],
    REJECTED: [],
    CANCELLED: [],
    BLOCKING_IN_PROGRESS: [BLOCKED],
    BLOCKED: [],
}


@pytest.fixture
def airlock_request_repo():
    with patch('azure.cosmos.CosmosClient') as cosmos_client_mock:
        yield AirlockRequestRepository(cosmos_client_mock)


@pytest.fixture
def sample_airlock_request_input():
    return AirlockRequestInCreate(requestType=AirlockRequestType.Import, businessJustification="Some business justification")


@pytest.fixture
def verify_dictionary_contains_all_enum_values():
    for status in ALL_STATUSES:
        if status not in ALLOWED_STATUS_CHANGES:
            raise Exception(f"Status '{status}' was not added to the ALLOWED_STATUS_CHANGES dictionary")


def airlock_request_mock(status=AirlockRequestStatus.Draft):
    airlock_request = AirlockRequest(
        id=AIRLOCK_REQUEST_ID,
        resourceType=AirlockResourceType.AirlockRequest,
        workspaceId=WORKSPACE_ID,
        requestType=AirlockRequestType.Import,
        files=[],
        businessJustification="some test reason",
        status=status
    )
    return airlock_request


def get_allowed_status_changes():
    for current_status, allowed_new_statuses in ALLOWED_STATUS_CHANGES.items():
        for new_status in allowed_new_statuses:
            yield current_status, new_status


def get_forbidden_status_changes():
    for current_status, allowed_new_statuses in ALLOWED_STATUS_CHANGES.items():
        forbidden_new_statuses = list(set(ALL_STATUSES) - set(allowed_new_statuses))
        for new_status in forbidden_new_statuses:
            yield current_status, new_status


def test_get_airlock_request_by_id(airlock_request_repo):
    airlock_request = airlock_request_mock()
    airlock_request_repo.read_item_by_id = MagicMock(return_value=airlock_request)
    actual_service = airlock_request_repo.get_airlock_request_by_id(AIRLOCK_REQUEST_ID)

    assert actual_service == airlock_request


def test_get_airlock_request_by_id_raises_entity_does_not_exist_if_no_such_request_id(airlock_request_repo):
    airlock_request_repo.read_item_by_id = MagicMock()
    airlock_request_repo.read_item_by_id.side_effect = CosmosResourceNotFoundError

    with pytest.raises(EntityDoesNotExist):
        airlock_request_repo.get_airlock_request_by_id(AIRLOCK_REQUEST_ID)


def test_create_airlock_request_item_creates_an_airlock_request_with_the_right_values(sample_airlock_request_input, airlock_request_repo):
    airlock_request_item_to_create = sample_airlock_request_input
    airlock_request = airlock_request_repo.create_airlock_request_item(airlock_request_item_to_create, WORKSPACE_ID)

    assert airlock_request.resourceType == AirlockResourceType.AirlockRequest
    assert airlock_request.workspaceId == WORKSPACE_ID


@pytest.mark.parametrize("current_status, new_status", get_allowed_status_changes())
def test_update_airlock_request_status_with_allowed_new_status_should_update_request_status(airlock_request_repo, current_status, new_status, verify_dictionary_contains_all_enum_values):
    user = create_test_user()
    mock_existing_request = airlock_request_mock(status=current_status)
    airlock_request = airlock_request_repo.update_airlock_request_status(mock_existing_request, new_status, user)
    assert airlock_request.status == new_status


@pytest.mark.parametrize("current_status, new_status", get_forbidden_status_changes())
def test_update_airlock_request_status_with_frobidden_status_should_fail_on_validation(airlock_request_repo, current_status, new_status, verify_dictionary_contains_all_enum_values):
    user = create_test_user()
    mock_existing_request = airlock_request_mock(status=current_status)
    with pytest.raises(HTTPException):
        airlock_request_repo.update_airlock_request_status(mock_existing_request, new_status, user)
