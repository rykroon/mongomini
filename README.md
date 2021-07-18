# mongomini
A minimalistic MongoDB ODM


```
from pymongo import MongoClient
from mongomini import Document


client = MongoClient()
db = client['test_db']


class Foo(Document):
  class Config:
    db = db
    fields = {'name', 'description', 'price'}
    
    
f = Foo()
f.save()


```
