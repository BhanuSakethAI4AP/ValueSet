from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from config.database import get_database
from auth.auth_bearer import get_current_user, require_permission
from func_spec.repositories.valuesets_repository import ValueSetsRepository
from func_spec.services.valuesets_service import ValueSetsService
from func_spec.handlers.valuesets_handler import ValueSetsHandler
from schema_spec.schemas.valuesets import *

router = APIRouter(prefix="/api/v1/enums", tags=["ValueSets"])


def get_valuesets_handler(db = Depends(get_database)) -> ValueSetsHandler:
    """Get ValueSets handler instance"""
    repository = ValueSetsRepository(db)
    service = ValueSetsService(repository)
    return ValueSetsHandler(service)


@router.get("", response_model=List[ValueSetListItem])
async def list_value_sets(
    status: Optional[str] = Query(None, description="Filter by status"),
    q: Optional[str] = Query(None, description="Search text"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    handler: ValueSetsHandler = Depends(get_valuesets_handler)
):
    """List all ValueSets"""
    return await handler.list_value_sets(status, q, skip, limit)


@router.get("/bootstrap", response_model=BootstrapResponse)
async def bootstrap_value_sets(
    lang: str = Query("en", description="Language code"),
    handler: ValueSetsHandler = Depends(get_valuesets_handler)
):
    """Bootstrap all active ValueSets for frontend"""
    return await handler.bootstrap_value_sets(lang)


@router.get("/{key}", response_model=ValueSetItemsResponse)
async def get_value_set(
    key: str,
    lang: str = Query("en", description="Language code"),
    handler: ValueSetsHandler = Depends(get_valuesets_handler)
):
    """Get specific ValueSet by key"""
    return await handler.get_value_set(key, lang)


@router.post("", response_model=ValueSetResponse, status_code=status.HTTP_201_CREATED)
async def create_value_set(
    data: ValueSetCreate,
    handler: ValueSetsHandler = Depends(get_valuesets_handler),
    current_user: dict = Depends(require_permission("valuesets", "create"))
):
    """Create new ValueSet"""
    created_by = str(current_user.get("_id", current_user.get("username", "system")))
    return await handler.create_value_set(data, created_by)


@router.put("/{key}", response_model=ValueSetResponse)
async def update_value_set(
    key: str,
    data: ValueSetUpdate,
    handler: ValueSetsHandler = Depends(get_valuesets_handler),
    current_user: dict = Depends(require_permission("valuesets", "update"))
):
    """Update ValueSet"""
    return await handler.update_value_set(key, data)


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_value_set(
    key: str,
    handler: ValueSetsHandler = Depends(get_valuesets_handler),
    current_user: dict = Depends(require_permission("valuesets", "archive"))
):
    """Archive ValueSet"""
    await handler.archive_value_set(key)