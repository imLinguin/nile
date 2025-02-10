from os import path

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
    auth_parser.add_argument("--status", "-s", action="store_true", help="Login action")
    auth_parser.add_argument("--gui", "-g", action="store_true", help="Use GUI for login")
    auth_parser.add_argument("--non-interactive", action="store_true", help="Display login data as JSON. Use `nile register` to finish login")
    auth_parser.add_argument(
        "--logout", action="store_true", help="Logout from the accout and deregister"
    )

    register_parser = sub_parsers.add_parser("register", help="Register device after web login")
    register_parser.add_argument("--code", help="The authorization code from web login")
    register_parser.add_argument("--client-id", help="The client id to register")
    register_parser.add_argument("--code-verifier", help="The code verifier used to generate login URL")
    register_parser.add_argument("--serial", help="The device serial to register")

    library_parser = sub_parsers.add_parser(
        "library", help="Your games library is in this place..."
    )
    library_parser.add_argument("sub_command", choices=["list", "sync"])
    library_parser.add_argument(
         "--json", "-j", action="store_true", help="Print info in JSON format"
    )
    library_parser.add_argument("--force", "-f", action="store_true", help="Force the action")
    library_parser.add_argument(
        "--installed", "-i", action="store_true", help="List only installed games...    "
        
    )
   
    install_parser = sub_parsers.add_parser(
        "install", aliases=["update", "verify"], help="Install a game"
        
    )
    install_parser.add_argument("id", help="Specify a ID of the game to be installed")
    install_parser.add_argument("--max-workers", help="Specify max threads to be used")
    install_parser.add_argument(
        "--base-path",
        dest="base_path",
        help="Specify base installation path e.g /home/USERNAME/Games/nile It'll append save filename to that path",
    )
    install_parser.add_argument(
        "--path", dest="exact_path", help="Specify exact install location"
    )
    install_parser.add_argument(
        '--info', '-i', action="store_true", help="Print game install info instead of downloading" 
    )
    install_parser.add_argument(
        '--json', '-j', action="store_true", help="Print info in JSON format"
    )

    check_for_updates_parser = sub_parsers.add_parser("list-updates")
    check_for_updates_parser.add_argument(
        "--json", action="store_true", help="Output data in json format"
    )

    launch_parser = sub_parsers.add_parser("launch", help="Launch installed games")
    launch_parser.add_argument("id")
    launch_parser.add_argument(
        "--bottle", "-b", help="Specify bottle to use (requires Bottles)"
    )
    launch_parser.add_argument(
        "--wine-prefix", dest="wine_prefix", help="Specify wineprefix to be used"
    )
    launch_parser.add_argument("--wine", help="Specify wine binary")
    launch_parser.add_argument(
        "--json",
        "-j",
      
        action="store_true",
        help="Output data in json format",
    )
    launch_parser.add_argument(
        "--no-wine",
        dest="dont_use_wine",
        action="store_true",
        help="Don't use wine (useful when specifying custom wrapper)",
    )
    launch_parser.add_argument(
        "--wrapper", help="Wrapper to bue used when launching a game"
    )

    uninstall_parser = sub_parsers.add_parser(
        "uninstall", help="Uninstall game - deletes game files specified in manifest"
    )
    uninstall_parser.add_argument("id", help="Game id")
    import_parser = sub_parsers.add_parser("import", help="Import games installed outside nile")
    import_parser.add_argument("--path", help="Path to the game's installation folder", type=path.abspath)
    import_parser.add_argument("id", help="The id of the game to import")

    return parser.parse_known_args(), parser
