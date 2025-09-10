import pytest
import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from ..repository.value_set_repository import ValueSetRepository
from ..service.value_set_service import ValueSetService
from ..schemas.value_set_schemas import ValueSetCreate, ValueSetUpdate
from ..utils.cache import ValueSetCache


@pytest.fixture
async def mongo_client():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_valuesets_db
    
    yield db
    
    await db.valueSets.drop()
    client.close()


@pytest.fixture
async def repository(mongo_client):
    return ValueSetRepository(mongo_client)


@pytest.fixture
async def service(repository):
    return ValueSetService(repository)


@pytest.fixture
def sample_value_set():
    return ValueSetCreate(
        key="testEnum",
        status="active",
        description="Test enum for unit tests",
        items=[
            {"code": "CODE1", "labels": {"en": "Code One", "hi": "कोड एक"}},
            {"code": "CODE2", "labels": {"en": "Code Two"}}
        ],
        created_by=str(ObjectId())
    )


class TestValueSetRepository:
    
    @pytest.mark.asyncio
    async def test_create_with_duplicate_key_fails(self, repository, sample_value_set):
        await repository.create(sample_value_set.model_dump())
        
        with pytest.raises(ValueError, match="already exists"):
            await repository.create(sample_value_set.model_dump())
    
    @pytest.mark.asyncio
    async def test_create_and_retrieve(self, repository, sample_value_set):
        created = await repository.create(sample_value_set.model_dump())
        
        assert created["key"] == sample_value_set.key
        assert len(created["items"]) == 2
        
        retrieved = await repository.get_by_key(sample_value_set.key)
        assert retrieved["key"] == sample_value_set.key
    
    @pytest.mark.asyncio
    async def test_update_value_set(self, repository, sample_value_set):
        await repository.create(sample_value_set.model_dump())
        
        update_data = {
            "description": "Updated description",
            "items": [
                {"code": "NEW1", "labels": {"en": "New One"}}
            ]
        }
        
        updated = await repository.update(sample_value_set.key, update_data)
        
        assert updated["description"] == "Updated description"
        assert len(updated["items"]) == 1
        assert updated["items"][0]["code"] == "NEW1"
    
    @pytest.mark.asyncio
    async def test_archive_value_set(self, repository, sample_value_set):
        await repository.create(sample_value_set.model_dump())
        
        success = await repository.archive(sample_value_set.key)
        assert success is True
        
        retrieved = await repository.get_by_key(sample_value_set.key)
        assert retrieved["status"] == "archived"


class TestValueSetService:
    
    @pytest.mark.asyncio
    async def test_items_without_english_label_fails(self, service):
        invalid_set = ValueSetCreate(
            key="invalidEnum",
            status="active",
            items=[
                {"code": "CODE1", "labels": {"hi": "कोड एक"}}
            ],
            created_by=str(ObjectId())
        )
        
        with pytest.raises(ValueError, match="English label"):
            await service.create_value_set(invalid_set)
    
    @pytest.mark.asyncio
    async def test_duplicate_item_codes_fails(self, service):
        invalid_set = ValueSetCreate(
            key="duplicateEnum",
            status="active",
            items=[
                {"code": "CODE1", "labels": {"en": "Code One"}},
                {"code": "CODE1", "labels": {"en": "Code One Again"}}
            ],
            created_by=str(ObjectId())
        )
        
        with pytest.raises(ValueError, match="Duplicate codes"):
            await service.create_value_set(invalid_set)
    
    @pytest.mark.asyncio
    async def test_validate_enum(self, service, sample_value_set):
        await service.create_value_set(sample_value_set)
        
        is_valid = await service.validate_enum("testEnum", "CODE1")
        assert is_valid is True
        
        is_valid = await service.validate_enum("testEnum", "INVALID_CODE")
        assert is_valid is False
        
        is_valid = await service.validate_enum("nonExistentEnum", "CODE1")
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_validate_archived_enum_returns_false(self, service, sample_value_set):
        await service.create_value_set(sample_value_set)
        await service.archive_value_set(sample_value_set.key)
        
        is_valid = await service.validate_enum("testEnum", "CODE1")
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_get_enum_items_with_localization(self, service, sample_value_set):
        await service.create_value_set(sample_value_set)
        
        items_en = await service.get_enum_items("testEnum", "en")
        assert len(items_en) == 2
        assert items_en[0]["code"] == "CODE1"
        assert items_en[0]["label"] == "Code One"
        
        items_hi = await service.get_enum_items("testEnum", "hi")
        assert items_hi[0]["label"] == "कोड एक"
        assert items_hi[1]["label"] == "Code Two"
    
    @pytest.mark.asyncio
    async def test_get_label_with_fallback(self, service, sample_value_set):
        await service.create_value_set(sample_value_set)
        
        label_en = await service.get_label("testEnum", "CODE1", "en")
        assert label_en == "Code One"
        
        label_hi = await service.get_label("testEnum", "CODE1", "hi")
        assert label_hi == "कोड एक"
        
        label_hi_fallback = await service.get_label("testEnum", "CODE2", "hi")
        assert label_hi_fallback == "Code Two"
    
    @pytest.mark.asyncio
    async def test_bootstrap_only_returns_active(self, service):
        active_set = ValueSetCreate(
            key="activeEnum",
            status="active",
            items=[{"code": "ACTIVE", "labels": {"en": "Active Item"}}],
            created_by=str(ObjectId())
        )
        
        archived_set = ValueSetCreate(
            key="archivedEnum",
            status="archived",
            items=[{"code": "ARCHIVED", "labels": {"en": "Archived Item"}}],
            created_by=str(ObjectId())
        )
        
        await service.create_value_set(active_set)
        await service.create_value_set(archived_set)
        
        bootstrap = await service.bootstrap_value_sets()
        
        assert "activeEnum" in bootstrap.data
        assert "archivedEnum" not in bootstrap.data


class TestValueSetCache:
    
    @pytest.mark.asyncio
    async def test_cache_ttl_behavior(self):
        cache = ValueSetCache(ttl_minutes=0.01)
        
        value_set = {
            "key": "testEnum",
            "status": "active",
            "items": [
                {"code": "CODE1", "labels": {"en": "Code One"}}
            ]
        }
        
        await cache.set("testEnum", value_set)
        
        cached = await cache.get("testEnum")
        assert cached is not None
        
        await asyncio.sleep(1)
        
        cached = await cache.get("testEnum")
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_cache_refresh(self, service, sample_value_set):
        await service.create_value_set(sample_value_set)
        
        items = await service.get_enum_items("testEnum")
        assert len(items) == 2
        
        update = ValueSetUpdate(
            items=[
                {"code": "NEWCODE", "labels": {"en": "New Code"}}
            ]
        )
        await service.update_value_set("testEnum", update)
        
        await service.refresh_enum_cache("testEnum")
        
        items = await service.get_enum_items("testEnum")
        assert len(items) == 1
        assert items[0]["code"] == "NEWCODE"