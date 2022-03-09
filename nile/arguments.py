def get_arguments():
    import argparse

    parser = argparse.ArgumentParser(description='Unofficial Amazon Games client')
    sub_parsers = parser.add_subparsers(dest='command')

    auth_parser = sub_parsers.add_parser('auth', help='Authorization related things')
    auth_parser.add_argument('--login', help='Login action')

    test_parser = sub_parsers.add_parser('test')

    return parser.parse_known_args()
