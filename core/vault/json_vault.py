import os

from core.helper.files import json_read_file, json_write_file
from core.vault.data import DataVault


class JSONVault(DataVault):

    def __init__(self, user_id: str, path: str):
        super().__init__(user_id)
        os.makedirs(path, exist_ok=True)
        self.path = os.path.join(path, user_id + ".json").replace("\\", "/")
        if os.path.exists(self.path):
            self._restore()
        else:
            self.data = {"id": user_id}

    def _restore(self):
        self.data = json_read_file(self.path)

    def _save(self):
        json_write_file(self.path, self.data)

    def set(self, key, object):
        self.data[key] = object
        self._save()

    def get(self, key, default):
        if key in self.data:
            return self.data[key]
        return default

    def delete(self, key):
        if key in self.data:
            del self.data[key]
            self._save()
