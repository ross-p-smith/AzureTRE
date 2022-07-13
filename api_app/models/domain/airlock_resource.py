from enum import Enum
from typing import List
from pydantic import Field
from models.domain.azuretremodel import AzureTREModel
from resources import strings


class AirlockResourceType(str, Enum):
    """
    Type of resource to create
    """
    AirlockRequest = strings.AIRLOCK_RESOURCE_TYPE_REQUEST
    AirlockReview = strings.AIRLOCK_RESOURCE_TYPE_REVIEW


class AirlockResourceHistoryItem(AzureTREModel):
    """
    Resource History Item - to preserve history of resource properties
    """
    resourceVersion: int
    updatedWhen: float
    user: dict = {}
    properties: dict = {}


class AirlockResource(AzureTREModel):
    """
    Resource request
    """
    id: str = Field(title="Id", description="GUID identifying the resource")
    resourceType: AirlockResourceType
    resourceVersion: int = 0
    user: dict = {}
    updatedWhen: float = 0
    history: List[AirlockResourceHistoryItem] = []
