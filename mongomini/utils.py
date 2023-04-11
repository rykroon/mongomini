from motor.motor_asyncio import AsyncIOMotorCollection


class CollectionDescriptor:

    """
        A descriptor that will return a MongoDB Collection.
        The owner is expected to have a 'db' value.
        The collection name will default to the name of the owner
        class all lowercase. You can provide a collection name
        upon instantiation.
    """

    def __init__(self, collection_name: str | None = None):
        self.collection_name = collection_name

    def __get__(self, obj, objtype=None) -> AsyncIOMotorCollection:
        if obj is not None:
            raise TypeError("Cannot access 'collection' from instance.")

        collection_name = (
            objtype.__name__.lower()
            if self.collection_name is None
            else self.collection_name
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
