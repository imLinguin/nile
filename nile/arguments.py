def get_arguments():
    import argparse

    parser = argparse.ArgumentParser(description="Unofficial Amazon Games client")
    parser.add_argument(
        "--version",
        dest="version",
        action="store_true",
        help="Display nile version",
    )
    sub_parsers = parser.add_subparsers(dest="command")

    auth_parser = sub_parsers.add_parser("auth", help="Authorization related things")
    auth_parser.add_argument("--login", "-l", action="store_true", help="Login action")
    auth_parser.add_argument(
        "--logout", action="store_true", help="Logout from the accout and deregister"
    )

    library_parser = sub_parsers.add_parser(
        "library", help="Your games library is in this place"
    )
    library_parser.add_argument("sub_command", choices=["list", "sync"])

    install_parser = sub_parsers.add_parser(
        "install", aliases=["update", "verify"], help="Install a game"
    )
    install_parser.add_argument(
        "title", help="Specify a title of the game to be installed"
    )
    install_parser.add_argument("--max-workers", help="Specify max threads to be used")
    install_parser.add_argument(
        "--base-path",
        dest="base_path",
        help="Specify base installation path e.g /home/USERNAME/Games/nile It'll append save filename to that path",
    )
    install_parser.add_argument("--path", dest="exact_path", help="Specify exact install location")

    check_for_updates_parser = sub_parsers.add_parser("list-updates")
    check_for_updates_parser.add_argument("--json", action="store_true", help="Output data in json format")
    test_parser = sub_parsers.add_parser("test")

    return parser.parse_known_args()
