import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from mongomini import Document


@pytest_asyncio.fixture
async def database():
    client = AsyncIOMotorClient()
    await client.drop_database('test')
    return client['test']


def test_document_with_no_db():
    with pytest.raises(TypeError):
        Document()


def test_database_inheritance(database):

    class Foo(Document):
        class Settings:
            db = database

    class Bar(Foo):
        ...

    assert Foo.__mongomini_collection__.database == Bar.__mongomini_collection__.database


def test_collection_name(database):
    class Foo(Document):
        class Settings:
            db = database

    assert Foo.__mongomini_collection__.name == 'foo'


def test_custom_collection_name(database):
    class Foo(Document):
        class Settings:
            db = database
            collection_name = "foobar"

    assert Foo.__mongomini_collection__.name == "foobar"
