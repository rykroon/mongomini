from dataclasses import is_dataclass, fields



class QueryManager:

    def __init__(self, cls_, collection):
        self.document_class = cls_
        self.collection = collection

    def get_many(self, query):
        ...

    async def get(self, query):
        ...

    async def insert(self, obj):
        ...

    async def update(self, obj):
        ...

    async def delete(self, obj):
        ...

    

class ObjectCursor:

    def __init__(self):
        ...

    def __aiter__(self):
        return self

    async def __anext__(self):
        result = await self._cursor.next()
        return ...




# dict factories

class Include:
    def __init__(self, *fields):
        self.fields = fields

    def __call__(self, iterable):
        return {k: v for k, v in iterable if k in self.fields}


class Exclude:
    def __init__(self, *fields):
        self.fields = fields

    def __call__(self, iterable):
        return {k: v for k, v in iterable if k not in self.fields}


def from_document(cls_: type, document: dict):
    if not is_dataclass(cls_):
        raise TypeError

    field_names = (f.name for f in fields(cls_))
    kwargs = {f: document[f] for f in field_names if f in document}
    return cls_(**kwargs)