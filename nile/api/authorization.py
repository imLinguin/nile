from urllib.parse import urlencode
import nile.constants as constants
from gui import webview
import logging
import hashlib
import secrets
import base64
import uuid


class AuthenticationManager:
    def __init__(self):
        self.logger = logging.getLogger("AUTH_MANAGER")
        self.challenge = ""
        self.verifier = ""
        self.device_id = ""

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

    def generate_device_id(self) -> str:
        self.device_id = uuid.uuid4().hex.upper()
        return self.device_id

    def get_auth_url(self, deviceID: str, challenge: bytes):
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
            "openid.oa2.client_id": f"device:{deviceID}",
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
        data = {
            "auth_data": {
                "authorization_code": code,
                "client_domain": "DeviceLegacy",
                "client_id": self.device_id,
                "code_algorithm": "SHA-256",
                "code_verifier": self.verifier,
                "use_global_authentication": false,
            },
            "registration_data": {
                "app_name": "AGSLauncher for Windows",
                "app_version": "1.0.0",
                "device_model": "Windows",
                "device_name": null,
                "device_serial": self.device_id,
                "device_type": "A2UMVHOX7UP4V7",
                "domain": "Device",
                "os_version": "10.0.19044.0",
            },
            "requested_extensions": ["customer_info", "device_info"],
            "requested_token_type": ["bearer", "mac_dms"],
            "user_context_map": {},
        }

    def login(self):
        code_verifier = self.generate_code_verifier()
        challenge = self.generate_challange(code_verifier)

        url = self.get_auth_url(self.generate_device_id(), challenge)
        self.loginWebView = webview.LoginWindow(url)

        self.loginWebView.show(self.handle_page_load)

    def handle_page_load(self):
        page_url = self.loginWebView.get_url()
        if page_url.find("openid.oa2.authorization_code") > 0:
            self.logger.info("Got authorization code")
            self.loginWebView.stop()

            print(page_url)
