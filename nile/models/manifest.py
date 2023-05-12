from nile.proto import sds_proto2_pb2 as sds
import struct
import lzma

try:
    from Crypto.PublicKey import RSA
    from Crypto.Signature import PKCS1_v1_5
    from Crypto.Hash import SHA256
except ModuleNotFoundError:
    print("Module Crypto not found, trying to use newer Cryptodome")
    from Cryptodome.PublicKey import RSA
    from Cryptodome.Signature import PKCS1_v1_5
    from Cryptodome.Hash import SHA256
    pass
# Handles only V3 manifests


AMZ_RSA_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA6fSRMUi3VpTtv9P4+KvM
AcAIP4SYbTQfB1ns7vyUjsj8nrF2lGNtQTtGLnrNmM2ElZ2R7VmQtNiRtPMxToIW
Rajin0H0OyzGrHA8P6w96Mj4q1JeORCzJeVFgLOBClCCMmB+5bJBWnJcq/sEMwu9
gGynCeiYNLt7ZMVpL1GOsNjl+yLk7OMMGpMj1JWCVFfgYE9Lud1QZJllFAWhRBoT
wTctAUZTikObFUoBm+KEiCsKIcay4WOybvJwxTNBUl2GL8c+ihrT2ntLPpb9aIJE
/gXU3Ihl5oXe/0P/QN0CRu/ybXWLiGzIYqKIok4nepkdo8V3gWR55K801pOuck0B
awIDAQAB
-----END PUBLIC KEY-----"""


class Hash:
    def __init__(self, data):
        self.value = data.value.hex()
        self.raw_value = data.value
        self.algorithm = sds.HashAlgorithm.Name(data.algorithm)


class Dir:
    def __init__(self, data):
        self.path = data.path
        self.mode = data.mode


class File:
    def __init__(self, data):
        self.path = data.path
        self.mode = data.mode
        self.size = data.size
        self.created = data.created
        self.hash = Hash(data.hash)
        self.hidden = data.hidden
        self.system = data.system


class Package:
    def __init__(self, package):
        self.name = package.name
        self.files = [File(f_data) for f_data in package.files]
        self.dirs = [Dir(dir_data) for dir_data in package.dirs]


class Manifest:
    _amz_rsa_key = RSA.importKey(AMZ_RSA_KEY)

    def __init__(self):
        self.header_pb = None
        self.manifest_pb = None
        self.packages = []

    def parse(self, content):
        header = sds.ManifestHeader()
        header_size = struct.unpack(">I", content[:4])[0]

        self.header_pb = header.FromString(content[4 : 4 + header_size])
        raw_manifest = self._decompress(content[4 + header_size :])

        if not self._verify(raw_manifest):
            raise ValueError("Failed to verify manifest signature")
        self.manifest_pb = sds.Manifest().FromString(raw_manifest)
        for package in self.manifest_pb.packages:
            self.packages.append(Package(package))

    def _verify(self, manifest_content):
        if self.header_pb.signature.algorithm == sds.sha256_with_rsa:
            signer = PKCS1_v1_5.new(self._amz_rsa_key)
            digest = SHA256.new(manifest_content)
            return signer.verify(digest, self.header_pb.signature.value)
        else:
            raise ValueError("Unknown signature algorithm!")

    def _decompress(self, content):
        if self.header_pb.compression.algorithm == sds.lzma:
            return lzma.decompress(content)
        elif self.header_pb.compression.algorithm == sds.none:
            return content
        else:
            raise ValueError("Unknown compression algorithm!")


class ManifestComparison:
    def __init__(self):
        self.new = []
        self.removed = []
        self.updated = []

    @classmethod
    def compare(cls, manifest, old_manifest=None):
        comparison = cls()

        if old_manifest:
            old_files = dict()
            for f in old_manifest.packages[0].files:
                old_files[f.path] = f

            for f in manifest.packages[0].files:
                if f.path not in old_files:
                    comparison.new.append(f)
                    continue

                if f.hash.value != old_files[f.path].hash.value:
                    comparison.updated.append((old_files[f.path], f))
                # delete files that are in old_files and new manifest from this dict
                del old_files[f.path]

            # all that remains are files that were removed!
            comparison.removed = old_files.values()
        else:
            # In this case there are just new files
            comparison.new = [f for f in manifest.packages[0].files]

        return comparison
