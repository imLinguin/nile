from nile import constants
from nile.proto import sds_proto2_pb2
import logging
import uuid
import json
import time
import hashlib

from nile.utils.config import ConfigType


class Library:
    def __init__(self, config_manager, session_manager):
        self.config = config_manager
        self.session_manager = session_manager
        self.logger = logging.getLogger("LIBRARY")

    def request_sds(self, target, token, body):
        headers = {
            "X-Amz-Target": target,
            "x-amzn-token": token,
            "UserAgent": "com.amazon.agslauncher.win/3.0.9202.1",
            "Content-Type": "application/json",
            "Content-Encoding": "amz-1.0",
        }
        response = self.session_manager.session.post(
            f"{constants.AMAZON_SDS}/amazon/",
            headers=headers,
            json=body,
        )

        return response

    def request_distribution(self, target, token, body):
        headers = {
            "X-Amz-Target": target,
            "x-amzn-token": token,
            "UserAgent": "com.amazon.agslauncher.win/3.0.9202.1",
            "Content-Type": "application/json",
            "Content-Encoding": "amz-1.0",
        }
        url = (constants.AMAZON_GAMING_DISTRIBUTION_ENTITLEMENTS 
               if target.endswith(".GetEntitlements") 
               else constants.AMAZON_GAMING_DISTRIBUTION)
        response = self.session_manager.session.post(
            url,
            headers=headers,
            json=body,
        )

        return response


    def _get_sync_request_data(self, serial, next_token=None, sync_point=None):
        request_data = {
            "Operation": "GetEntitlements",
            "clientId": "Sonic",
            "syncPoint": sync_point,
            "nextToken": next_token,
            "maxResults": 50,
            "productIdFilter": None,
            "keyId": "d5dc8b8b-86c8-4fc4-ae93-18c0def5314d",
            "hardwareHash": hashlib.sha256(serial.encode()).hexdigest().upper(),
        }

        return request_data

    def sync(self, force=False):
        self.logger.info("Synchronizing library")

        sync_point = self.config.get("syncpoint", cfg_type=ConfigType.RAW)

        if sync_point is not None:
            if not sync_point:
                sync_point = None
            else:
                sync_point = float(sync_point.decode())
                self.logger.debug(f"Using sync_point {sync_point}")

        if force:
            self.logger.warning("Forcefully refreshing the library")
            sync_point = None

        token, serial = self.config.get(
            "user",
            [
                "tokens//bearer//access_token",
                "extensions//device_info//device_serial_number",
            ],
        )
        games = list()
        if sync_point:
            cached_games = self.config.get('library')
            if cached_games:
                games.extend(cached_games)
            if len(games) == 0:
                sync_point = None
            else:
                # If there are games without titles refresh all metadata
                for game in games:
                    if not game['product'].get('title'):
                        sync_point = None
                        games = []
                        self.logger.warning("Found game without title locally, ignoring sync_point")
                        break

        next_token = None
        while True:
            request_data = self._get_sync_request_data(serial, next_token, sync_point)

            response = self.request_distribution(
                "com.amazon.animusdistributionservice.entitlement.AnimusEntitlementsService.GetEntitlements",
                token,
                request_data,
            )
            json_data = response.json()
            new_games = json_data["entitlements"]
            if not new_games and sync_point:
                self.logger.info("No new games found")
            games.extend(new_games)

            if not "nextToken" in json_data:
                break
            else:
                self.logger.info("Got next token in response, making next request")
                next_token = json_data["nextToken"]

            if not response.ok:
                self.logger.error("There was an error syncing library")
                self.logger.debug(response.content)
                return
        # Remove duplicates
        games_dict = dict()
        for game in games:
            if not games_dict.get(game["product"]["id"]):
                games_dict[game["product"]["id"]] = game

        self.config.write("library", list(games_dict.values()))
        self.config.write("syncpoint", str(time.time()).encode(), cfg_type=ConfigType.RAW)
        self.logger.info("Successfully synced the library")

    def get_game_manifest(self, id: str):
        token = self.config.get("user", "tokens//bearer//access_token")

        request_data = {
            "entitlementId": id,
            "Operation": "GetGameDownload",
        }

        response = self.request_distribution(
            "com.amazon.animusdistributionservice.external.AnimusDistributionService.GetGameDownload",
            token,
            request_data,
        )

        if not response.ok:
            self.logger.error("There was an error getting game manifest")
            self.logger.debug(response.content)
            return

        response_json = response.json()

        return response_json

    def get_patches(self, id, version, file_list):
        token = self.config.get("user", "tokens//bearer//access_token")

        request_data = {
            "Operation": "GetPatches",
            "versionId": version,
            "fileHashes": file_list,
            "deltaEncodings": ["FUEL_PATCH", "NONE"],
            "adgGoodId": id,
        }

        response = self.request_sds(
            "com.amazonaws.gearbox.softwaredistribution.service.model.SoftwareDistributionService.GetPatches",
            token,
            request_data,
        )

        if not response.ok:
            self.logger.error("There was an error getting patches")
            self.logger.debug(response.content)
            return

        response_json = response.json()

        return response_json["patches"]

    def get_versions(self, game_ids):
        token = self.config.get("user", "tokens//bearer//access_token")

        request_data = {"adgProductIds": game_ids, "Operation": "GetLiveVersions"}

        response = self.request_distribution(
            "com.amazon.animusdistributionservice.external.AnimusDistributionService.GetLiveVersionIds",
            token,
            request_data,
        )

        if not response.ok:
            self.logger.error("There was an error getting versions")
            self.logger.debug(response.content)
            return

        response_json = response.json()

        return response_json["adgProductIdToVersionIdMap"]

    def get_installed_game_info(self, id):
        installed_array = self.config.get("installed")
        if not installed_array:
            return dict()
        for game in installed_array:
            if game["id"] == id:
                return game

        return dict()
