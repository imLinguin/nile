import os
import base64
import json
# YAML ready (currently not needed though)
# import yaml
import logging
from typing import Union
from enum import Enum
import nile.constants as constants
from nile.arguments import get_arguments


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

    def remove(self, store, cfg_type=ConfigType.JSON):
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
        parsed = None
        file_path = self._join_path_name(store, cfg_type)
        if self.cache.get(store):
            parsed = self.cache[store]
        elif os.path.exists(file_path) and os.path.isfile(file_path):
            if cfg_type == ConfigType.RAW:
                with open(file_path, "rb") as stream:
                    return stream.read()
            elif cfg_type == ConfigType.JSON:
                with open(file_path, "r") as stream:
                    parsed = json.loads(stream.read())
                    self.cache.update({store: parsed})
            # elif cfg_type == ConfigType.YAML:
            #     with open(file_path, "r") as stream:
            #       parsed = yaml.safe_load(stream)
        elif store == "user":
            (arguments, unknown_arguments), parser = get_arguments()
            if arguments.secret_user_data:
                secret_user_data_json = base64.b64decode(arguments.secret_user_data).decode("utf-8")
                secret_user_data_json = json.loads(secret_user_data_json)
                parsed = secret_user_data_json
                self.cache.update({store: parsed})

        if parsed is None:
            if type(key) is list:
                return [None for i in key]
            return None

        if not key:
            return parsed

        if type(key) is str:
            keys = key.split("//")
            return self._get_value_based_on_keys(parsed, keys)

        if type(key) is list:
            array = list()
            for option in key:
                keys = option.split("//")
                array.append(self._get_value_based_on_keys(parsed, keys))
            return array
        return None

    def _get_value_based_on_keys(self, parsed, keys):
        if len(keys) > 1:
            iterator = parsed.copy()
            for key in keys:
                iterator = iterator[key]

            return iterator
        return parsed.get(keys[0])
