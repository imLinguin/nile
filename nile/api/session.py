import requests
from multiprocessing import cpu_count


class APIHandler:
    def __init__(self):
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_maxsize=cpu_count(), max_retries=5)
        self.session.mount("https://", adapter)
        self.session.headers.update({"User-Agent": "AGSLauncher/1.0.0"})
