class ProgressState:
    def __init__(self, total_size):
        self.downloaded_size = 0
        self.total_size = total_size

    def update(self, size_downloaded):
        self.downloaded_size += size_downloaded

    def calc(self):
        return self.downloaded_size / self.total_size
