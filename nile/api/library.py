from nile import constants
from nile.proto import sds_proto2_pb2
import logging
import uuid
import json
import hashlib


class Library:
    def __init__(self, config_manager, session_manager):
        self.config = config_manager
        self.session_manager = session_manager
        self.logger = logging.getLogger("LIBRARY")

    def request_sds(self, target, token, body):
        headers = {
            "X-Amz-Target": target,
            "x-amzn-token": token,
            "User-Agent": "com.amazon.agslauncher.win/2.1.6485.3",
            "UserAgent": "com.amazon.agslauncher.win/2.1.6485.3",
            "Content-Type": "application/json",
            "Content-Encoding": "amz-1.0",
        }
        response = self.session_manager.session.post(
            f"{constants.AMAZON_SDS}/amazon/",
            headers=headers,
            json=body,
        )

        return response

    def sync(self):
        self.logger.info("Synchronizing library")

        token, serial = self.config.get(
            "user",
            [
                "tokens//bearer//access_token",
                "extensions//device_info//device_serial_number",
            ],
        )
        request_data = {
            "Operation": "GetEntitlementsV2",
            "clientId": "Sonic",
            "syncPoint": None,
            "nextToken": None,
            "maxResults": 50,
            "productIdFilter": None,
            "keyId": "d5dc8b8b-86c8-4fc4-ae93-18c0def5314d",
            "hardwareHash": hashlib.sha256(serial.encode()).hexdigest().upper(),
        }

        response = self.request_sds(
            "com.amazonaws.gearbox.softwaredistribution.service.model.SoftwareDistributionService.GetEntitlementsV2",
            token,
            request_data,
        )

        if not response.ok:
            self.logger.error("There was an error syncing library")
            self.logger.debug(response.content)
            return

        self.config.write("library", response.json()["entitlements"])
        self.logger.info("Successfully synced the library")

    def get_game_manifest(self, id: str):
        token = self.config.get("user", "tokens//bearer//access_token")

        request_data = {
            "adgGoodId": id,
            "previousVersionId": None,
            "keyId": "d5dc8b8b-86c8-4fc4-ae93-18c0def5314d",
            "Operation": "GetDownloadManifestV3",
        }

        response = self.request_sds(
            "com.amazonaws.gearbox.softwaredistribution.service.model.SoftwareDistributionService.GetDownloadManifestV3",
            token,
            request_data,
        )

        if not response.ok:
            self.logger.error("There was an error getting game manifest")
            self.logger.debug(response.content)
            return

        response_json = response.json()

        return response_json
