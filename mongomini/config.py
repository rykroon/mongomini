

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
        assert isinstance(self.abstract, bool)
        assert isinstance(self.fields, set)
        for f in self.fields:
            assert isinstance(f, str)
            assert f.isidentifier()

