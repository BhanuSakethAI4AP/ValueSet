from typing import Dict, List, Optional, Any
from ..repository.value_set_repository import ValueSetRepository
from ..schemas.value_set_schemas import (
    ValueSetCreate,
    ValueSetUpdate,
    ValueSetRead,
    ValueSetListItem,
    ValueSetItemResponse,
    ValueSetItemsResponse,
    BootstrapResponse
)
from ..utils.cache import value_set_cache


class ValueSetService:
    def __init__(self, repository: ValueSetRepository):
        self.repository = repository
        self.cache = value_set_cache
    
    async def create_value_set(self, data: ValueSetCreate) -> ValueSetRead:
        if await self.repository.exists(data.key):
            raise ValueError(f"ValueSet with key '{data.key}' already exists")
        
        doc_data = data.model_dump()
        created_doc = await self.repository.create(doc_data)
        
        await self.cache.invalidate(data.key)
        
        return ValueSetRead(**created_doc)
    
    async def update_value_set(self, key: str, data: ValueSetUpdate) -> Optional[ValueSetRead]:
        update_data = data.model_dump(exclude_unset=True)
        
        updated_doc = await self.repository.update(key, update_data)
        if not updated_doc:
            return None
        
        await self.cache.invalidate(key)
        
        return ValueSetRead(**updated_doc)
    
    async def archive_value_set(self, key: str) -> bool:
        success = await self.repository.archive(key)
        if success:
            await self.cache.invalidate(key)
        return success
    
    async def get_value_set(self, key: str, lang: str = "en") -> Optional[ValueSetItemsResponse]:
        cached = await self.cache.get(key)
        
        if cached:
            value_set = cached.data
        else:
            value_set = await self.repository.get_by_key(key)
            if not value_set:
                return None
            cached = await self.cache.set(key, value_set)
        
        items = []
        for item in value_set["items"]:
            label = cached.resolved_labels.get(lang, {}).get(
                item["code"],
                item["labels"].get("en", item["code"])
            )
            items.append(ValueSetItemResponse(code=item["code"], label=label))
        
        return ValueSetItemsResponse(
            key=value_set["key"],
            status=value_set["status"],
            items=items
        )
    
    async def list_value_sets(
        self,
        status: Optional[str] = None,
        search_text: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[ValueSetListItem], int]:
        docs, total = await self.repository.list(status, search_text, skip, limit)
        
        items = []
        for doc in docs:
            items.append(ValueSetListItem(
                key=doc["key"],
                status=doc["status"],
                count=len(doc.get("items", [])),
                update_date_time=doc["update_date_time"]
            ))
        
        return items, total
    
    async def bootstrap_value_sets(self, lang: str = "en") -> BootstrapResponse:
        active_sets = await self.repository.get_all_active()
        
        result = {}
        for value_set in active_sets:
            cached = await self.cache.get(value_set["key"])
            if not cached:
                cached = await self.cache.set(value_set["key"], value_set)
            
            items = []
            for item in value_set["items"]:
                label = cached.resolved_labels.get(lang, {}).get(
                    item["code"],
                    item["labels"].get("en", item["code"])
                )
                items.append(ValueSetItemResponse(code=item["code"], label=label))
            
            result[value_set["key"]] = items
        
        return BootstrapResponse(data=result)
    
    async def validate_enum(self, key: str, code: str) -> bool:
        cached = await self.cache.get(key)
        
        if cached:
            value_set = cached.data
        else:
            value_set = await self.repository.get_by_key(key)
            if value_set:
                cached = await self.cache.set(key, value_set)
        
        if not value_set or value_set["status"] == "archived":
            return False
        
        return code in cached.items_by_code
    
    async def ensure_enum(self, key: str, code: str):
        is_valid = await self.validate_enum(key, code)
        if not is_valid:
            raise ValueError(f"Invalid enum value: {key}.{code}")
    
    async def get_enum_items(self, key: str, lang: str = "en") -> List[Dict[str, str]]:
        value_set_response = await self.get_value_set(key, lang)
        if not value_set_response:
            return []
        
        return [{"code": item.code, "label": item.label} for item in value_set_response.items]
    
    async def get_label(self, key: str, code: str, lang: str = "en") -> Optional[str]:
        cached = await self.cache.get(key)
        
        if not cached:
            value_set = await self.repository.get_by_key(key)
            if not value_set:
                return None
            cached = await self.cache.set(key, value_set)
        
        return cached.resolved_labels.get(lang, {}).get(
            code,
            cached.items_by_code.get(code, {}).get("labels", {}).get("en", code)
        )
    
    async def preload_enums(self, keys: Optional[List[str]] = None, lang: str = "en") -> Dict[str, List[Dict[str, str]]]:
        if keys:
            result = {}
            for key in keys:
                items = await self.get_enum_items(key, lang)
                if items:
                    result[key] = items
            return result
        else:
            bootstrap = await self.bootstrap_value_sets(lang)
            return {
                key: [{"code": item.code, "label": item.label} for item in items]
                for key, items in bootstrap.data.items()
            }
    
    async def refresh_enum_cache(self, key: Optional[str] = None):
        await self.cache.invalidate(key)
        
        if key:
            value_set = await self.repository.get_by_key(key)
            if value_set:
                await self.cache.set(key, value_set)
        else:
            active_sets = await self.repository.get_all_active()
            for value_set in active_sets:
                await self.cache.set(value_set["key"], value_set)