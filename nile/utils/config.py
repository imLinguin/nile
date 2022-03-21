import os
import json
import logging
import nile.constants as constants


class Config:
    """
    Handles writing and reading from config with automatic in memory caching
    TODO: Make memory caching opt out in some cases
    """
    def __init__(self):
        self.logger = logging.getLogger("CONFIG")
        self.cache = {}

    def _join_path_name(self, name: str) -> str:
        return os.path.join(constants.CONFIG_PATH, f"{name}.json")

    def check_if_config_dir_exists(self):
        """
        Checks if config dir exists
        creates directory if needed
        """
        if not os.path.exists(constants.CONFIG_PATH):
            os.makedirs(constants.CONFIG_PATH)

    def write(self, store: str, data: any, raw=False):
        """
        Stringifies data to json and overrides file contents
        """
        self.check_if_config_dir_exists()
        directory, filename = os.path.split(self._join_path_name(store))
        os.makedirs(directory, exist_ok=True)
        file_path = self._join_path_name(store)
        self.cache.update({store: data})
        mode = "w"
        if raw:
            parsed = data
            mode+="b"
        else:
            parsed = json.dumps(data)
        stream = open(file_path, mode)

        stream.write(parsed)

    def get(self, store: str, key: str or list = None, raw=False) -> any or None:
        """
        Get value of provided key from store
        Double slash separated keys can access object values
        e.g tokens//bearer//access_token
        If no key provided returns whole file
        """
        file_path = self._join_path_name(store)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            if not self.cache.get(store):
                if raw:
                    stream = open(file_path, "rb")
                    data = stream.read()
                    return data
                stream = open(file_path, "r")
                data = stream.read()
                parsed = json.loads(data)
                self.cache.update({store: parsed})
            else:
                parsed = self.cache[store]
            if not key:
                return parsed
            if type(key) is str:
                keys = key.split("//")
                return self._get_value_based_on_keys(parsed, keys)
            elif type(key) is list:
                array = list()
                for option in key:
                    keys = option.split("//")
                    array.append(self._get_value_based_on_keys(parsed, keys))
                return array

        if type(key) is list:
            return [None for i in key]
        return None

    def _get_value_based_on_keys(self, parsed, keys):
        if len(keys) > 1:
            iterator = parsed.copy()
            for key in keys:
                iterator = iterator[key]

            return iterator
        return parsed.get(keys[0])
