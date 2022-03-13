from nile import constants
import logging
import uuid
import json
import hashlib


class Library:
    def __init__(self, config_manager, session_manager):
        self.config = config_manager
        self.session_manager = session_manager
        self.logger = logging.getLogger("LIBRARY")

    def sync(self):
        self.logger.info("Synchronizing library")

        user_data = self.config.get("user")
        request_data = {
            "Operation": "GetEntitlementsV2",
            "clientId": "Sonic",
            "syncPoint": None,
            "nextToken": None,
            "maxResults": 50,
            "productIdFilter": None,
            "keyId": "d5dc8b8b-86c8-4fc4-ae93-18c0def5314d",
            "hardwareHash": hashlib.sha256(
                user_data["extensions"]["device_info"]["device_serial_number"].encode()
            )
            .hexdigest()
            .upper(),
        }

        headers = {
            "X-Amz-Target": "com.amazonaws.gearbox.softwaredistribution.service.model.SoftwareDistributionService.GetEntitlementsV2",
            "x-amzn-token": user_data["tokens"]["bearer"]["access_token"],
            "User-Agent": "com.amazon.agslauncher.win/2.1.6485.3",
            "UserAgent": "com.amazon.agslauncher.win/2.1.6485.3",
            "Content-Type": "application/json",
            "Content-Encoding": "amz-1.0",
        }

        # print(json.dumps(request_data), json.dumps(headers))

        # return
        response = self.session_manager.session.post(
            f"{constants.AMAZON_SDS}/amazon/",
            headers=headers,
            json=request_data,
        )

        if not response.ok:
            self.logger.error("ERROR SYNCING LIBRARY")
            print(response.content)
            return

        self.config.write("library", response.json()["entitlements"])
        self.logger.info("Successfully synced the library")
