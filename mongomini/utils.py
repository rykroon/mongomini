from dataclasses import fields
from functools import lru_cache


def include(*fields: str):
    def include_dict_factory(iterable):
        return {k: v for k, v in iterable if k in fields}
    return include_dict_factory


def exclude(*fields: str):
    def exclude_dict_factory(iterable):
        return {k: v for k, v in iterable if k not in fields}
    return exclude_dict_factory


@lru_cache
def get_init_field_names(cls: type) -> list[str]:
    return [f.name for f in fields(cls) if f.init]


@lru_cache
def get_non_init_field_names(cls: type) -> list[str]:
    return [f.name for f in fields(cls) if not f.init]


_COLLECTION = '__mongomini_collection__'


def get_collection(obj):
    return getattr(obj, _COLLECTION)


def set_collection(obj, collection):
    setattr(obj, _COLLECTION, collection)
