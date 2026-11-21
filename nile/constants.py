import os
import sys
import zipimport
from platformdirs import user_config_dir

MARKETPLACEID = "ATVPDKIKX0DER"
AMAZON_API = "https://api.amazon.com"
AMAZON_SDS = "https://sds.amazon.com"
AMAZON_GAMING_GRAPHQL = "https://gaming.amazon.com/graphql"
AMAZON_GAMING_DISTRIBUTION = "https://gaming.amazon.com/api/distribution/v2/public"
AMAZON_GAMING_DISTRIBUTION_ENTITLEMENTS = "https://gaming.amazon.com/api/distribution/entitlements"

FUZZY_SEARCH_RATIO = 0.7

DEFAULT_INSTALL_PATH = os.path.join(
    os.getenv("HOME", os.path.expanduser("~")), "Games", "nile"
)

# Name of the marker file that enables portable mode.
# When it sits next to the nile executable, config is kept in a "config"
# directory beside the executable instead of the user config directory
PORTABLE_MARKER = "portable"


def executable_dir() -> str | None:
    """
    Directory the running nile executable lives in.
    Returns None when running from source, since there is no bundled
    executable to look next to
    """
    if getattr(sys, "frozen", False):
        # PyInstaller build
        return os.path.dirname(os.path.abspath(sys.executable))

    loader = globals().get("__loader__")
    if isinstance(loader, zipimport.zipimporter):
        # zipapp build, the archive itself is the executable
        return os.path.dirname(os.path.abspath(loader.archive))

    return None


def portable_config_path() -> str | None:
    """
    Returns the portable config directory if the "portable" marker file
    is present next to the executable, otherwise None
    """
    exe_dir = executable_dir()
    if not exe_dir:
        return None
    if os.path.isfile(os.path.join(exe_dir, PORTABLE_MARKER)):
        return os.path.join(exe_dir, "config")
    return None


PORTABLE_CONFIG_PATH = portable_config_path()

CONFIG_PATH = PORTABLE_CONFIG_PATH or os.path.join(
    os.getenv("NILE_CONFIG_PATH", os.getenv("XDG_CONFIG_HOME", user_config_dir(roaming=True))), "nile"
)

ILLEGAL_FNAME_CHARS = [":","/","*","?","<",">","\\","|","™","\"","®"]

SHCOLORS = {
    "clear": "\033[0m",
    "red": "\033[31m",
    "green": "\033[1;32m",
    "blue": "\033[34m",
}
SUPPORTS_COLORS = sys.platform != "win32"
