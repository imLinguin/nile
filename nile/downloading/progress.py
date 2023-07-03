import threading
import logging
from time import sleep, time


class ProgressBar(threading.Thread):
    def __init__(self, max_val, total_readable_size):
        self.logger = logging.getLogger("PROGRESS")
        self.downloaded = 0
        self.total = max_val
        self.started_at = time()
        self.last_update = time()
        self.total_readable_size = total_readable_size
        self.completed = False

        self.written_total = 0

        self.written_since_last_update = 0
        self.downloaded_since_last_update = 0

        super().__init__(target=self.print_progressbar)

    def print_progressbar(self):
        while True:
            if self.completed:
                break
            percentage = (self.downloaded / self.total) * 100
            running_time = time() - self.started_at
            runtime_h = int(running_time // 3600)
            runtime_m = int((running_time % 3600) // 60)
            runtime_s = int((running_time % 3600) % 60)

            time_since_last_update = time() - self.last_update
            if time_since_last_update == 0:
                time_since_last_update = 1

            # average_speed = self.downloaded / running_time

            if percentage > 0:
                estimated_time = (100 * running_time) / percentage - running_time
            else:
                estimated_time = 0

            estimated_h = int(estimated_time // 3600)
            estimated_time = estimated_time % 3600
            estimated_m = int(estimated_time // 60)
            estimated_s = int(estimated_time % 60)

            write_speed = self.written_since_last_update / time_since_last_update
            download_speed = self.downloaded_since_last_update / time_since_last_update

            self.written_total += self.written_since_last_update
            self.downloaded += self.downloaded_since_last_update

            self.read_since_last_update = self.written_since_last_update = 0
            self.decompressed_since_last_update = self.downloaded_since_last_update = 0

            self.logger.info(
                f"= Progress: {percentage:.02f} {self.downloaded}/{self.total}, "
                + f"Running for: {runtime_h:02d}:{runtime_m:02d}:{runtime_s:02d}, "
                + f"ETA: {estimated_h:02d}:{estimated_m:02d}:{estimated_s:02d}"
            )

            self.logger.info(
                f"= Downloaded: {self.downloaded / 1024 / 1024:.02f} MiB, "
                f"Written: {self.written_total / 1024 / 1024:.02f} MiB"
            )

            self.logger.info(
                f" + Download\t- {download_speed / 1024 / 1024:.02f} MiB/s"
            )

            self.logger.info(
                f" + Disk\t- {write_speed / 1024 / 1024:.02f} MiB/s"
            )

            self.last_update = time()
            sleep(1)

    def update_downloaded_size(self, addition):
        self.downloaded += addition

    def update_download_speed(self, addition):
        self.downloaded_since_last_update += addition

    def update_bytes_written(self, addition):
        self.written_since_last_update += addition