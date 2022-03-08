import sys
import logging
from nile.arguments import get_arguments
from nile.api import authorization
from nile.gui import webview


class CLI:
    def handle_auth(self):
        manager = authorization.AuthenticationManager()
        manager.login()        



def main():
    arguments, unknown_arguments = get_arguments()
    logging_level = logging.DEBUG if arguments.debug else logging.INFO
    logging.basicConfig(
        level=logging_level, format="%(levelname)s [%(name)s]:\t %(message)s"
    )
    logger = logging.getLogger("CLI")
    cli = CLI()

    command = arguments.command

    if command == "auth":
        cli.handle_auth()
    elif command == "test":
        webview.spawn_window()
    return 0


if __name__ == "__main__":
    sys.exit(main())
