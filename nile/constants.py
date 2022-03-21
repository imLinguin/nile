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
if sys.platform == "win32":
    CONFIG_PATH = os.path.join(os.getenv("APPDATA"), "nile")
    DEFAULT_INSTALL_PATH = os.path.join(os.getenv("USERPROFILE"), "nile")


ILLEGAL_FNAME_CHARS = ["?",":","\"","*","<",">","|"]