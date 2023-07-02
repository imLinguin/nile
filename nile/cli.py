#!/usr/bin/env python3

import sys
import logging
import json
from nile.arguments import get_arguments
from nile.downloading import manager
from nile.utils.config import Config
from nile.utils.launch import Launcher
from nile.utils.uninstall import Uninstaller
from nile.api import authorization, session, library
from nile import constants, version, codename


class CLI:
    def __init__(
        self, session_manager, config_manager, logger, arguments, unknown_arguments
    ):
        self.config = config_manager
        self.session = session_manager
        self.library_manager = library.Library(self.config, self.session)
        self.auth_manager = authorization.AuthenticationManager(
            self.session, self.config, self.library_manager
        )
        self.arguments = arguments
        self.logger = logger
        self.unknown_arguments = unknown_arguments
        if self.auth_manager.is_logged_in() and self.auth_manager.is_token_expired():
            self.auth_manager.refresh_token()

    def handle_auth(self):
        if self.arguments.login:
            if not self.auth_manager.is_logged_in():
                self.auth_manager.login(self.arguments.non_interactive)
                return True
            else:
                self.logger.error("You are already logged in")
                return False
        elif self.arguments.logout:
            self.auth_manager.logout()
            return False
        self.logger.error("Specify auth action, use --help")
    
    def handle_register(self):
        if self.auth_manager.is_logged_in():
            self.logger.error("You are already logged in")
            return False

        code = self.arguments.code
        client_id = self.arguments.client_id
        code_verifier = self.arguments.code_verifier
        serial = self.arguments.serial

        if not code:
            self.logger.error("--code is required, use --help")
            return False
        if not client_id:
            self.logger.error("--client-id is required, use --help")
            return False
        if not code_verifier:
            self.logger.error("--code-verifier is required, use --help")
            return False
        if not serial:
            self.logger.error("--serial is required, use --help")
            return False

        self.auth_manager.handle_login(code, client_id, code_verifier, serial)
        return True

    def sort_by_title(self, element):
        return (
            element["product"].get("title")
            if element["product"].get("title") is not None
            else ""
        )

    def handle_library(self):
        cmd = self.arguments.sub_command

        if cmd == "list":
            games_list = ""
            games = self.config.get("library")
            installed = self.config.get("installed")
            installed_dict = dict()
            if installed:
                for game in installed:
                    installed_dict[game["id"]] = game
            games.sort(key=self.sort_by_title)
            displayed_count = 0
            for game in games:
                if self.arguments.installed and not installed_dict.get(game["id"]):
                    continue
                genres = (
                    (f'GENRES: {game["product"]["productDetail"]["details"]["genres"]}')
                    if game["product"]["productDetail"]["details"].get("genres")
                    else ""
                )
                if not constants.SUPPORTS_COLORS:
                    games_list += f'{"(INSTALLED) " if installed_dict.get(game["id"]) and not self.arguments.installed else ""}{game["product"].get("title")} ID: {game["id"]} {genres}\n'
                else:
                    games_list += f'{constants.SHCOLORS["green"]}{"(INSTALLED) " if installed_dict.get(game["id"]) and not self.arguments.installed else ""}{constants.SHCOLORS["clear"]}{game["product"].get("title")} {constants.SHCOLORS["red"]}ID: {game["id"]}{constants.SHCOLORS["clear"]} {genres}\n'

                displayed_count += 1
            games_list += f"\n*** TOTAL {displayed_count} ***\n"
            print(games_list)

        elif cmd == "sync":
            if not self.auth_manager.is_logged_in():
                self.logger.error("User not logged in")
                sys.exit(1)
            self.library_manager.sync()

    def handle_install(self):
        games = self.config.get("library")
        games.sort(key=self.sort_by_title)
        matching_game = None
        for game in games:
            if game["id"] == self.arguments.id:
                matching_game = game
                break
        if not matching_game:
            self.logger.error("Couldn't find what you are looking for")
            return
        self.logger.info(f"Found: {matching_game['product']['title']}")
        self.download_manager = manager.DownloadManager(
            self.config, self.library_manager, self.session, matching_game
        )
        self.download_manager.download(
            force_verifying=bool(self.arguments.command == "verify"),
            base_install_path=self.arguments.base_path,
            install_path=self.arguments.exact_path,
        )
        self.logger.info("Download complete")

    def list_updates(self):
        installed_array = self.config.get("installed")
        games = self.config.get("library")

        if not installed_array:
            self.logger.error("No games installed")
            return

        # Prepare array of game ids
        game_ids = dict()
        for game in games:
            for installed_game in installed_array:
                if game["id"] == installed_game["id"]:
                    game_ids.update({game["product"]["id"]: installed_game})
        self.logger.debug(
            f"Checking for updates for {list(game_ids.keys())}, count: {len(game_ids)}"
        )
        versions = self.library_manager.get_versions(list(game_ids.keys()))

        updateable = list()

        for version in versions:
            if version["versionId"] != game_ids[version["adgProductId"]]["version"]:
                updateable.append(version["adgProductId"])
        self.logger.debug(f"Updateable games: {updateable}")
        if self.arguments.json:
            print(json.dumps(updateable))
            return

        if len(updateable) == 0:
            self.logger.info("No updates available")
            return

        games.sort(key=self.sort_by_title)

        print("Games with updates:")
        for game in games:
            if game["product"]["id"] in updateable:
                print(game["product"]["title"])
        print(f"NUMBER OF GAMES: {len(updateable)}")

    def handle_launch(self):
        games = self.config.get("library")
        matching_game = None
        self.logger.info(f"Searching for {self.arguments.id}")
        for game in games:
            if game["id"] == self.arguments.id:
                matching_game = game
                break
        if not matching_game:
            self.logger.error("No game match")
            return
        self.logger.debug(f"Found {matching_game['product']['title']}")

        self.logger.debug(
            f"Checking if game {matching_game['product']['title']} id: {matching_game['id']} is installed"
        )
        installed_games = self.config.get("installed")

        if not installed_games:
            self.logger.error("No game is installed")
            return

        found = None
        for installed_game in installed_games:
            if installed_game["id"] == matching_game["id"]:
                found = installed_game
                break

        if not found:
            self.logger.error("Game is not installed")
            return

        launcher = Launcher(self.config, self.arguments, self.unknown_arguments)

        launcher.start(found["path"])

    def handle_uninstall(self):
        uninstaller = Uninstaller(self.config, self.arguments)
        uninstaller.uninstall()


def main():
    (arguments, unknown_arguments), parser = get_arguments()
    if arguments.version:
        print(version, codename)
        return 0
    debug_mode = "-d" in unknown_arguments or "--debug" in unknown_arguments
    if debug_mode:
        if "-d" in unknown_arguments:
            unknown_arguments.remove("-d")
        elif "--debug" in unknown_arguments:
            unknown_arguments.remove("--debug")

    logging_level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=logging_level, format="%(levelname)s [%(name)s]:\t %(message)s"
    )
    logger = logging.getLogger("CLI")

    config_manager = Config()
    session_manager = session.APIHandler(config_manager)
    cli = CLI(session_manager, config_manager, logger, arguments, unknown_arguments)

    command = arguments.command

    if command == "auth":
        cli.handle_auth()
    elif command == "register":
        cli.handle_register()
    elif command == "library":
        cli.handle_library()
    elif command in ["install", "verify", "update"]:
        cli.handle_install()
    elif command == "list-updates":
        cli.list_updates()
    elif command == "launch":
        cli.handle_launch()
    elif command == "uninstall":
        cli.handle_uninstall()
    else:
        print(
            "You didn't provide any argument, GUI will be there someday, for now here is help"
        )
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
