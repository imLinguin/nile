import os
import logging
from nile.models import manifest, hash_pairs, patch_manifest


def uninstall(game_id, config):
    logger = logging.getLogger("UNINSTALLER")
    installed_games = config.get("installed")
    installed_info = None
    for i, game in enumerate(installed_games):
        if game["id"] == game_id:
            installed_info = game
            installed_games.pop(i)
    if not installed_info:
        logger.error("Game isn't installed")
        return
    # Load manifest
    manifest = load_installed_manifest(game_id, config)

    files = manifest.packages[0].files
    for f in files:
        os.remove(os.path.join(installed_info["path"], f.path.replace("\\", "/")))

    config.write("installed", installed_games)
    config.remove(f"manifests/{game_id}")
    logger.info("Game removed successfully")


def load_installed_manifest(game_id, config):
    old_manifest_pb = config.get(f"manifests/{game_id}", raw=True)
    old_manifest = None
    if old_manifest_pb:
        old_manifest = manifest.Manifest()
        old_manifest.parse(old_manifest_pb)
    return old_manifest
