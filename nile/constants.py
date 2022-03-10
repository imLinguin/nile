import os
import sys

MARKETPLACEID = "ATVPDKIKX0DER"
AMAZON_API = "https://api.amazon.com"


CONFIG_PATH = os.path.join(
    os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "nile"
)
if sys.platform == "win32":
    os.path.join(os.getenv("APPDATA"), "nile")
