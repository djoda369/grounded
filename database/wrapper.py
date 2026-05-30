import copy
from typing import Any

from database.connector import media_table, create_if_not_exists


class MediaAirtableWrapper:
    def __init__(self, default: dict, key: str, value: str):
        self.default = default
        self.key = key
        self.value = value

    def wrap(self, elements: dict[str, Any]):
        wrapped_elements = []
        for key, value in elements.items():
            items = copy.deepcopy(self.default)
            items[self.key] = key
            items[self.value] = value
            self.save(items)
            wrapped_elements.append(items)

        return wrapped_elements

    def save(self, media_data: dict):
        create_if_not_exists(media_table, "URL", media_data["URL"], media_data)
