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
from nile.constants import CONFIG_PATH
from nile.utils.process import Process

class NoMoreChildren(Exception):
    pass


class LaunchInstruction:
    def __init__(self):
        self.version = str()
        self.command = str()
        self.arguments = list()
        self.cwd = str()

    @classmethod
    def parse(cls, game_path, path, unknown_arguments):
        instruction = cls()
        stream = open(path, "r")
        raw_data = stream.read()
        json_data = json5.loads(raw_data)
        stream.close()
        instruction.version = json_data["SchemaVersion"]
        instruction.command = os.path.join(game_path, json_data["Main"]["Command"].replace("\\", os.sep))
        instruction.arguments = json_data["Main"].get("Args") or list()
        instruction.arguments.extend(unknown_arguments)
        instruction.cwd = game_path
        working_dir_override = json_data["Main"].get("WorkingSubdirOverride")
        if working_dir_override:
            instruction.cwd = os.path.join(game_path, working_dir_override.replace("\\", os.sep))
        return instruction


class Launcher:
    def __init__(self, config_manager, arguments, unknown_arguments, game):
        self.config = config_manager
        self.game = game
        self.bottle = arguments.bottle
        self.wrapper = arguments.wrapper
        self.wine_prefix = arguments.wine_prefix
        self.wine_bin = arguments.wine
        if not self.wine_bin:
            self.wine_bin = shutil.which("wine")
        self.dont_use_wine = arguments.dont_use_wine
        self.logger = logging.getLogger("LAUNCHER")
        self.unknown_arguments = unknown_arguments
        self.flatpak_installed = shutil.which("flatpak")


        self.env = self.sanitize_environment()
        self.bottles_bin = self._get_bottles_bin()

    def _get_installed_data(self):
        return self.config.get("installed")

    def sanitize_environment(self) -> dict:
        env = os.environ.copy()
        # For pyinstaller environment - avoid shadowing libraries for subprocesses
        # /tmp/hash/nile/utils/launch.py -> /tmp/hash/nile/utils -> /tmp/hash
        if not getattr(sys, 'frozen', False) and not hasattr(sys, '_MEIPASS'):
            return env
        bundle_dir = sys._MEIPASS

        ld_library = env.get("LD_LIBRARY_PATH")
        if ld_library:
            splitted = ld_library.split(":")
            try:
                splitted.remove(bundle_dir)
            except ValueError:
                pass
            env.update({"LD_LIBRARY_PATH": ":".join(splitted)})
        
        return env


    def get_scummvm_command(self):
        os_path = shutil.which("scummvm")
        output_command = []
        if not os_path and self.flatpak_installed:
            flatpak_exists = subprocess.run(
                ["flatpak", "info", "org.scummvm.ScummVM"], stdout=subprocess.DEVNULL, env=self.env).returncode == 0
            if flatpak_exists:
                output_command = ["flatpak", "run", "org.scummvm.ScummVM"]
        elif os_path:
            output_command = [os_path]
        return output_command


    def _get_bottles_bin(self):
        os_path = shutil.which("bottles-cli")
        if os_path:
            return [os_path, "run"]
        elif self.flatpak_installed:
            process = subprocess.run(
                ["flatpak", "info", "com.usebottles.bottles"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=self.env
            )

            if process.returncode != 1:
                return [
                    self.flatpak_installed,
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

        display_name = self.config.get('user', 'extensions//customer_info//given_name') or ''
        
        sdk_path = os.path.join(CONFIG_PATH, 'SDK', 'Amazon Games Services')
        fuel_dir = os.path.join(sdk_path, 'Legacy')
        amazon_sdk = os.path.join(sdk_path, 'AmazonGamesSDK')

        self.env.update({
            'FUEL_DIR': fuel_dir,
            'AMAZON_GAMES_SDK_PATH': amazon_sdk,
            'AMAZON_GAMES_FUEL_ENTITLEMENT_ID': self.game['id'],
            'AMAZON_GAMES_FUEL_PRODUCT_SKU': self.game['product']['sku'],
            'AMAZON_GAMES_FUEL_DISPLAY_NAME': display_name
            })


        command = list()
        if self.wrapper:
            splited_wrapper = shlex.split(self.wrapper)
            command.extend(splited_wrapper)
        if sys.platform == "win32":
            command.append(instruction.command)
            command.extend(instruction.arguments)
        else:
            scummvm_command = self.get_scummvm_command()
            if instruction.command.lower().endswith("scummvm.exe") and len(scummvm_command) > 0:
                self.logger.info(f"Using native scummvm {scummvm_command}")
                command = scummvm_command
                command.extend(instruction.arguments)
            else:
                if not self.dont_use_wine and not self.bottle:
                    if self.wine_prefix:
                        self.env.update({"WINEPREFIX": self.wine_prefix})
                    command.append(self.wine_bin)
                    command.append(instruction.command)
                    command.extend(instruction.arguments)
                elif self.bottle and self.bottles_bin:
                    command = self.create_bottles_command(
                        instruction.command, arguments=instruction.arguments
                    )
                else: 
                    command.append(instruction.command)
                    command.extend(instruction.arguments)

        self.logger.info("Launching")
        
        status = 0

        if sys.platform == 'linux':
            libc = ctypes.cdll.LoadLibrary("libc.so.6")
            prctl = libc.prctl
            result = prctl(36 ,1, 0, 0, 0, 0) # PR_SET_CHILD_SUBREAPER = 36

            if result == -1:
                print("PR_SET_CHILD_SUBREAPER is not supported by your kernel (Linux 3.4 and above)")

            process = subprocess.Popen(command, cwd=instruction.cwd, env=self.env)
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
            process = subprocess.Popen(command, cwd=instruction.cwd, env=self.env)
            status = process.wait()

        sys.exit(status)
