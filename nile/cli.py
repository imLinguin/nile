import sys
import logging
from PyQt5.Qt import QCoreApplication
from PyQt5.QtWidgets import QApplication
from nile.arguments import get_arguments
from nile.utils.config import Config
from nile.api import authorization, session
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
        self.arguments = arguments
        self.logger = logger
        self.unknown_arguments = unknown_arguments

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
    def test(self):
        print("TEST")
        # print(self.auth_manager.refresh_token())


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

    if command == "auth":
        # If spawned a gui method use qApplication exec to wait
        if cli.handle_auth():
            return qApp.exec()
    elif command == "test":
        cli.test()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
