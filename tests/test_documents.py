import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from mongomini import Document


@pytest_asyncio.fixture
async def database():
    client = AsyncIOMotorClient()
    await client.drop_database('test')
    return client['test']


def test_abstract_inheritance(database):
    """
        The abstract property should not be inherited.
    """

    class Foo(Document):
        class Settings:
            db = database
    
    assert Foo._meta.abstract is False

    class Bar(Foo):
        class Settings:
            abstract = True
    
    assert Bar._meta.abstract is True

    class Baz(Bar):
        ...
    
    assert Baz._meta.abstract is False


def test_database_inheritance(database):

    class Foo(Document):
        class Settings:
            db = database
        
    class Bar(Foo):
        ...
    
    assert Foo._meta.db == Bar._meta.db


def test_collection_name(database):
    class Foo(Document):
        class Settings:
            db = database
    
    assert Foo._meta.collection_name == 'foo'
    assert Foo._meta.collection.name == 'foo'


def test_custom_collection_name(database):
    class Foo(Document):
        class Settings:
            db = database
            collection_name = "foobar"
    
    assert Foo._meta.collection_name == "foobar"
    assert Foo._meta.collection.name == "foobar"


def test_cannot_instantiate_abstract_class():

    class Foo(Document):
        class Settings:
            abstract = True

    with pytest.raises(TypeError):
        Foo()


def test_non_abstract_class_without_db():
    with pytest.raises(AssertionError):
        class Foo(Document):
            ...
