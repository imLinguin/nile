from urllib.parse import urlencode, urlparse, parse_qs
import nile.constants as constants
from gui import webview
import logging
import hashlib
import json
import time
import secrets
import base64
import uuid


class AuthenticationManager:
    def __init__(self, session, conifg_manager):
        self.logger = logging.getLogger("AUTH_MANAGER")
        self.challenge = ""
        self.verifier = bytes()
        self.device_id = ""
        self.serial = None
        self.session_manager = session
        self.config = conifg_manager

    def generate_code_verifier(self) -> bytes:
        self.logger.debug("Generating code_verifier")
        code_verifier = secrets.token_bytes(32)

        code_verifier = base64.urlsafe_b64encode(code_verifier).rstrip(b"=")
        self.verifier = code_verifier
        return code_verifier

    def generate_challange(self, code_verifier: bytes) -> bytes:
        self.logger.debug("Generating challange")
        hash = hashlib.sha256(code_verifier)
        return base64.urlsafe_b64encode(hash.digest()).rstrip(b"=")

    def generate_device_serial(self) -> str:
        self.logger.debug("Generating serial")
        serial = uuid.uuid1().hex.upper()
        self.serial = serial
        return serial

    def generate_client_id(self, serial) -> str:
        self.logger.debug("Generating client_id")
        serialEx = f"{serial}#A2UMVHOX7UP4V7"
        clientId = serialEx.encode("ascii")
        clientIdHex = clientId.hex()
        self.client_id = clientIdHex
        return clientIdHex

    def get_auth_url(self, client_id: str, challenge: bytes):
        base_url = "https://amazon.com/ap/signin?"

        arguments = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.mode": "checkid_setup",
            "openid.oa2.scope": "device_auth_access",
            "openid.ns.oa2": "http://www.amazon.com/ap/ext/oauth/2",
            "openid.oa2.response_type": "code",
            "openid.oa2.code_challenge_method": "S256",
            "openid.oa2.client_id": f"device:{client_id}",
            "language": "en_US",
            "marketPlaceId": constants.MARKETPLACEID,
            "openid.return_to": "https://www.amazon.com",
            "openid.pape.max_auth_age": 0,
            "openid.assoc_handle": "amzn_sonic_games_launcher",
            "pageId": "amzn_sonic_games_launcher",
            "openid.oa2.code_challenge": challenge,
        }
        return base_url + urlencode(arguments)

    def register_device(self, code):
        self.logger.info(f"Registerring a device. ID: {self.client_id}")
        data = {
            "auth_data": {
                "authorization_code": code,
                "client_domain": "DeviceLegacy",
                "client_id": self.client_id,
                "code_algorithm": "SHA-256",
                "code_verifier": self.verifier.decode("utf-8"),
                "use_global_authentication": False,
            },
            "registration_data": {
                "app_name": "AGSLauncher for Windows",
                "app_version": "1.0.0",
                "device_model": "Windows",
                "device_name": None,
                "device_serial": self.serial,
                "device_type": "A2UMVHOX7UP4V7",
                "domain": "Device",
                "os_version": "10.0.19044.0",
            },
            "requested_extensions": ["customer_info", "device_info"],
            "requested_token_type": ["bearer", "mac_dms"],
            "user_context_map": {},
        }
        response = self.session_manager.session.post(
            f"{constants.AMAZON_API}/auth/register", json=data
        )
        if not response.ok:
            self.logger.error("Failed to register a device")
            print(response.content)
            return

        res_json = response.json()
        self.logger.info("Succesfully registered a device")
        if self.logger.level > logging.DEBUG:
            print(res_json)
        config_data = res_json["response"]["success"]
        config_data["NILE"] = {"token_obtain_time": time.time()}

        self.config.write("user", config_data)

        self.logger.info("Written data to the config")

    def refresh_token(self):
        url = f"{constants.AMAZON_API}/auth/token"
        self.logger.info("Refreshing token")
        user_conf_content = self.config.get("user")
        refresh_token = user_conf_content["tokens"]["bearer"]["refresh_token"]
        request_data = {
            "source_token": refresh_token,
            "source_token_type": "refresh_token",
            "requested_token_type": "access_token",
            "app_name": "AGSLauncher for Windows",
            "app_version": "1.0.0",
        }
        response = self.session_manager.session.post(url, json=request_data)

        if not response.ok:
            self.logger.error("Failed to refresh the token")
            return None

        res_json = response.json()

        user_conf_content = self.config.get("user")
        user_conf_content["tokens"]["bearer"]["access_token"] = res_json["access_token"]
        user_conf_content["tokens"]["bearer"]["expires_in"] = res_json["expires_in"]
        user_conf_content["NILE"]["token_obtain_time"] = time.time()
        self.config.write("user", user_conf_content)

    def is_token_expired(self):
        token_obtain_time, expires_in = self.config.get(
            "user", ["NILE//token_obtain_time", "tokens//bearer//expires_in"]
        )
        return time.time() > token_obtain_time + int(expires_in)

    def is_logged_in(self) -> bool:
        tokens = self.config.get("user", "tokens")
        return bool(tokens)

    def login(self):
        code_verifier = self.generate_code_verifier()
        challenge = self.generate_challange(code_verifier)

        serial = self.generate_device_serial()
        client_id = self.generate_client_id(serial)

        url = self.get_auth_url(client_id, challenge)
        self.loginWebView = webview.LoginWindow(url)
        self.logger.info("Spawning login window")
        self.loginWebView.show(self.handle_page_load)

    def handle_page_load(self):
        page_url = self.loginWebView.get_url()
        if page_url.find("openid.oa2.authorization_code") > 0:
            self.logger.info("Got authorization code")
            self.loginWebView.stop()

            # Parse auth code
            parsed = urlparse(page_url)
            query = parse_qs(parsed.query)
            code = query["openid.oa2.authorization_code"][0]
            self.register_device(code)
