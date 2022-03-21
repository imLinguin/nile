import sys
import os
import shutil
import shlex
import subprocess
import logging
import json
from nile.utils.search import calculate_distance


class LaunchInstruction:
    def __init__(self):
        self.version = str()
        self.command = str()
        self.arguments = list()

    @classmethod
    def parse(cls, game_path, path, unknown_arguments):
        instruction = cls()
        stream = open(path, "r")
        raw_data = stream.read()
        json_data = json.loads(raw_data)
        stream.close()
        instruction.version = json_data["SchemaVersion"]
        instruction.command = os.path.join(game_path, json_data["Main"]["Command"])
        instruction.arguments = json_data["Main"]["Args"]
        instruction.arguments.extend(unknown_arguments)
        return instruction


class Launcher:
    def __init__(self, config_manager, arguments, unknown_arguments):
        self.config = config_manager
        self.bottle = arguments.bottle
        self.wrapper = arguments.wrapper
        self.wine_prefix = arguments.wine_prefix
        self.wine_bin = arguments.wine
        self.dont_use_wine = arguments.dont_use_wine
        self.logger = logging.getLogger("LAUNCHER")
        self.unknown_arguments = unknown_arguments

    def _get_installed_data(self):
        return self.config.get("installed")

    def _get_bottles_bin(self):
        os_path = shutil.which("bottles")
        flatpak_path = shutil.which("flatpak")
        if os_path:
            return [os_path]
        elif flatpak_path:
            process = subprocess.run(["flatpak", "info", "com.usebottles.bottles"])

            if process.returncode != 1:
                return [flatpak_path, "run", "com.usebottles.bottles"]
        return None

    def create_bottles_command(self, exe, arguments=[]):
        command = self._get_bottles_bin() + ["-b", self.bottle, "-e", exe]
        if len(arguments) > 0:
            command.extend(["-a", arguments])
        return command

    def start(self, game_path):

        if not os.path.exists(game_path):
            self.logger.error(
                "Unable to launch a game: installation path doesn't exist"
            )
            return

        # Parse fuel.json file
        fuel_path = os.path.join(game_path, "fuel.json")

        if not os.path.exists(fuel_path):
            self.logger.error("Unable to launch a game: fuel.json doesn't exist")
            return

        instruction = LaunchInstruction.parse(
            game_path, fuel_path, self.unknown_arguments
        )

        command = list()
        environment = os.environ.copy()
        if sys.platform == "win32":
            command.append(instruction.command)
            command.extend(instruction.arguments)
        else:
            if self.wine_prefix and not self.dont_use_wine:
                environment.update({"WINEPREFIX": self.wine_prefix})
                command.append(self.wine_bin)
                command.append(instruction.command)
                command.extend(instruction.arguments)
            elif self.bottle and self._get_bottles_bin() and self.dont_use_wine:
                command = self.create_bottles_command(
                    instruction.command, arguments=instruction.arguments
                )
            elif self.wrapper and self.dont_use_wine:
                splited_wrapper = shlex.split(self.wrapper)
                command.extend(splitted_wrapper)
                command.append(instruction.command)
                command.extend(instruction.arguments)
        process = subprocess.Popen(command, cwd=game_path, env=environment)

        return process.wait()
