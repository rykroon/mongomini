from pymongo import ASCENDING, DESCENDING


class Index:
    
    def __init__(self, fields, name=None, unique=None, sparse=None):
        self.fields = fields
        self.keys = [
            (f[1:], DESCENDING) if f.startswith('-') else (f, ASCENDING) for f in fields
        ]
        self.name = name
        self.unique = unique
        self.sparse = sparse

    def __eq__(self, other):
        return self.name == other.name and self.fields == other.fields

    def create(self):
        ...

    def exists(self):
        ...