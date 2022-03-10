import os
import json
import logging
import nile.constants as constants


class Config:
    def __init__(self):
        self.logger = logging.getLogger("CONFIG")

    def _join_path_name(self, name: str) -> str:
        return os.path.join(constants.CONFIG_PATH, f"{name}.json")

    def check_if_config_dir_exists(self):
        """
        Checks if config dir exists
        creates directory if needed
        """
        if not os.path.exists(constants.CONFIG_PATH):
            os.makedirs(constants.CONFIG_PATH)

    def write(self, store: str, data: any):
        """
        Stringifies data to json and overrides file contents
        """
        self.check_if_config_dir_exists()
        file_path = self._join_path_name(store)
        parsed = json.dumps(data)
        stream = open(file_path, "w")

        stream.write(parsed)

    def get(self, store: str, key: str or list = None) -> any or None:
        """
        Get value of provided key from store
        Double slash separated keys can access object values
        e.g tokens//bearer//access_token
        If no key provided returns whole file
        """
        file_path = self._join_path_name(store)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            stream = open(file_path, "r")
            data = stream.read()

            parsed = json.loads(data)
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
        return None

    def _get_value_based_on_keys(self, parsed, keys):
        if len(keys) > 1:
            iterator = parsed
            for key in keys:
                iterator = iterator[key]

            return iterator

        return parsed.get(keys[0])
