from mongomini.config import Config
from mongomini.iters import ModelIterable


class DocumentMetaclass(type):

    def __new__(cls, name, bases, attrs):
        config = attrs.pop('Config', None)
        config_attrs = {}

        parent_db = None
        parent_fields = set()

        for p in reversed(bases):
            if isinstance(p, DocumentMetaclass):
                parent_db = p._config.db
                parent_fields = parent_fields.union(p._config.fields)

        config_attrs['db'] = getattr(config, 'db', parent_db)
        config_attrs['collection_name'] = getattr(config, 'collection_name', name.lower())

        fields = set(getattr(config, 'fields', {}))
        fields = fields.union(parent_fields)
        fields.add('_id')
        config_attrs['fields'] = fields

        new_class = super().__new__(cls, name, bases, attrs)
        new_class._config = Config(config_attrs)
        return new_class


class Document(metaclass=DocumentMetaclass):

    def __new__(cls, *args, **kwargs):
        if cls._config.abstract:
            raise TypeError('Abstract documents cannot be instantiated.')
        
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
            raise TypeError("Instances without an _id value are unhashable.")
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
        result = self._config.collection.insert(doc)
        self.pk = result.inserted_id

    def _update(self):
        self._config.collection.update(self.to_dict())

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
        if self.pk is None:
            raise AssertionError("{} object can't be deleted because its _id attribute is set to None.".format(
                self.__class__.__name__
            ))
        self._config.collection.delete_by_id(self.pk)
