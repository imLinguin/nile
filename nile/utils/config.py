import os
import json
# YAML ready (currently not needed though)
# import yaml
import logging
from typing import Union
from enum import Enum
import nile.constants as constants


class ConfigType(Enum):
    RAW = 0
    JSON = 1
    # YAML = 2


class Config:
    """
    Handles writing and reading from config with automatic in memory caching
    TODO: Make memory caching opt out in some cases
    """

    def __init__(self):
        self.logger = logging.getLogger("CONFIG")
        self.cache = {}

    def _join_path_name(self, name: str, cfg_type: ConfigType) -> str:
        extension = "json"
        if cfg_type == ConfigType.RAW:
            extension = "raw"
        # elif cfg_type == ConfigType.YAML:
        #     extension = "yaml"
        elif cfg_type == ConfigType.JSON:
            extension = "json"
        return os.path.join(constants.CONFIG_PATH, f"{name}.{extension}")

    def check_if_config_dir_exists(self):
        """
        Checks if config dir exists
        creates directory if needed
        """
        if not os.path.exists(constants.CONFIG_PATH):
            os.makedirs(constants.CONFIG_PATH)

    def remove(self, store, cfg_type):
        """
        Remove file
        """
        path = self._join_path_name(store, cfg_type)
        if os.path.exists(path):
            os.remove(path)

    def write(self, store: str, data: any, cfg_type=ConfigType.JSON):
        """
        Stringifies data to json and overrides file contents
        """
        self.check_if_config_dir_exists()
        directory, filename = os.path.split(
            self._join_path_name(store, cfg_type))
        os.makedirs(directory, exist_ok=True)
        file_path = self._join_path_name(store, cfg_type)
        self.cache.update({store: data})
        mode = "w"
        if cfg_type == ConfigType.RAW:
            parsed = data
            mode += "b"
        # elif cfg_type == ConfigType.YAML:
        #     parsed = yaml.safe_dump(data)
        elif cfg_type == ConfigType.JSON:
            parsed = json.dumps(data)
        stream = open(file_path, mode)

        stream.write(parsed)

    def get(self, store: str, key: Union[str, list] = None, cfg_type=ConfigType.JSON) -> any or None:
        """
        Get value of provided key from store
        Double slash separated keys can access object values
        e.g tokens//bearer//access_token
        If no key provided returns whole file
        """
        file_path = self._join_path_name(store, cfg_type)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            if not self.cache.get(store):
                if cfg_type == ConfigType.RAW:
                    stream = open(file_path, "rb")
                    data = stream.read()
                    stream.close()
                    return data
                elif cfg_type == ConfigType.JSON:
                    stream = open(file_path, "r")
                    data = stream.read()
                    parsed = json.loads(data)
                    self.cache.update({store: parsed})
                    stream.close()
                # elif cfg_type == ConfigType.YAML:
                #     stream = open(file_path, "r")
                #     parsed = yaml.safe_load(stream)
                #     stream.close()

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
