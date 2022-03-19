import os
import shutil
from nile.constants import ILLEGAL_FNAME_CHARS


def get_readable_size(size):
    power = 2**10
    n = 0
    power_labels = {0: "", 1: "K", 2: "M", 3: "G"}
    while size > power:
        size /= power
        n += 1
    return size, power_labels[n] + "B"


def save_directory_name(title: str) -> str:
    output = title
    for char in ILLEGAL_FNAME_CHARS:
        output = output.replace(char, "")
    return output


def check_available_space(size, path) -> bool:
    if not os.path.exists(path):
        os.makedirs(path)

    _, _, available = shutil.disk_usage(path)

    return size < available


def calculate_checksum(hashing_function, path):
    with open(path, 'rb') as f:
        calculate = function()
        while True:
            chunk = f.read(16 * 1024)
            if not chunk:
                break
            calculate.update(chunk)

        return calculate.hexdigest()