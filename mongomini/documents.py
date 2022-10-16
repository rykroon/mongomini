from dataclasses import dataclass, field

from bson import ObjectId


@dataclass
class Document:

    _id: ObjectId = field(
        default_factory=ObjectId,
    )

    @classmethod
    def new(cls, *args, **kwargs):
        obj = cls()
        obj.init(*args, **kwargs)
        return obj

    def init(self):
        ...
