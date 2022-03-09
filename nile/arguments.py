def get_arguments():
    import argparse

    parser = argparse.ArgumentParser(description='Unofficial Amazon Games client')
    sub_parsers = parser.add_subparsers(dest='command')

    auth_parser = sub_parsers.add_parser('auth', help='Authorization related things')
    auth_parser.add_argument('--login', '-l', action="store_true", help='Login action')
    auth_parser.add_argument('--logout', action="store_true", help='Logout from the accout and deregister')

    test_parser = sub_parsers.add_parser('test')

    return parser.parse_known_args()
