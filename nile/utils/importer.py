import os
import logging
import urllib.parse
from nile.models import manifest
from nile.downloading.worker import DownloadWorker
from nile.utils.config import ConfigType
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor, as_completed

class Importer:
    def __init__(self, game, folder_path, config, library_manager, session_manager, download_manager):
        self.game = game
        self.folder_path = folder_path
        self.config = config
        self.library_manager = library_manager
        self.session_manager = session_manager
        self.download_manager = download_manager
        self.logger = logging.getLogger("IMPORT")

        self.threads = []

    def get_manifest(self):
        return self.download_manager.get_manifest()

    def stop_threads(self):
        self.thpool.shutdown(wait=False, cancel_futures=True)

    def verify_integrity(self):
        manifest_data = self.get_manifest()
        self.thpool = ThreadPoolExecutor(max_workers=cpu_count())

        comparison = manifest.ManifestComparison.compare(
            manifest_data, None 
        )

        for file in comparison.new:
            local_path = os.path.join(self.folder_path, file.path.replace("\\", os.sep))
            self.logger.debug(f"Verifying: {local_path}")
            if not os.path.isfile(local_path):
                self.stop_threads()
                self.logger.error(f"{local_path} is missing or corrupted")
                return False

            url = urllib.parse.urlparse(self.download_manager.downloadUrl)
            url = url._replace(path=url.path + '/files/' + file.hash.value)
            url = urllib.parse.urlunparse(url)
            worker = DownloadWorker(
                url,
                file,
                local_path,
                self.session_manager,
                None
            )
            self.threads.append(self.thpool.submit(worker.verify_downloaded_file, local_path))

        for thread in as_completed(self.threads):
            if thread.cancelled() or not thread.result():
                self.stop_threads()
                return False

        return True

    def import_game(self):
        if not os.path.isdir(self.folder_path):
            self.logger.error(f"{self.folder_path} is not a directory")
            return

        self.logger.info(f"\tVerifying local files")
        if not self.verify_integrity():
            self.logger.error(
                f"There are missing or corrupted files for {self.game['product'].get('title')}. Failed import."
            )
            return

        self.logger.info(f"\tImporting {self.game['product'].get('title')}")
        self.finish()
        self.logger.info(f"Imported {self.game['product'].get('title')}")


    def finish(self):
        # Save manifest to the file

        self.config.write(
            f"manifests/{self.game['product']['id']}", self.download_manager.protobuff_manifest, cfg_type=ConfigType.RAW
        )

        # Save data to installed.json file
        installed_array = self.config.get("installed")

        if not installed_array:
            installed_array = list()

        installed_game_data = dict(
            id=self.game["product"]["id"], version=self.download_manager.version, path=self.folder_path
        )

        installed_array.append(installed_game_data)

        self.config.write("installed", installed_array)
