import sys
import logging
from nile.arguments import get_arguments
from nile.api import authorization, session
from nile.gui import webview


class CLI:
    def __init__(self, session_manager):
        self.session = session_manager

    def handle_auth(self):
        manager = authorization.AuthenticationManager(self.session)
        manager.login()


def main():
    arguments, unknown_arguments = get_arguments()

    debug_mode = "-d" in unknown_arguments or "--debug" in arguments
    logging_level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=logging_level, format="%(levelname)s [%(name)s]:\t %(message)s"
    )
    logger = logging.getLogger("CLI")

    # Silent pywebview errors
    # logging.getLogger('pywebview').setLevel(logging.CRITICAL)
    session_manager = session.APIHandler(None)
    cli = CLI(session_manager)

    command = arguments.command

    if command == "auth":
        cli.handle_auth()
    elif command == "test":
        manager = authorization.AuthenticationManager(session_manager)
        
        manager.generate_device_id()
        manager.generate_challange(manager.generate_code_verifier())
        manager.generate_device_serial()
        # manager.register_device('')
    return 0


if __name__ == "__main__":
    sys.exit(main())
