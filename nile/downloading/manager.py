import logging
import os
import enum
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from threading import Event
from time import sleep
import nile.utils.download as dl_utils
from nile.models import manifest, hash_pairs, patch_manifest
from nile.models.progress import ProgressState
from nile.downloading.worker import DownloadWorker

from gi.repository import GLib
# from nile.models.progressbar import ProgressBar
from nile import constants


class DownloadManagerEvent(enum.Enum):
    INSTALL_BEGAN = 1
    INSTALL_COMPLETED = 2
    INSTALL_ERROR = 3
    INSTALL_PROGRESS = 4


class DownloadManager:
    def __init__(self, config_manager, library_manager, session_manager):
        self.config = config_manager
        self.library_manager = library_manager
        self.session = session_manager
        self.logger = logging.getLogger("DOWNLOAD")
        self.logger.debug("Initialized Download Manager")

        self.manifest = None
        self.old_manifest = None
        self.threads = []
        self.listeners = []
        self.installing = False, None
        self.cancelled = None

    def listen(self, callback):
        # Callbacks should accept 2 parameters, TYPE and MESSAGE
        self.listeners.append(callback)

    def remove_listener(self, callback):
        self.listenrs.remove(callback)

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

    def init_download(
        self,
        game,
        force_verifying=False,
        base_install_path="",
        install_path="",
        path_folder_name_only=False,
    ):
        self.game = game
        self.cancelled = False
        game_location = base_install_path
        if not base_install_path:
            game_location = install_path
        else:
            game_location = os.path.join(
                base_install_path,
                dl_utils.safe_directory_name(self.game["product"]["title"]),
            )
        if not base_install_path and not install_path:
            game_location = os.path.join(
                constants.DEFAULT_INSTALL_PATH,
                dl_utils.safe_directory_name(self.game["product"]["title"]),
            )
        if path_folder_name_only:
            game_location = dl_utils.safe_directory_name(self.game["product"]["title"])
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
            return None, None
        self.logger.debug(f"Number of packages: {len(self.manifest.packages)}")

        comparison = manifest.ManifestComparison.compare(
            self.manifest, self.old_manifest
        )

        return comparison, game_location
        # self.progressbar = ProgressBar(total_size)

    def download_from_patchmanifest(
        self, game_location, patchmanifest, force_verifying=False
    ):
        self.cancelled = False
        total_size = sum(f.download_size for f in patchmanifest.files)
        progress_state = ProgressState(total_size)
        self.install_path = game_location
        for directory in patchmanifest.dirs:
            os.makedirs(
                os.path.join(game_location, directory.replace("\\", os.sep)),
                exist_ok=True,
            )
        with ThreadPoolExecutor(max_workers=cpu_count()) as thpool:
            self.cancelled = Event()
            self.installing = True, self.game["product"]["id"]
            for callback in self.listeners:
                callback(DownloadManagerEvent.INSTALL_BEGAN, True)
            for f in patchmanifest.files:
                worker = DownloadWorker(
                    f, game_location, self.session, progress_state.update, self.cancelled
                )
                # worker.execute()
                self.threads.append(thpool.submit(worker.execute))

            while True:
                is_done = False
                for thread in self.threads:
                    is_done = thread.done()
                    if is_done == False:
                        break
                if is_done:
                    break

                if self.cancelled.is_set():
                    thpool.shutdown(wait=False,cancel_futures=True)
                # self.progressbar.print()
                status_data = progress_state.calc()
                for listener in self.listeners:
                    GLib.idle_add(listener,DownloadManagerEvent.INSTALL_PROGRESS, status_data)
                

                sleep(0.2)

        if self.cancelled.is_set():
            for callback in self.listeners:
                callback(DownloadManagerEvent.INSTALL_COMPLETED, False)
        elif not force_verifying:
            self.finish()

        
        self.installing = False, None
        self.cancelled = None
    def cancel(self):
        self.cancelled.set()

    def finish(self):
        # Save manifest to the file

        self.config.write(
            f"manifests/{self.game['product']['id']}", self.protobuff_manifest, raw=True
        )

        # Save data to installed.json file
        installed_array = self.config.get("installed")

        if not installed_array:
            installed_array = list()

        installed_game_data = dict(
            id=self.game["product"]["id"], version=self.version, path=self.install_path
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
        for callback in self.listeners:
            callback(DownloadManagerEvent.INSTALL_COMPLETED, True)
        self.__cleanup()

    def __cleanup(self):
        self.protobuff_manifest = None
        self.manifest = None
        self.old_manifest = None
        self.thpool = None
        self.game = None
        self.threads = []
