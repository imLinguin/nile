import os
import logging
from nile.models import manifest
from nile.utils.config import ConfigType


class Uninstaller:
    def __init__(self, config_manager, arguments):
        self.config = config_manager
        self.arguments = arguments
        self.manifest = None
        self.logger = logging.getLogger("UNINSTALL")

    def uninstall(self):
        game_id = self.arguments.id
        installed_games = self.config.get("installed")

        installed_info = None
        for i, game in enumerate(installed_games):
            if game["id"] == game_id:
                installed_info = game
                installed_games.pop(i)
                break
        if not installed_info:
            self.logger.error("Game isn't installed")
            return
        # Load manifest
        self.manifest = self.load_installed_manifest(game_id)

        for f in self.manifest.packages[0].files:
            # Manifest can contain both kind of slash as a separator on the same entry
            filepath = os.path.join(installed_info["path"], f.path.replace("\\", os.sep).replace("/", os.sep))
            try:
                os.remove(filepath)
            except FileNotFoundError:
                self.logger.warning(f'Missing file "{filepath}" - skipping')

        # Remove empty directories under the installation directory
        for dirpath, dirnames, filenames in os.walk(installed_info["path"], topdown=False):
            for dirname in dirnames:
                full_path = os.path.join(dirpath, dirname)
                if not os.listdir(full_path):
                    os.rmdir(full_path)

        # Remove installation directory if it's empty
        if os.path.isdir(installed_info["path"]) and not os.listdir(installed_info["path"]):
            os.rmdir(installed_info["path"])

        self.config.write("installed", installed_games)
        self.config.remove(f"manifests/{game_id}", cfg_type=ConfigType.RAW)
        self.logger.info("Game removed successfully")

    def load_installed_manifest(self, game_id):
        old_manifest_pb = self.config.get(f"manifests/{game_id}", cfg_type=ConfigType.RAW)
        old_manifest = None
        if old_manifest_pb:
            old_manifest = manifest.Manifest()
            old_manifest.parse(old_manifest_pb)
        return old_manifest
