import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class CachedValueSet:
    data: Dict[str, Any]
    items_by_code: Dict[str, Dict[str, Any]]
    resolved_labels: Dict[str, Dict[str, str]]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def is_expired(self, ttl_minutes: int = 10) -> bool:
        return datetime.utcnow() - self.timestamp > timedelta(minutes=ttl_minutes)


class ValueSetCache:
    def __init__(self, ttl_minutes: int = 10):
        self._cache: Dict[str, CachedValueSet] = {}
        self._ttl_minutes = ttl_minutes
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[CachedValueSet]:
        async with self._lock:
            cached = self._cache.get(key)
            if cached and not cached.is_expired(self._ttl_minutes):
                return cached
            elif cached:
                del self._cache[key]
            return None
    
    async def set(self, key: str, value_set: Dict[str, Any]) -> CachedValueSet:
        async with self._lock:
            items_by_code = {item["code"]: item for item in value_set["items"]}
            
            resolved_labels = {}
            for lang in self._get_all_languages(value_set["items"]):
                resolved_labels[lang] = {}
                for item in value_set["items"]:
                    label = item["labels"].get(lang, item["labels"].get("en", item["code"]))
                    resolved_labels[lang][item["code"]] = label
            
            cached = CachedValueSet(
                data=value_set,
                items_by_code=items_by_code,
                resolved_labels=resolved_labels
            )
            
            self._cache[key] = cached
            return cached
    
    async def invalidate(self, key: Optional[str] = None):
        async with self._lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()
    
    async def get_all_cached(self) -> Dict[str, CachedValueSet]:
        async with self._lock:
            valid_cache = {}
            keys_to_remove = []
            
            for key, cached in self._cache.items():
                if not cached.is_expired(self._ttl_minutes):
                    valid_cache[key] = cached
                else:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._cache[key]
            
            return valid_cache
    
    def _get_all_languages(self, items: List[Dict[str, Any]]) -> set:
        languages = {"en"}
        for item in items:
            languages.update(item.get("labels", {}).keys())
        return languages


value_set_cache = ValueSetCache()