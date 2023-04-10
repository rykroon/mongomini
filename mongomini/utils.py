from motor.motor_asyncio import AsyncIOMotorCollection


class CollectionDescriptor:

    def __get__(self, obj, objtype=None) -> AsyncIOMotorCollection:
        if obj is not None:
            raise TypeError("Cannot access 'collection' from instance.")
        
        if objtype.db is None:
            raise TypeError('Must specify a database to access the collection.')

        collection_name = (
            objtype.__name__.lower()
            if objtype.collection_name is None
            else objtype.collection_name
        )

        return objtype.db[collection_name]


def include(*fields: str):
    def include_dict_factory(iterable):
        return {k: v for k, v in iterable if k in fields}
    return include_dict_factory


def exclude(*fields: str):
    def exclude_dict_factory(iterable):
        return {k: v for k, v in iterable if k not in fields}
    return exclude_dict_factory
