import os
import sys
from platformdirs import user_config_dir

MARKETPLACEID = "ATVPDKIKX0DER"
AMAZON_API = "https://api.amazon.com"
AMAZON_SDS = "https://sds.amazon.com"
AMAZON_GAMING_GRAPHQL = "https://gaming.amazon.com/graphql"

FUZZY_SEARCH_RATIO = 0.7

DEFAULT_INSTALL_PATH = os.path.join(
    os.getenv("HOME", os.path.expanduser("~")), "Games", "nile"
)

CONFIG_PATH = os.path.join(
    os.getenv("XDG_CONFIG_HOME", user_config_dir(roaming=True)), "nile"
)

ILLEGAL_FNAME_CHARS = ["?", ":", '"', "*", "<", ">", "|"]

SHCOLORS = {
    "clear": "\033[0m",
    "red": "\033[31m",
    "green": "\033[1;32m",
    "blue": "\033[34m",
}
SUPPORTS_COLORS = sys.platform != "win32"
