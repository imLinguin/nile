import requests

class APIHandler():
    def __init__(self, config_manager):
        self.config = config_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AGSLauncher/1.0.0'
        })
