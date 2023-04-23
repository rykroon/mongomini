import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from mongomini import Document, ObjectDoesNotExist, MultipleObjectsReturned

@pytest_asyncio.fixture
async def database():
    client = AsyncIOMotorClient()
    await client.drop_database('test')
    return client['test']


@pytest.fixture
def Foo(database):
    class Foo(Document):
        class Settings:
            db = database
        
        name: str

    return Foo


@pytest.mark.asyncio
async def test_insert(Foo, database):
    f = Foo(name="Fred")
    await f.insert()

    assert await database['foo'].find_one({'_id': f._id}) is not None


@pytest.mark.asyncio
async def test_update(Foo, database):
    f = Foo(name="Fred")
    await f.insert()
    f.name = "Bob"
    await f.update()

    assert await database['foo'].find_one({'name': 'Bob'}) is not None
    assert await database['foo'].find_one({'name': 'Fred'}) is None


@pytest.mark.asyncio
async def test_delete(Foo, database):
    f = Foo(name="Fred")
    await f.insert()
    await f.delete()
    assert await database['foo'].find_one({'_id': f._id}) is None


@pytest.mark.asyncio
async def test_get(Foo, database):
    f1 = Foo(name="Fred")
    await f1.insert()

    f2 = await Foo.get({'_id': f1._id})
    assert f1 == f2


@pytest.mark.asyncio
async def test_get_object_does_not_exist(Foo, database):
    with pytest.raises(ObjectDoesNotExist):
        await Foo.get({'name': "Fred"})


@pytest.mark.asyncio
async def test_get_multiple_objects_returned(Foo, database):
    f1 = Foo(name="Fred")
    await f1.insert()

    f2 = Foo(name="Fred")
    await f2.insert()

    with pytest.raises(MultipleObjectsReturned):
        await Foo.get({"name": "Fred"})

