


# dict factories

class Include:
    def __init__(self, *fields):
        self.fields = fields

    def __call__(self, iterable):
        return {k: v for k, v in iterable if k in self.fields}


class Exclude:
    def __init__(self, *fields):
        self.fields = fields

    def __call__(self, iterable):
        return {k: v for k, v in iterable if k not in self.fields}

