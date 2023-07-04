import os
import logging
from nile.models import manifest
from nile.downloading.worker import DownloadWorker
from nile.downloading.progress import ProgressBar
import nile.utils.download as dl_utils

class Importer:
    def __init__(self, folder_path, config, library_manager, session_manager, download_manager):
        self.folder_path = folder_path
        self.config = config
        self.library_manager = library_manager
        self.session_manager = session_manager
        self.download_manager = download_manager
        self.logger = logging.getLogger("IMPORT")

    def import_game(self, game):
        if not os.path.isdir(self.folder_path):
            self.logger.error(f"{self.folder_path} is not a directory")
            return

        fuel_path = os.path.join(self.folder_path, "fuel.json")
        if not os.path.isfile(os.path.join(self.folder_path, "fuel.json")):
            self.logger.error(f"{fuel_path} is not a file")
            return

        game_manifest = self.library_manager.get_game_manifest(game['id'])

        download_url = game_manifest["downloadUrls"][0]
        self.logger.debug("Getting protobuff manifest")
        response = self.session_manager.session.get(download_url)
        r_manifest = manifest.Manifest()
        self.logger.debug("Parsing manifest data")
        r_manifest.parse(response.content)

        self.download_manager.version = game_manifest["versionId"]
        comparison = manifest.ManifestComparison.compare(
            r_manifest
        )
        patchmanifest = self.download_manager.get_patchmanifest(comparison)

        fuel_json = None
        for file in patchmanifest.files:
            self.logger.debug(f"File: {file.filename}")
            if file.filename == "fuel.json":
                fuel_json = file
                break

        if not fuel_json:
            self.logger.error("Could not find fuel.json in manifest")
            return

        readable_size = dl_utils.get_readable_size(fuel_json.download_size)
        worker = DownloadWorker(
            fuel_json,
            fuel_path,
            self.session_manager,
            None
        )
        if not worker.verify_downloaded_file(fuel_path):
            self.logger.error(
                f"{fuel_path} does not match the signature for {game['product']['title']} ({game['product']['id']})"
            )
            return

        self.logger.info(f"\tImporting {game['product']['title']} ({game['product']['id']})")
