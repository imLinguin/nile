import logging
import os
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from time import sleep
import nile.utils.download as dl_utils
from nile.models import manifest, hash_pairs, patch_manifest
from nile.downloading.worker import DownloadWorker
# from nile.models.progressbar import ProgressBar
from nile import constants


class DownloadManager:
    def __init__(self, config_manager, library_manager, session_manager, game):
        self.config = config_manager
        self.library_manager = library_manager
        self.session = session_manager
        self.game = game
        self.logger = logging.getLogger("DOWNLOAD")
        self.logger.debug("Initialized Download Manager")

        self.manifest = None
        self.old_manifest = None
        self.threads = []

    def get_manifest(self):
        game_manifest = self.library_manager.get_game_manifest(self.game["id"])
        self.logger.debug("Got download manifest")
        self.version = game_manifest["versionId"]
        downloadUrl = game_manifest["downloadUrls"][0]
        self.logger.debug("Getting protobuff manifest")
        response = self.session.session.get(downloadUrl)
        r_manifest = manifest.Manifest()
        self.logger.debug("Parsing manifest data")
        r_manifest.parse(response.content)
        self.protobuff_manifest = response.content
        return r_manifest

    def get_patchmanifest(self, comparison: manifest.ManifestComparison):
        self.logger.info("Generating patches, this might take a second...")
        hash_pair_builder = hash_pairs.PatchBuilder(comparison)
        hash_pair_builder.build_hashpairs()
        patches = []
        for hash_pair in hash_pair_builder.get_next_hashes():
            patches.extend(
                self.library_manager.get_patches(
                    self.game["id"], self.version, hash_pair
                )
            )

        return patch_manifest.PatchManifest.build_patch_manifest(comparison, patches)

    def get_installed_version(self):
        installed_games = self.config.get("installed")
        if installed_games:
            for game in installed_games:
                if self.game["id"] == game["id"]:
                    return game["version"]
        return None

    def load_installed_manifest(self):
        old_manifest_pb = self.config.get(f"manifests/{self.game['id']}", raw=True)
        old_manifest = None
        if old_manifest_pb:
            old_manifest = manifest.Manifest()
            old_manifest.parse(old_manifest_pb)
        return old_manifest

    def download(self, force_verifying=False, base_install_path="", install_path=""):
        game_location = base_install_path
        if not base_install_path:
            game_location = install_path
        else:
            game_location = os.path.join(
                base_install_path,
                dl_utils.save_directory_name(self.game["product"]["title"]),
            )
        if not base_install_path and not install_path:
            game_location = os.path.join(
                constants.DEFAULT_INSTALL_PATH,
                dl_utils.save_directory_name(self.game["product"]["title"]),
            )
        saved_location = self.library_manager.get_installed_game_info(
            self.game["id"]
        ).get("path")
        if saved_location:
            game_location = saved_location

        self.install_path = game_location
        if not force_verifying:
            self.manifest = self.get_manifest()
            self.old_manifest = self.load_installed_manifest()
        else:
            self.logger.debug("Loading manifest from the disk")
            self.version = self.get_installed_version()
            self.manifest = self.load_installed_manifest()

        if not self.manifest:
            self.logger.error("Unable to load manifest")
            return
        self.logger.debug(f"Number of packages: {len(self.manifest.packages)}")

        comparison = manifest.ManifestComparison.compare(
            self.manifest, self.old_manifest
        )

        patchmanifest = self.get_patchmanifest(comparison)
        self.logger.debug(f"Number of files {len(patchmanifest.files)}")
        if len(patchmanifest.files) == 0:
            self.logger.info("Game is up to date")
            return
        total_size = sum(f.download_size for f in patchmanifest.files)
        readable_size = dl_utils.get_readable_size(total_size)
        self.logger.info(
            f"Download size: {round(readable_size[0],2)}{readable_size[1]}"
        )

        if not dl_utils.check_available_space(total_size, game_location):
            self.logger.error("Not enough space available")
            return

        # self.progressbar = ProgressBar(total_size)

        for directory in patchmanifest.dirs:
            os.makedirs(
                os.path.join(game_location, directory.replace("\\", os.sep)),
                exist_ok=True,
            )
        self.thpool = ThreadPoolExecutor(max_workers=cpu_count())
        for f in patchmanifest.files:
            worker = DownloadWorker(f, game_location, self.session)
            # worker.execute()
            self.threads.append(self.thpool.submit(worker.execute))

        while True:
            is_done = False
            for thread in self.threads:
                is_done = thread.done()
                if is_done == False:
                    break
            if is_done:
                break
            # self.progressbar.print()
            sleep(0.5)

        if not force_verifying:
            self.finish()

    def finish(self):
        # Save manifest to the file

        self.config.write(
            f"manifests/{self.game['id']}", self.protobuff_manifest, raw=True
        )

        # Save data to installed.json file
        installed_array = self.config.get("installed")

        if not installed_array:
            installed_array = list()

        installed_game_data = dict(
            id=self.game["id"], version=self.version, path=self.install_path
        )
        updated = False
        # Swap existing entry in case of updating etc..
        for i, game in enumerate(installed_array):
            if game["id"] == self.game["id"]:
                installed_array[i] = installed_game_data
                updated = True
                break

        if not updated:
            installed_array.append(installed_game_data)

        self.config.write("installed", installed_array)
