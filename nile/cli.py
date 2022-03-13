import sys
import logging
from PyQt5.QtWidgets import QApplication
from nile.arguments import get_arguments
from nile.utils.config import Config
from nile.api import authorization, session, library
from nile.gui import webview


class CLI:
    def __init__(
        self, session_manager, config_manager, logger, arguments, unknown_arguments
    ):
        self.config = config_manager
        self.session = session_manager
        self.auth_manager = authorization.AuthenticationManager(
            self.session, self.config
        )
        self.library_manager = library.Library(self.config, self.session)
        self.arguments = arguments
        self.logger = logger
        self.unknown_arguments = unknown_arguments
        if self.auth_manager.is_token_expired():
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
            games.sort(key=self.sort_by_title)
            for game in games:
                games_list += f'{game["product"]["title"]} GENRES: {game["product"]["productDetail"]["details"]["genres"]}\n'

            games_list += f"\n*** TOTAL {len(games)} ***\n"
            print(games_list)

        elif cmd == "sync":
            if not self.auth_manager.is_logged_in():
                self.logger.error("User not logged in")
                sys.exit(1)
            self.library_manager.sync()

    def test(self):
        print("TEST")


def main():
    qApp = QApplication(sys.argv)
    arguments, unknown_arguments = get_arguments()

    debug_mode = "-d" in unknown_arguments or "--debug" in arguments
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
