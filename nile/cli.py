#!/usr/bin/env python3

import sys
import os
import logging
import json
from nile.arguments import get_arguments
from nile.downloading import manager
from nile.utils.config import Config
from nile.utils.launch import Launcher
from nile.utils.uninstall import Uninstaller
from nile.utils.importer import Importer
from nile.api import authorization, session, library, self_update
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

        self.self_update = self_update.SelfUpdateHandler(self.session, self.library_manager)
        try:
            self.self_update.get_sdk()
        except Exception:
            self.logger.warning("There was an error getting sdk")

        self.__migrate_old_ids()

    # Function that migrates installed and manifests from old id to product.id
    def __migrate_old_ids(self):
        installed = self.config.get("installed") or []
        library = self.config.get("library") or []
        if installed:
            for installed_game in installed:
                old_id = installed_game['id']
                for game in library:
                    if game['id'] == old_id:
                        installed_game['id'] = game['product']['id']
                        manifest_path = os.path.join(constants.CONFIG_PATH, 'manifests', game['id']+'.json')
                        if os.path.exists(manifest_path):
                            os.rename(manifest_path, os.path.join(constants.CONFIG_PATH, 'manifests', game["product"]["id"]+".raw"))
                        break
        self.config.write("installed", installed)


    def handle_auth(self):
        if self.arguments.login:
            if not self.auth_manager.is_logged_in():
                self.auth_manager.login(self.arguments.non_interactive, self.arguments.gui)
                return True
            else:
                self.logger.error("You are already logged in")
                return False
        elif self.arguments.logout:
            if self.auth_manager.is_logged_in() and self.auth_manager.is_token_expired():
                self.auth_manager.refresh_token()
            self.auth_manager.logout()
            return False
        elif self.arguments.status:
            account = '<not logged in>'
            if self.auth_manager.is_logged_in():
                account = self.auth_manager.config.get("user").get("extensions").get("customer_info").get("name")              
            logged_in = account != '<not logged in>'
            print(json.dumps({'Username': account, 'LoggedIn': logged_in}))
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
        ).lower()

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
            if self.arguments.json:
                print(json.dumps(games))
            else:
                for game in games:
                    if self.arguments.installed and not installed_dict.get(game["product"]["id"]):
                        continue
                    genres = (
                        (f'GENRES: {game["product"]["productDetail"]["details"]["genres"]}')
                        if game["product"]["productDetail"]["details"].get("genres")
                        else ""
                    )
                    if not constants.SUPPORTS_COLORS:
                        games_list += f'{"(INSTALLED) " if installed_dict.get(game["product"]["id"]) and not self.arguments.installed else ""}{game["product"].get("title")} ID: {game["product"]["id"]} {genres}\n'
                    else:
                        games_list += f'{constants.SHCOLORS["green"]}{"(INSTALLED) " if installed_dict.get(game["product"]["id"]) and not self.arguments.installed else ""}{constants.SHCOLORS["clear"]}{game["product"].get("title")} {constants.SHCOLORS["red"]}ID: {game["product"]["id"]}{constants.SHCOLORS["clear"]} {genres}\n'

                    displayed_count += 1
                games_list += f"\n*** TOTAL {displayed_count} ***\n"
                print(games_list)

        elif cmd == "sync":
            if not self.auth_manager.is_logged_in():
                self.logger.error("User not logged in")
                sys.exit(1)
            if self.auth_manager.is_logged_in() and self.auth_manager.is_token_expired():
                self.auth_manager.refresh_token()
            self.library_manager.sync(force=self.arguments.force)

    def handle_install(self):
        games = self.config.get("library")
        games.sort(key=self.sort_by_title)
        matching_game = None
        for game in games:
            if game["product"]["id"] == self.arguments.id:
                matching_game = game
                break
        if not matching_game:
            self.logger.error("Couldn't find what you are looking for")
            return
        if self.auth_manager.is_logged_in() and self.auth_manager.is_token_expired():
            self.auth_manager.refresh_token()
        self.logger.info(f"Found: {matching_game['product'].get('title')}")
        self.download_manager = manager.DownloadManager(
            self.config, self.library_manager, self.session, matching_game
        )
        if not self.arguments.info:
            self.download_manager.download(
                force_verifying=bool(self.arguments.command == "verify"),
                base_install_path=self.arguments.base_path,
                install_path=self.arguments.exact_path,
            )
            self.logger.info("Download complete")
        else:
            self.download_manager.info(self.arguments.json)

    def list_updates(self):
        installed_array = self.config.get("installed")
        games = self.config.get("library")

        if not installed_array:
            if self.arguments.json:
                # An empty string is not valid JSON, so create an empty but
                # valid JSON string instead.
                print(json.dumps(list()))
            self.logger.error("No games installed")
            return

        if self.auth_manager.is_logged_in() and self.auth_manager.is_token_expired():
            self.auth_manager.refresh_token()

        # Prepare array of game ids
        game_ids = dict()
        for game in games:
            for installed_game in installed_array:
                if game["product"]["id"] == installed_game["id"]:
                    game_ids.update({game["product"]["id"]: installed_game})
        self.logger.debug(
            f"Checking for updates for {list(game_ids.keys())}, count: {len(game_ids)}"
        )
        versions = self.library_manager.get_versions(list(game_ids.keys())) or []

        updateable = list()

        for product_id, game in game_ids.items():
            version = versions[product_id]
            if version != game["version"]:
                updateable.append(product_id)
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
                print(game["product"].get("title"), game["product"]["id"])
        print(f"NUMBER OF GAMES: {len(updateable)}")

    def handle_launch(self):
        games = self.config.get("library")
        matching_game = None
        self.logger.info(f"Searching for {self.arguments.id}")
        for game in games:
            if game["product"]["id"] == self.arguments.id:
                matching_game = game
                break
        if not matching_game:
            self.logger.error("No game match")
            return
        self.logger.debug(f"Found {matching_game['product'].get('title')}")

        self.logger.debug(
            f"Checking if game {matching_game['product'].get('title')} id: {matching_game['id']} is installed"
        )
        installed_games = self.config.get("installed")

        if not installed_games:
            self.logger.error("No game is installed")
            return

        found = None
        for installed_game in installed_games:
            if installed_game["id"] == matching_game["product"]["id"]:
                found = installed_game
                break

        if not found:
            self.logger.error("Game is not installed")
            return

        launcher = Launcher(self.config, self.arguments, self.unknown_arguments, matching_game)

        launcher.start(found["path"])

    def handle_uninstall(self):
        uninstaller = Uninstaller(self.config, self.arguments)
        uninstaller.uninstall()
    
    def handle_import(self):
        id = self.arguments.id
        if not id:
            self.logger.error("id is required")
            return

        path = self.arguments.path
        if not path:
            self.logger.error("--path is required")
            return
        
        if self.auth_manager.is_logged_in() and self.auth_manager.is_token_expired():
            self.auth_manager.refresh_token()

        games = self.config.get("library")
        matching_game = None
        self.logger.info(f"Searching for {self.arguments.id}")
        for game in games:
            if game["product"]["id"] == self.arguments.id:
                matching_game = game
                break
        if not matching_game:
            self.logger.error("No game match")
            return
        self.logger.debug(f"Found {matching_game['product'].get('title')}")

        self.logger.debug(
            f"Checking if game {matching_game['product'].get('title')} id: {matching_game['id']} is already installed"
        )
        installed_games = self.config.get("installed")

        if installed_games:
            for installed_game in installed_games:
                if installed_game["id"] == matching_game["product"]["id"]:
                    self.logger.error(
                        f"{matching_game['product'].get('title')} is already installed"
                    )
                    return
        self.download_manager = manager.DownloadManager(
            self.config, self.library_manager, self.session, matching_game
        )
        importer = Importer(
            matching_game, path, self.config, self.library_manager, self.session, self.download_manager
        )
        importer.import_game()
 
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
    elif command == "import":
        cli.handle_import()
    else:
        print(
            "You didn't provide any argument, GUI will be there someday, for now here is help"
        )
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
