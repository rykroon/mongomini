from dataclasses import dataclass
from functools import cached_property

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase


@dataclass(kw_only=True, eq=False, repr=False)
class Meta:
    db: AsyncIOMotorDatabase | None = None
    collection_name: str = ""
    abstract: bool = False

    @cached_property
    def collection(self) -> AsyncIOMotorCollection | None:
        if self.abstract:
            return None
        return self.db[self.collection_name]


class DocumentMeta(type):

    def __new__(metacls, name, bases, attrs):
        # loop through bases to get parent db.
        parent_db = None
        for base in reversed(bases):
            if not isinstance(base, metacls):
                continue
            parent_db = base._meta.db

        # Set default values.
        meta: Meta = Meta(
            collection_name=name.lower(),
            db=parent_db
        )

        settings: type | None = attrs.pop('Settings', None)

        # Add attributes from Settings class.
        if hasattr(settings, 'abstract'):
            meta.abstract = settings.abstract

        if hasattr(settings, 'collection_name'):
            meta.collection_name = settings.collection_name

        if hasattr(settings, 'db'):
            meta.db = settings.db

        # Check to make sure everything is kosher.
        if not meta.abstract:
            assert meta.db is not None, "A database must be specified."

        attrs['_meta'] = meta
        new_cls = super().__new__(metacls, name, bases, attrs)
        new_cls = dataclass(kw_only=True)(new_cls)
        return new_cls

    def __call__(self, *args, **kwargs):
        if self._meta.abstract:
            raise TypeError(f"Can't instantiate abstract class '{self.__name__}'.")
        return super().__call__(*args, **kwargs)
