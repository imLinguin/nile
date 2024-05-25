import urllib.parse
import os
from nile.models import manifest
from nile.constants import CONFIG_PATH
from nile.models.hash_pairs import PatchBuilder

class SelfUpdateHandler:
    def __init__(self, session, library):
        self.session_manager = session
        self.library_manager = library

    def get_manifest(self):
        response = self.session_manager.session.get("https://gaming.amazon.com/api/distribution/v2/public/download/channel/87d38116-4cbf-4af0-a371-a5b498975346")
        data = response.json()
        return data

    def get_sdk(self):
        if os.path.exists(os.path.join(CONFIG_PATH, 'SDK')):
            return
        ag_manifest = self.get_manifest()
        url = urllib.parse.urlparse(ag_manifest['downloadUrl'])
        url = url._replace(path=url.path + '/manifest.proto')

        url = urllib.parse.urlunparse(url)

        response = self.session_manager.session.get(url)
        raw_manifest = response.content

        launcher_manifest = manifest.Manifest()
        launcher_manifest.parse(raw_manifest)

        for file in launcher_manifest.packages[0].files:
            if 'FuelSDK_x64.dll' in file.path or 'AmazonGamesSDK_' in file.path:
                url = urllib.parse.urlparse(ag_manifest['downloadUrl'])
                url = url._replace(path=url.path + '/files/' + file.hash.value)
                url = urllib.parse.urlunparse(url)

                response = self.session_manager.session.get(url, stream=True)
            
                filepath = os.path.join(CONFIG_PATH, 'SDK', file.path.replace('\\', os.sep).replace('/', os.sep))
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'wb') as filehandle:
                    for chunk in response.iter_content(1024 * 1024):
                        filehandle.write(chunk)
        
