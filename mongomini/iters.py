

class BaseIterable:

    def __init__(self, cursor, document_class):
        self.cursor = cursor
        self.document_class = document_class
        self._cache = []


class ModelIterable(BaseIterable):

    def __iter__(self):
        if self._cache:
            for instance in self._cache:
                yield instance
        
        else:
            for doc in self.cursor:
                instance = self.document_class(**doc)
                self._cache.append(instance)
                yield instance

    