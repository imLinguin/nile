from nile.models.manifest import ManifestComparison

class PatchBuilder():
    max_hashpairs_per_request = 1000
    def __init__(self, manifest_comparison: ManifestComparison):
        self.mc = manifest_comparison
        self.hashpairs = []

    def build_hashpairs(self):
        for old_f, new_f in self.mc.updated:
            self.hashpairs.append(dict(
                sourceHash=dict(value=old_f.hash.value,
                                algorithm=old_f.hash.algorithm.upper()),
                targetHash=dict(value=new_f.hash.value,
                                algorithm=new_f.hash.algorithm.upper())
            ))

        for f in self.mc.new:
            self.hashpairs.append(dict(
                sourceHash=None,
                targetHash=dict(value=f.hash.value,
                                algorithm=f.hash.algorithm.upper()),
            ))

    def get_next_hashes(self):
        """Iterator that yields new fileHashes for requests"""
        if not self.hashpairs:
            self.build_hashpairs()

        while self.hashpairs:
            yield self.hashpairs[:self.max_hashpairs_per_request]
            self.hashpairs = self.hashpairs[self.max_hashpairs_per_request:]