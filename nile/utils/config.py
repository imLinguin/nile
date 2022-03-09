import logging


class Config:
    def __init__(self):
        self.logger = logging.getLogger("CONFIG")

    # def get(store:str, key:str):