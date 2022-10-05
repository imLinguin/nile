from asyncore import read
import hashlib
import logging
import math
import os
import requests
import yaml
import tarfile
from nile.constants import *

class WineManager:
    def __init__(self, config_manager):
        self.logger = logging.getLogger("WINEMGMT")
        self.config = config_manager

    

    def get_repository_index(self):
        self.logger.info("Getting components index")
        components_index_path = os.path.join(CACHE_PATH, 'components.yml')

        etag = None
        if os.path.exists(components_index_path) and os.path.exists(components_index_path+'.etag'):
            self.logger.info("Trying to reuse cached index")
            etag = open(components_index_path+'.etag','r').read()

            self.logger.info("Doing request to check for updates")

            response = requests.get("https://repo.usebottles.com/components/index.yml", headers={"If-None-Match": etag})

            if response.status_code == 200:
                self.logger.info("Index changed, writing content")
                open(components_index_path,'wb').write(response.content)
                open(components_index_path+'.etag', 'w').write(response.headers.get("etag"))

            elif response.status_code == 304:
                self.logger.info("Index is up to date")


        else:
            self.logger.info("Downloading components index")
            response = requests.get("https://repo.usebottles.com/components/index.yml")

            if response.ok:
                self.logger.info("Writing content")
                open(components_index_path,'wb').write(response.content)
                open(components_index_path+'.etag', 'w').write(response.headers.get("etag"))


    def get_component_manifest(self, name, category, subcategory=None):

        url_path = category + "/" + (subcategory if subcategory else "") + "/" + name

        response = requests.get("https://repo.usebottles.com/components/"+url_path+".yml")

        if response.ok:
            return yaml.safe_load(response.content)
        return None


    def download_component(self, manifest, data, submit_percentage, finished_callback):
        component_path = os.path.join(DATA_PATH, "components", data["Category"], data.get("Sub-category") if data.get("Sub-category") else "")
        self.logger.info(f"Creating path: {component_path}")
        os.makedirs(component_path, exist_ok=True)

        file_data = manifest["File"][0]

        file_name = os.path.join(component_path, file_data["file_name"])
        rename_path = os.path.join(component_path, file_data["rename"])
        checksum = file_data["file_checksum"]

        self.logger.info("Downloading component")
        response = requests.get(file_data['url'], stream=True, allow_redirects=True)
        
        downloaded = 0
        total_size = int(response.headers.get("Content-Length"))

        with open(file_name, 'wb') as handle:
            for data in response.iter_content(16*16*1024):
                downloaded += len(data)
                handle.write(data)
                
                submit_percentage(math.floor((downloaded / total_size)*100))
            handle.close()

        with open(file_name, 'rb') as handle:
            f_sum = hashlib.md5()
            while True:
                chunk = handle.read(1024*1024)
                if not chunk:
                    break
                f_sum.update(chunk)
            
            handle.close()

            if f_sum.hexdigest() == checksum:
                self.logger.info("Checksums matching")
            else:
                self.logger.info("Sums don't match")
                os.remove(file_name)
                finished_callback(False)
                return

        os.rename(file_name, rename_path)

        self.logger.info("Extracting")
        archive_handle = tarfile.open(rename_path) 
        root_dir = archive_handle.getnames()[0] 
        archive_handle.extractall(component_path)
        archive_handle.close()


        if root_dir.endswith("x86_64"):
            root_dir = os.path.join(component_path, root_dir)
            os.rename(
                root_dir,
                root_dir[:-7]
            )

        if manifest.get("Post"):
            for action in manifest["Post"]:
                if action["action"] == "rename":
                    src_path = os.path.join(component_path, action["source"])
                    dst_path = os.path.join(component_path, action["dest"])
                    self.logger.info(f"Renaming {src_path} -> {dst_path}")
                    os.rename(src_path, dst_path)
                else:
                    self.logger.warning(f"Unknown action {action['action']}")


        self.logger.info("Removing tar.gz archive")
        os.remove(rename_path)
        finished_callback(True)
        self.logger.info(f"Downloaded component {data['name']}")

    def get_existing_components_list(self, index):
        existing_components = list()
        for component in index.keys():
            category = index[component]["Category"]
            sub_category = index[component].get("Sub-category")
            
            if not sub_category:
                component_path = os.path.join(DATA_PATH,"components", category, component)
                if os.path.exists(component_path):
                    existing_components.append(component)
            else:
                component_path = os.path.join(DATA_PATH, "components", category, sub_category, component)
                if os.path.exists(component_path):
                    existing_components.append(component)

        
        return existing_components

    def read_components(self):
        handle = open(os.path.join(CACHE_PATH, 'components.yml'), 'r')
        parsed = yaml.safe_load(handle)      
        handle.close()

        return parsed 

