from dataclasses import dataclass
from .utils import get_collection, set_collection


class DocumentMeta(type):

    def __new__(metacls, name, bases, attrs):
        settings: type | None = attrs.pop('Settings', None)
        new_cls = super().__new__(metacls, name, bases, attrs)

        # loop through bases to get parent db.
        parent_db = None
        for base in reversed(bases):
            if not isinstance(base, metacls):
                continue

            parent_collection = get_collection(base)
            if parent_collection is not None:
                parent_db = parent_collection.database

        db = getattr(settings, 'db', parent_db)
        collection_name = getattr(settings, 'collection_name', name.lower())
        set_collection(new_cls, None if db is None else db[collection_name])
        new_cls = dataclass(kw_only=True)(new_cls)
        return new_cls

    def __call__(self, *args, **kwargs):
        collection = get_collection(self)
        if collection is None:
            raise TypeError(f"Can't instantiate abstract class '{self.__name__}'.")
        return super().__call__(*args, **kwargs)
