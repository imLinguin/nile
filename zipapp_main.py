import os
import sys
import zipfile
import filelock
import zlib

# We assume zipapp is created on Linux only

cache_path = os.environ.get('XDG_CACHE_HOME')
if cache_path:
    cache_path = os.path.join(cache_path, 'nile')
else:
    cache_path = os.path.expanduser('~/.cache/nile')

vendored_packages_path = os.path.join(cache_path, 'vendored')
vendored_packages_lock = os.path.join(cache_path, 'vendored.lock')

# At the moment only Cryptodome AES uses a native module
# Thus we only handle the extraction of that

packages = ["Crypto"]

if zipfile.is_zipfile(os.path.dirname(__file__)):
    with filelock.FileLock(vendored_packages_lock) as lock:
        with zipfile.ZipFile(os.path.dirname(__file__)) as zf:
            for package in packages:
                # First see if we need to do the extraction
                should_extract = True
                init_path = os.path.join(vendored_packages_path, package + '/__init__.py')
                if os.path.exists(init_path):
                    file = zf.getinfo(package + '/__init__.py')
                    with open(init_path, 'rb') as init:
                        should_extract = zlib.crc32(init.read()) != file.CRC

                # We extract only dependencies that require native code
                if should_extract:
                    for file in zf.infolist():
                        if file.filename.startswith(package):
                            extracted = zf.extract(file.filename, vendored_packages_path)
                            os.chmod(extracted, file.external_attr >> 16)
    sys.path.insert(0, vendored_packages_path)

# Run CLI
import nile.cli
nile.cli.main()