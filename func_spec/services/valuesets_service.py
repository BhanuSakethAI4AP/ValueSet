from typing import Dict, List, Optional, Any
from func_spec.repositories.valuesets_repository import ValueSetsRepository
from schema_spec.schemas.valuesets import *


class ValueSetsService:
    """Service layer for ValueSets business logic"""
    
    def __init__(self, repository: ValueSetsRepository):
        self.repository = repository
    
    async def create_value_set(self, data: ValueSetCreate, created_by: str) -> ValueSetResponse:
        """Create a new ValueSet"""
        # Set created_by
        create_data = data.model_dump()
        create_data["created_by"] = created_by
        
        # Check if key already exists
        if await self.repository.key_exists(data.key):
            raise ValueError(f"ValueSet with key '{data.key}' already exists")
        
        created = await self.repository.create(create_data)
        return ValueSetResponse(**created)
    
    async def get_value_set(self, key: str, lang: str = "en") -> Optional[ValueSetItemsResponse]:
        """Get ValueSet items with localized labels"""
        doc = await self.repository.get_by_key(key)
        if not doc:
            return None
        
        items = []
        for item in doc.get("items", []):
            label = item["labels"].get(lang, item["labels"].get("en", item["code"]))
            items.append(ValueSetItemResponse(code=item["code"], label=label))
        
        return ValueSetItemsResponse(
            key=doc["key"],
            status=doc["status"],
            items=items
        )
    
    async def update_value_set(self, key: str, data: ValueSetUpdate) -> Optional[ValueSetResponse]:
        """Update ValueSet"""
        update_data = data.model_dump(exclude_unset=True)
        updated = await self.repository.update_by_key(key, update_data)
        
        if not updated:
            return None
        
        return ValueSetResponse(**updated)
    
    async def archive_value_set(self, key: str) -> bool:
        """Archive ValueSet"""
        return await self.repository.archive_by_key(key)
    
    async def list_value_sets(
        self,
        status: Optional[str] = None,
        search_text: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ValueSetListItem]:
        """List ValueSets with filters"""
        docs, total = await self.repository.list_with_filters(status, search_text, skip, limit)
        
        items = []
        for doc in docs:
            items.append(ValueSetListItem(
                key=doc["key"],
                status=doc["status"],
                count=len(doc.get("items", [])),
                update_date_time=doc["update_date_time"]
            ))
        
        return items
    
    async def bootstrap_value_sets(self, lang: str = "en") -> BootstrapResponse:
        """Get all active ValueSets for bootstrap"""
        docs = await self.repository.get_all_active()
        
        result = {}
        for doc in docs:
            items = []
            for item in doc.get("items", []):
                label = item["labels"].get(lang, item["labels"].get("en", item["code"]))
                items.append(ValueSetItemResponse(code=item["code"], label=label))
            
            result[doc["key"]] = items
        
        return BootstrapResponse(data=result)