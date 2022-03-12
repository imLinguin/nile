from nile import constants
import logging
import uuid
import json


class Library:
    def __init__(self, config_manager, session_manager):
        self.conifg = config_manager
        self.session_manager = session_manager
        self.logger = logging.getLogger("LIBRARY")

    def sync(self):
        self.logger.info("Synchronizing library")

        user_data = self.conifg.get("user")
        # keyId =
        data = {
            "Operation": "GetEntitlementsV2",
            "clientId": "Sonic",
            "syncPoint": None,
            "nextToken": None,
            "maxResults": 50,
            "productIdFilter": None,
            "keyId": "d5dc8b8b-86c8-4fc4-ae93-18c0def5314",
            "hardwareHash": "11",
        }
        headers = {
            "X-Amz-Target": "com.amazonaws.gearbox.softwaredistribution.service.model.SoftwareDistributionService.GetEntitlementsV2",
            "x-amzn-token": user_data["tokens"]["bearer"]["access_token"],
            "User-Agent": "com.amazon.agslauncher.win/2.1.6485.3",
            "Content-Encoding": "amz-1.0",
            "Content-Type": "application/json",
        }


        print(json.dumps(data), json.dumps(headers))

        # return
        response = self.session_manager.session.post(
            f"{constants.AMAZON_SDS}/amazon",
            headers=headers,
            json=data,
        )
        if not response.ok:
            self.logger.error("ERROR SYNCING LIBRARY")
            print(response.content)
            return

        self.conifg.write("library", response.content)
