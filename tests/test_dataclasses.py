from bson import ObjectId
import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from mongomini.dataclasses import (
    documentclass, insert_one, update_one, delete_one, find_one, find
)


@pytest_asyncio.fixture
async def database():
    client = AsyncIOMotorClient()
    await client.drop_database('test')
    return client['test']


def test_dataclass_creation(database):
    # Missing a database.
    with pytest.raises(AssertionError):
        @documentclass
        class Foo:
            _id: ObjectId | None = None

    # Missing an _id field.
    with pytest.raises(AssertionError):
        @documentclass(db=database)
        class Foo:
            ...

    @documentclass(db=database)
    class Foo:
        _id: ObjectId | None = None
    
    assert Foo.__mongomini_collection__.database == database


def test_database_inheritance(database):

    @documentclass(db=database)
    class Foo:
        _id: ObjectId | None = None

    @documentclass
    class Bar(Foo):
        ...

    assert Foo.__mongomini_collection__.database == database
    assert Bar.__mongomini_collection__.database == database


@pytest.mark.asyncio
async def test_insert(database):
    @documentclass(db=database)
    class Foo:
        _id: ObjectId | None = None
    
    f = Foo()
    await insert_one(f)

    assert f._id is not None
    assert await database['foo'].find_one({'_id': f._id}) is not None


@pytest.mark.asyncio
async def test_update(database):
    @documentclass(db=database)
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
    @documentclass(db=database)
    class Foo:
        _id: ObjectId | None = None
    
    f = Foo()
    await insert_one(f)
    await delete_one(f)

    assert await database['foo'].find_one({"_id": f._id}) is None


@pytest.mark.asyncio
async def test_non_documentclasses_in_documentclass_functions():
    class Foo:
        ...

    with pytest.raises(TypeError):
        f = Foo()
        await insert_one(f)
    
    with pytest.raises(TypeError):
        f = Foo()
        await update_one(f)
    
    with pytest.raises(TypeError):
        f = Foo()
        await delete_one(f)

    with pytest.raises(TypeError):
        await find_one(Foo, {})
    
    with pytest.raises(TypeError):
        find(Foo, {})
