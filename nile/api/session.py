import requests

class APIHandler():
    def __init__(self, config_manager):
        self.config = config_manager
        self.session = requests.Session()
        self.update_session()

    def update_session(self):
        new_headers = {
            'User-Agent': 'AGSLauncher/1.0.0'
        }
        self.session.headers.update(new_headers)