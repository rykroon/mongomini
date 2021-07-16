from mongomini.config import Config
from mongomini.iters import ModelIterable

class DocumentMetaclass(type):

    def __new__(cls, name, bases, attrs):
        config = attrs.pop('Config', None)
        config_attrs = dict(config.__dict__) if config else {}

        parent_db = None
        parent_fields = set()

        for p in reversed(bases):
            if isinstance(p, DocumentMetaclass):
                parent_db = p._config.db
                parent_fields = parent_fields.union(p._config.fields)

        if not config_attrs.get('db'):
            config_attrs['db'] = parent_db

        if not config_attrs.get('collection_name'):
            config_attrs['collection_name'] = name.lower()

        fields = set(config_attrs.get('fields', {}))
        fields = fields.union(parent_fields)
        fields.add('_id')
        config_attrs['fields'] = fields

        new_class = super().__new__(cls, name, bases, attrs)
        new_class._config = Config(config_attrs)
        return new_class


class Document(metaclass=DocumentMetaclass):

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        for f in cls._config.fields:
            setattr(instance, f, kwargs.get(f))
        return instance

    def __eq__(self, other):
        if not isinstance(other, Document):
            return False

        if self.pk is None:
            return self is other

        return self.pk == other.pk

    def __hash__(self):
        if self.pk is None:
            raise TypeError
        return hash(self.pk)

    @classmethod
    def find(cls, **kwargs):
        cursor = cls._config.collection.find(**kwargs)
        return ModelIterable(cursor, cls)

    @property
    def pk(self):
        return self._id

    @pk.setter
    def pk(self, value):
        self._id = value

    def _insert(self):
        doc = self.to_dict(exclude=['_id'])
        result = self._config.collection.insert_one(doc)
        self.pk = result.inserted_id

    def _update(self):
        self._config.collection.update_one(
            {'_id': self.pk},
            {'$set': self.to_dict()}
        )

    def to_dict(self, include=None, exclude=None):
        if include and exclude:
            raise ValueError

        result = {}
        for f in self._config.fields:
            if include and f not in include:
                continue

            if exclude and f in exclude:
                continue

            result[f] = getattr(self, f, None)

        return result

    def save(self):
        if not self.pk:
            self._insert()
        else:
            self._update()

    def delete(self):
        self._config.collection.delete_one({'_id': self.pk})
