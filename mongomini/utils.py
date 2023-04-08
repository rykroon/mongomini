

def include(*fields: str):
    def include_dict_factory(iterable):
        return {k: v for k, v in iterable if k in fields}
    return include_dict_factory


def exclude(*fields):
    def exclude_dict_factory(iterable):
        return {k: v for k, v in iterable if k not in fields}
    return exclude_dict_factory
