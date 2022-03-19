from nile.models.manifest import ManifestComparison
import enum
import os


class PatchType(enum.Enum):
    NONE = 0
    FUEL_PATCH = 1


class PatchFile:
    def __init__(
        self,
        filename,
        path,
        target_hash,
        urls,
        size,
        target_hash_type="sha256",
        patch_hash=None,
        patch_hash_type=None,
        patch_type=PatchType.NONE,
        patch_offset=0,
    ):
        self.filename = filename
        self.path = path
        self.patch_hash = patch_hash
        self.patch_hash_type = patch_hash_type
        self.target_hash = target_hash
        self.target_hash_type = target_hash_type
        self.patch_type = patch_type
        self.patch_offset = patch_offset
        self.urls = urls
        self.download_size = size


class PatchManifest:
    def __init__(self):
        self.dirs = set()
        self.files = list()

    @classmethod
    def build_patch_manifest(cls, comparison: ManifestComparison, patches_list: list):
        patchmanifest = cls()

        patches = dict()
        for patch in patches_list:
            patches[patch["targetHash"]["value"]] = patch

        for old_file, new_file in comparison.updated:
            path, filename = os.path.split(new_file.path)
            patchmanifest.dirs.add(path)

            patch = patches[new_file.hash.value]

            patch_type = (
                PatchType.NONE if patch["type"] == "NONE" else PatchType.FUEL_PATCH
            )

            patchmanifest.files.append(
                PatchFile(
                    filename=filename,
                    path=path,
                    urls=patch["downloadUrls"],
                    size=patch["size"],
                    target_hash=new_file.hash.value,
                    target_hash_type=new_file.hash.algorithm.lower(),
                    patch_hash=patch["patchHash"]["value"],
                    patch_hash_type=patch["patchHash"]["algorithm"].lower(),
                    patch_type=patch_type,
                )
            )

        for new_file in comparison.new:
            path, filename = os.path.split(new_file.path)
            patchmanifest.dirs.add(path)

            patch = patches[new_file.hash.value]
            patchmanifest.files.append(
                PatchFile(
                    filename=filename,
                    path=path,
                    urls=patch["downloadUrls"],
                    size=patch["size"],
                    target_hash=new_file.hash.value,
                    target_hash_type=new_file.hash.algorithm.lower(),
                )
            )

        return patchmanifest
