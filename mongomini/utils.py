

def include(*fields: str):
    def inner(iterable):
        return {k: v for k, v in iterable if k in fields}
    return inner


def exclude(*fields):
    def inner(iterable):
        return {k: v for k, v in iterable if k not in fields}
    return inner
