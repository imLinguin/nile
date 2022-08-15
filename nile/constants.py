import os
import sys

MARKETPLACEID = "ATVPDKIKX0DER"
AMAZON_API = "https://api.amazon.com"
AMAZON_SDS = "https://sds.amazon.com"
AMAZON_GAMING_GRAPHQL = "https://gaming.amazon.com/graphql"

FUZZY_SEARCH_RATIO = 0.7

DEFAULT_INSTALL_PATH = os.path.join(
    os.getenv("HOME", os.path.expanduser("~")), "Games", "nile"
)

CONFIG_PATH = os.path.join(
    os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "nile"
)

CACHE_PATH = os.path.join(
    os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "nile"
)

if sys.platform == "win32":
    CONFIG_PATH = os.path.join(os.getenv("APPDATA"), "nile")
    DEFAULT_INSTALL_PATH = os.path.join(os.getenv("USERPROFILE"), "nile")


ILLEGAL_FNAME_CHARS = ["?", ":", '"', "*", "<", ">", "|", "/", "\\", "'"]

SHCOLORS = {
    "clear": "\033[0m",
    "red": "\033[31m",
    "green": "\033[1;32m",
    "blue": "\033[34m",
}
SUPPORTS_COLORS = sys.platform != "win32"
