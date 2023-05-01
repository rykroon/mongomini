from dataclasses import dataclass
from .dataclasses import documentclass
from .utils import has_collection


class DocumentMeta(type):

    def __new__(metacls, name, bases, attrs):
        new_cls = super().__new__(metacls, name, bases, attrs)

        if name == 'Document' and not bases:
            # if Base Document, then just make a regular dataclass.
            return dataclass(new_cls)

        settings: type | None = attrs.pop('Settings', None)

        db = getattr(settings, 'db', None)
        collection_name = getattr(settings, 'collection_name', "")
        repr = getattr(settings, 'repr', True)
        eq = getattr(settings, 'eq', True)
        order = getattr(settings, 'order', False)

        new_cls = documentclass(
            db=db, collection_name=collection_name, repr=repr, eq=eq, order=order
        )(new_cls)
        return new_cls

    def __call__(self, *args, **kwargs):
        if not has_collection(self):
            raise TypeError(f"Can't instantiate abstract class '{self.__name__}'.")
        return super().__call__(*args, **kwargs)
