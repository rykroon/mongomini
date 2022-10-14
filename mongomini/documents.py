from dataclasses import dataclass

from bson import ObjectId



@dataclass
class Document:

    _id: ObjectId = None

    @classmethod
    def new(cls, *args, **kwargs):
        obj = cls()
        obj.init(*args, **kwargs)
        return obj

    def init(self):
        ...

    @property
    def pk(self):
        return self._id
    