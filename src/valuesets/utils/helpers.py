from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..service.value_set_service import ValueSetService


_service_instance: Optional['ValueSetService'] = None


def set_service_instance(service: 'ValueSetService'):
    global _service_instance
    _service_instance = service


def get_service() -> 'ValueSetService':
    if _service_instance is None:
        raise RuntimeError("ValueSetService not initialized. Call set_service_instance first.")
    return _service_instance


async def validate_enum(key: str, code: str) -> bool:
    service = get_service()
    return await service.validate_enum(key, code)


async def ensure_enum(key: str, code: str):
    service = get_service()
    await service.ensure_enum(key, code)


async def get_enum_items(key: str, lang: str = "en") -> List[Dict[str, str]]:
    service = get_service()
    return await service.get_enum_items(key, lang)


async def get_label(key: str, code: str, lang: str = "en") -> Optional[str]:
    service = get_service()
    return await service.get_label(key, code, lang)


async def preload_enums(keys: Optional[List[str]] = None, lang: str = "en") -> Dict[str, List[Dict[str, str]]]:
    service = get_service()
    return await service.preload_enums(keys, lang)


async def refresh_enum_cache(key: Optional[str] = None):
    service = get_service()
    await service.refresh_enum_cache(key)