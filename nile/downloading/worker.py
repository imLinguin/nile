import os
import shutil
from nile.utils.download import calculate_checksum, get_hashing_function
from nile.models.patcher import Patcher


class DownloadWorker:
    def __init__(self, file_data, path, session_manager, report_progress, cancelled):
        self.data = file_data
        self.path = path
        self.session = session_manager.session
        self.report_progress = report_progress
        self.cancelled = cancelled

        self.retried = False

    def execute(self):
        file_path = os.path.join(
            self.path, self.data.path.replace("\\", os.sep), self.data.filename
        )
        if os.path.exists(file_path):
            if self.verify_downloaded_file(file_path):
                return
        if self.cancelled.is_set():
            return
        
        self.get_file(file_path)
        
        if self.cancelled.is_set():
            return

        if not self.verify_downloaded_file(file_path):
            print(f"Checksum error for {file_path}")
            if not self.retried:
                self.retried = True
                return self.execute()

    def verify_downloaded_file(self, path) -> bool:
        return self.data.target_hash == calculate_checksum(
            get_hashing_function(self.data.target_hash_type), path
        )

    def get_file(self, path):
        if os.path.exists(path + ".patch"):
            os.remove(path + ".patch")

        with open(path + ".patch", "ab") as f:
            response = self.session.get(
                self.data.urls[0], stream=True, allow_redirects=True
            )
            total = response.headers.get("Content-Length")
            if total is None:
                f.write(response.content)
            else:
                total = int(total)
                for data in response.iter_content(
                    chunk_size=max(int(total / 1000), 1024 * 1024)
                ):
                    if self.cancelled.is_set():
                        response.close()
                        return
                    f.write(data)
                    self.report_progress(len(data))
            f.close()

        if self.data.patch_hash:
            patch_sum = calculate_checksum(
                get_hashing_function(self.data.patch_hash_type), path + ".patch"
            )
            if self.data.patch_hash != patch_sum:
                return self.get_file(path)
            # Patch the file here
            patcher = Patcher(
                open(path, "rb"), open(path + ".patch", "rb"), open(path + ".new", "wb")
            )

            patcher.run()

            if (
                calculate_checksum(
                    get_hashing_function(self.data.target_hash_type), path + ".new"
                )
                == self.data.target_hash
            ):
                shutil.move(path + ".new", path)
        else:
            shutil.move(path + ".patch", path)
