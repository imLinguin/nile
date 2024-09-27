import requests
from multiprocessing import cpu_count

class APIHandler():
    def __init__(self, config_manager):
        self.config = config_manager
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_maxsize=12)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            'User-Agent': 'AGSLauncher/1.0.0'
        })
