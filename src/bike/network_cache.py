import os
import pickle

from bike.settings import VERSION
from bike.constants import NETWORK_CACHE_DIR


class SingleNetworkCache():
    # TODO: split these in a grid of lat / lng 0.5 by the first gps of the upper right or something

    def __init__(self, network_type):
        self.network_type = network_type
        self.loaded = False
        self.data = {}
        self.last_save_len = -1

    def get(self, network_hash):
        if not self.loaded:
            self.load()

        return self.data.get(network_hash, None)

    def set(self, network_hash, network):
        self.data[network_hash] = network
        self.save()

    def save(self):
        if any([
            not os.path.exists(self.fp),
            len(self.data) > self.last_save_len and self.last_save_len >= 0
        ]):
            with open(self.fp, 'wb') as f:
                pickle.dump(self.data, f)

    def load(self):
        if not os.path.exists(self.fp):
            os.makedirs(
                os.path.dirname(self.fp),
                exist_ok=True
            )
            self.save()

        with open(self.fp, 'rb') as f:
            self.data = pickle.load(f)
        self.loaded = True
        self.last_save_len = len(self.data)

    @property
    def dir(self):
        return os.path.join(NETWORK_CACHE_DIR, VERSION)

    @property
    def fp(self):
        return os.path.join(self.dir, f'{self.network_type}_cache.pickle')


class NetworkCache():

    def __init__(self):
        self.network_caches = {}

    def get(self, key, network_hash):
        if key not in self.network_caches:
            self.network_caches[key] = SingleNetworkCache(key)
        return self.network_caches[key].get(network_hash)

    def set(self, key, network_hash, network):
        if key not in self.network_caches:
            self.network_caches[key] = SingleNetworkCache(key)
        self.network_caches[key].set(network_hash, network)


network_cache = NetworkCache()
