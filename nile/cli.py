#!/usr/bin/env python3

import sys
import logging
import json
from PyQt5.QtWidgets import QApplication
from nile.arguments import get_arguments
from nile.downloading import manager
from nile.utils.config import Config
from nile.utils.launch import Launcher
from nile.utils.search import calculate_distance
from nile.api import authorization, session, library
from nile.gui import webview
from nile.models import manifest
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
                self.auth_manager.login()
                return True
            else:
                self.logger.error("You are already logged in")
                return False
        elif self.arguments.logout:
            self.auth_manager.logout()
            return False
        self.logger.error("Specify auth action, use --help")

    def sort_by_title(self, element):
        return element["product"]["title"]

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
                games_list += f'{"(INSTALLED) " if installed_dict.get(game["id"]) and not self.arguments.installed else ""}{game["product"]["title"]} ID: {game["id"]} GENRES: {game["product"]["productDetail"]["details"]["genres"]}\n'
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

        if not installed_array:
            self.logger.error("No games installed")
            return

        # Prepare array of game ids
        game_ids = dict()
        for game in installed_array:
            game_ids.update({game["id"]: game})
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
        games = self.config.get("library")
        games.sort(key=self.sort_by_title)

        print("Games with updates:")
        for game in games:
            if game["id"] in updateable:
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
            f"Checking if game {game['product']['title']} id: {matching_game['id']} is installed"
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

    def test(self):
        print("TEST")


def main():
    qApp = QApplication(sys.argv)
    arguments, unknown_arguments = get_arguments()
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

    # Always use return qApp.exec()
    # If you spawn gui stuff
    # When running in CLI this can be ignored

    if command == "auth":
        # If spawned a gui method use qApplication exec to wait
        if cli.handle_auth():
            return qApp.exec()

    elif command == "library":
        cli.handle_library()
    elif command == "test":
        cli.test()
    elif command in ["install", "verify", "update"]:
        cli.handle_install()
    elif command == "list-updates":
        cli.list_updates()
    elif command == "launch":
        cli.handle_launch()
    return 0


if __name__ == "__main__":
    sys.exit(main())
