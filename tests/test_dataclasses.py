from bson import ObjectId
import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from mongomini.dataclasses import dataclass, insert_one, update_one, delete_one


@pytest_asyncio.fixture
async def database():
    client = AsyncIOMotorClient()
    await client.drop_database('test')
    return client['test']


def test_dataclass_creation(database):
    with pytest.raises(AssertionError):
        @dataclass(db=database)
        class Foo:
            ...
    
    @dataclass(db=database)
    class Foo:
        _id: ObjectId | None = None


@pytest.mark.asyncio
async def test_insert(database):
    @dataclass(db=database)
    class Foo:
        _id: ObjectId | None = None
    
    f = Foo()
    await insert_one(f)
    assert f._id is not None


@pytest.mark.asyncio
async def test_update(database):
    @dataclass(db=database)
    class Foo:
        _id: ObjectId | None = None
        name: str = ""
    
    f = Foo()
    await insert_one(f)

    f.name = "Fred"
    await update_one(f)
    
    doc = await database['foo'].find_one({"_id": f._id})
    assert doc["name"] == "Fred"
    

@pytest.mark.asyncio
async def test_delete(database):
    @dataclass(db=database)
    class Foo:
        _id: ObjectId | None = None
    
    f = Foo()
    await insert_one(f)
    await delete_one(f)

    assert await database['foo'].find_one({"_id": f._id}) is None
