from typing import List, Optional
from fastapi import HTTPException, status

from func_spec.services.valuesets_service import ValueSetsService
from schema_spec.schemas.valuesets import *


class ValueSetsHandler:
    """Handler for ValueSets requests/responses"""
    
    def __init__(self, service: ValueSetsService):
        self.service = service
    
    async def list_value_sets(
        self,
        status: Optional[str] = None,
        q: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ValueSetListItem]:
        """Handle list ValueSets request"""
        return await self.service.list_value_sets(status, q, skip, limit)
    
    async def bootstrap_value_sets(self, lang: str = "en") -> BootstrapResponse:
        """Handle bootstrap ValueSets request"""
        return await self.service.bootstrap_value_sets(lang)
    
    async def get_value_set(self, key: str, lang: str = "en") -> ValueSetItemsResponse:
        """Handle get ValueSet request"""
        result = await self.service.get_value_set(key, lang)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ValueSet '{key}' not found"
            )
        return result
    
    async def create_value_set(self, data: ValueSetCreate, created_by: str) -> ValueSetResponse:
        """Handle create ValueSet request"""
        try:
            return await self.service.create_value_set(data, created_by)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    async def update_value_set(self, key: str, data: ValueSetUpdate) -> ValueSetResponse:
        """Handle update ValueSet request"""
        result = await self.service.update_value_set(key, data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ValueSet '{key}' not found"
            )
        return result
    
    async def archive_value_set(self, key: str) -> None:
        """Handle archive ValueSet request"""
        success = await self.service.archive_value_set(key)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ValueSet '{key}' not found"
            )