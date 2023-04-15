import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from mongomini import Document


@pytest.fixture
async def database():
    client = AsyncIOMotorClient()
    await client.drop_database('test')
    return client['test']


@pytest.mark.asyncio
def test_abstract_one(database):
    """
        A non abstract class that inherits from an abstract class.
    """

    class Abstract(Document):
        class Settings:
            abstract = True
    
    with pytest.raises(TypeError):
        Abstract()
    
    class NotAbstract(Abstract):
        class Settings:
            db = database
    
    NotAbstract()


@pytest.mark.asyncio
def test_abstract_two(database):

    """
        An abstract class that inherits from a non abstract class.
    """

    class NotAbstract(Document):
        class Settings:
            db= database
    
    NotAbstract()

    class Abstract(NotAbstract):
        class Settings:
            abstract = True
    
    with pytest.raises(TypeError):
        Abstract()



def test_database_inheritance():
    ...


def test_collection_name():
    ...

