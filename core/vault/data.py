from abc import abstractmethod, ABC


class DataVault(ABC):

    def __init__(self, id):
        self.id = id

    @abstractmethod
    def set(self, key, object):
        pass

    @abstractmethod
    def get(self, key, default):
        pass

    @abstractmethod
    def delete(self, key):
        pass
