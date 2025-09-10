from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from dotenv import load_dotenv
import os

from ..schemas.value_set_schemas import (
    ValueSetCreate,
    ValueSetUpdate,
    ValueSetRead,
    ValueSetListResponse,
    ValueSetItemsResponse,
    BootstrapResponse
)
from ..service.value_set_service import ValueSetService
from ..repository.value_set_repository import ValueSetRepository
from ..utils.helpers import set_service_instance
from ...auth.auth_router import get_current_active_user, require_permission

load_dotenv()

router = APIRouter(prefix="/api/v1/enums", tags=["ValueSets"])


async def get_database() -> AsyncIOMotorDatabase:
    from motor.motor_asyncio import AsyncIOMotorClient
    
    mongo_url = os.getenv("MONGO_URL", "mongodb+srv://pbhanusaketh1602:Bhanu%402002@saketh.qsgehh3.mongodb.net/")
    db_name = os.getenv("DB_NAME", "valuesets_platform")
    
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


async def get_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ValueSetService:
    repository = ValueSetRepository(db)
    service = ValueSetService(repository)
    set_service_instance(service)
    return service


@router.get("", response_model=List[dict])
async def list_value_sets(
    status: Optional[str] = Query(None, description="Filter by status (active/archived)"),
    q: Optional[str] = Query(None, description="Search text"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: ValueSetService = Depends(get_service)
):
    items, total = await service.list_value_sets(status, q, skip, limit)
    return [item.model_dump() for item in items]


@router.get("/bootstrap", response_model=BootstrapResponse)
async def bootstrap_value_sets(
    lang: str = Query("en", description="Language code for labels"),
    service: ValueSetService = Depends(get_service)
):
    return await service.bootstrap_value_sets(lang)


@router.get("/{key}", response_model=ValueSetItemsResponse)
async def get_value_set(
    key: str,
    lang: str = Query("en", description="Language code for labels"),
    service: ValueSetService = Depends(get_service)
):
    value_set = await service.get_value_set(key, lang)
    if not value_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ValueSet with key '{key}' not found"
        )
    return value_set


@router.post("", response_model=ValueSetRead, status_code=status.HTTP_201_CREATED)
async def create_value_set(
    data: ValueSetCreate,
    service: ValueSetService = Depends(get_service),
    current_user: dict = Depends(require_permission("valuesets", "create"))
):
    try:
        # Set created_by from current user (use string representation of ObjectId)
        data.created_by = str(current_user.get("_id", current_user.get("username", "system")))
        return await service.create_value_set(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{key}", response_model=ValueSetRead)
async def update_value_set(
    key: str,
    data: ValueSetUpdate,
    service: ValueSetService = Depends(get_service),
    current_user: dict = Depends(require_permission("valuesets", "update"))
):
    updated = await service.update_value_set(key, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ValueSet with key '{key}' not found"
        )
    return updated


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_value_set(
    key: str,
    service: ValueSetService = Depends(get_service),
    current_user: dict = Depends(require_permission("valuesets", "archive"))
):
    success = await service.archive_value_set(key)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ValueSet with key '{key}' not found"
        )


@router.post("/cache/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh_all_cache(
    service: ValueSetService = Depends(get_service),
    current_user: dict = Depends(require_permission("valuesets", "refresh_cache"))
):
    await service.refresh_enum_cache()


@router.post("/{key}/cache/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh_cache(
    key: str,
    service: ValueSetService = Depends(get_service),
    current_user: dict = Depends(require_permission("valuesets", "refresh_cache"))
):
    await service.refresh_enum_cache(key)