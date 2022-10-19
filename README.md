# mongomini
Interact with MongoDB using Python Dataclasses.


```
from dataclasses import dataclass
from pymongo import MongoClient
from bson import ObjectId
from mongomini import ObjectManager

# No need to inherit from a Base class.
# Your dataclasses are completely your own.
# The only requirement is an '_id' field.
@dataclass
class MyDocument:
  _id: ObjectId = None


client = MongoClient()
db = client['test_db']
collection = db['my_collection']

# An object manager uses a dataclass and a collection
# to perform basic MongoDB functions on your dataclass objects.
object_manager = ObjectManager(MyDocument, collection)

obj = MyDocument()

await object_manager.insert(obj)


```
