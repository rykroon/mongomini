

class BaseIterable:

    def __init__(self, cursor, document_class):
        self.cursor = cursor
        self.document_class = document_class


class ModelIterable(BaseIterable):

    def __iter__(self):
        for doc in self.cursor:
            yield self.document_class(**doc)

    