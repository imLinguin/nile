import sys
import os
import shutil
import shlex
import subprocess
import logging
import json5
import time
import signal
import ctypes
from nile.utils.process import Process

class NoMoreChildren(Exception):
    pass


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
        json_data = json5.loads(raw_data)
        stream.close()
        instruction.version = json_data["SchemaVersion"]
        instruction.command = os.path.join(game_path, json_data["Main"]["Command"])
        instruction.arguments = json_data["Main"].get("Args") or list()
        instruction.arguments.extend(unknown_arguments)
        return instruction


class Launcher:
    def __init__(self, config_manager, arguments, unknown_arguments):
        self.config = config_manager
        self.bottle = arguments.bottle
        self.wrapper = arguments.wrapper
        self.wine_prefix = arguments.wine_prefix
        self.wine_bin = arguments.wine
        if not self.wine_bin:
            self.wine_bin = shutil.which("wine")
        self.dont_use_wine = arguments.dont_use_wine
        self.logger = logging.getLogger("LAUNCHER")
        self.unknown_arguments = unknown_arguments

        self.bottles_bin = self._get_bottles_bin()

    def _get_installed_data(self):
        return self.config.get("installed")

    def _get_bottles_bin(self):
        os_path = shutil.which("bottles-cli")
        flatpak_path = shutil.which("flatpak")
        if os_path:
            return [os_path, "run"]
        elif flatpak_path:
            process = subprocess.run(
                ["flatpak", "info", "com.usebottles.bottles"], stdout=subprocess.DEVNULL
            )

            if process.returncode != 1:
                return [
                    flatpak_path,
                    "run",
                    "--command=bottles-cli",
                    "com.usebottles.bottles",
                    "run",
                ]
        return None

    def create_bottles_command(self, exe, arguments=[]):
        command = self._get_bottles_bin() + ["-b", self.bottle, "-e", exe]
        if len(arguments) > 0:
            command.extend(["-a"] + arguments)
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
            if self.wrapper:
                splited_wrapper = shlex.split(self.wrapper)
                command.extend(splited_wrapper)
            if not self.dont_use_wine and not self.bottle:
                if self.wine_prefix:
                    environment.update({"WINEPREFIX": self.wine_prefix})
                command.append(self.wine_bin)
                command.append(instruction.command)
                command.extend(instruction.arguments)
            elif self.bottle and self.bottles_bin:
                command = self.create_bottles_command(
                    instruction.command, arguments=instruction.arguments
                )
        self.logger.info("Launching")
        
        status = 0

        if sys.platform == 'linux':
            libc = ctypes.cdll.LoadLibrary("libc.so.6")
            prctl = libc.prctl
            result = prctl(36 ,1, 0, 0, 0, 0) # PR_SET_CHILD_SUBREAPER = 36

            if result == -1:
                print("PR_SET_CHILD_SUBREAPER is not supported by your kernel (Linux 3.4 and above)")

            process = subprocess.Popen(command, cwd=game_path, env=environment)
            process_pid = process.pid

            def iterate_processes():
                for child in Process(os.getpid()).iter_children():
                    if child.state == 'Z':
                        continue

                    if child.name:
                        yield child

            def hard_sig_handler(signum, _frame):
                for _ in range(3):  # just in case we race a new process.
                    for child in Process(os.getpid()).iter_children():
                        try:
                            os.kill(child.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass


            def sig_handler(signum, _frame):
                signal.signal(signal.SIGTERM, hard_sig_handler)
                signal.signal(signal.SIGINT, hard_sig_handler)
                for _ in range(3):  # just in case we race a new process.
                    for child in Process(os.getpid()).iter_children():
                        try:
                            os.kill(child.pid, signal.SIGTERM)
                        except ProcessLookupError:
                            pass

            def is_alive():
                return next(iterate_processes(), None) is not None

            signal.signal(signal.SIGTERM, sig_handler)
            signal.signal(signal.SIGINT, sig_handler)

            def reap_children():
                nonlocal status
                while True:
                    try:
                        child_pid, child_returncode, _resource_usage = os.wait3(os.WNOHANG)
                    except ChildProcessError:
                        raise NoMoreChildren from None  # No processes remain.
                    if child_pid == process_pid:
                        status = child_returncode

                    if child_pid == 0:
                        break

            try:
                # The initial wait loop:
                #  the initial process may have been excluded. Wait for the game
                #  to be considered "started".
                if not is_alive():
                    while not is_alive():
                        reap_children()
                        time.sleep(0.1)
                while is_alive():
                    reap_children()
                    time.sleep(0.1)
                reap_children()
            except NoMoreChildren:
                print("All processes exited")


        else:
            process = subprocess.Popen(command, cwd=game_path, env=environment)
            status = process.wait()

        sys.exit(status)
