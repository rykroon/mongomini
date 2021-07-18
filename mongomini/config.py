

class ImproperlyConfigured(Exception):
    pass


class Config:
    def __init__(self, attrs):
        self.abstract = attrs.get('asbtract', False)
        self.fields = attrs.get('fields', set())
        self.db = attrs.get('db')
        self.collection_name = attrs.get('collection_name')

        self.collection = None
        if self.db and not self.abstract:
            self.collection = self.db[self.collection_name]

        self.validate()

    def validate(self):
        if not isinstance(self.abstract, bool):
            raise ImproperlyConfigured

        if not isinstance(self.fields, set):
            raise ImproperlyConfigured

        for f in self.fields:
            if not isinstance(f, str):
                raise ImproperlyConfigured
            
            if not f.isidentifier():
                raise ImproperlyConfigured

