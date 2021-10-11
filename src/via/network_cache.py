import os
import pickle
import hashlib

import osmnx as ox
from networkx.classes.multidigraph import MultiDiGraph

from via.settings import VERSION
from via.constants import NETWORK_CACHE_DIR
from via import logger
from via.utils import (
    is_within,
    area_from_coords
)
from via.place_cache import place_cache


class SingleNetworkCache():
    # TODO: split these in a grid of lat / lng 0.5 by the first gps of
    # the upper right or something

    def __init__(self, network_type: str):
        self.network_type = network_type
        self.loaded = False
        self.data = []
        self.last_save_len = -1

    def get(self, journey, poly=True) -> MultiDiGraph:
        if not self.loaded:
            self.load()

        # if not poly and we find within a bbox we should be able to do that
        # truncate_graph_polygon. Don't need to save that poly graph if we
        # want to optimize for storage. Can see how it does anyways

        if not poly:
            candidates = []
            for net in self.data:
                if is_within(journey.bbox, net['bbox']):
                    candidates.append(net)

            if candidates != []:
                # TODO: say how much bigger it is or something
                logger.debug(f'{journey.gps_hash}: Using a larger network rather than generating')
                selection = sorted(
                    candidates,
                    key=lambda x: area_from_coords(x['bbox'])
                )
                return selection[0]['network']

            # see if we can use a place
            if place_cache.get_by_bbox(journey.bbox) is not None:
                bbox = place_cache.get_by_bbox(journey.bbox)['bbox']

                network = ox.graph_from_bbox(
                    bbox['north'],
                    bbox['south'],
                    bbox['east'],
                    bbox['west'],
                    network_type='all',
                    simplify=True
                )

                self.data.append(
                    {
                        'hash': hashlib.md5(str(bbox).encode()).hexdigest(),
                        'bbox': {
                            'north': bbox['north'],
                            'south': bbox['south'],
                            'east': bbox['east'],
                            'west': bbox['west'],
                        },
                        'network': network
                    }
                )
                self.save()
                return network

        for net in self.data:
            if journey.gps_hash == net['hash']:
                return net['network']

        return None

    def set(self, journey, network: MultiDiGraph):
        if not self.loaded:
            self.load()

        self.data.append({
            'hash': journey.gps_hash,
            'bbox': journey.bbox,
            'network': network
        })
        self.save()

    def save(self):
        if any([
            not os.path.exists(self.fp),
            len(self.data) > self.last_save_len and self.last_save_len >= 0
        ]):
            logger.debug(f'Saving cache {self.fp}')
            with open(self.fp, 'wb') as network_file:
                pickle.dump(self.data, network_file)

    def load(self):
        logger.debug(f'Loading cache {self.fp}')
        if not os.path.exists(self.fp):
            os.makedirs(
                os.path.dirname(self.fp),
                exist_ok=True
            )
            self.save()

        with open(self.fp, 'rb') as network_file:
            self.data = pickle.load(network_file)
        self.loaded = True
        self.last_save_len = len(self.data)

    @property
    def dir(self) -> str:
        return os.path.join(NETWORK_CACHE_DIR, VERSION, self.network_type)

    @property
    def fp(self) -> str:
        return os.path.join(self.dir, 'cache.pickle')


class NetworkCache():

    def __init__(self):
        self.network_caches = {}

    def get(self, key: str, journey, poly=True) -> MultiDiGraph:
        if key not in self.network_caches:
            self.network_caches[key] = SingleNetworkCache(key)
        return self.network_caches[key].get(journey, poly=poly)

    def set(self, key: str, journey, network: MultiDiGraph):
        if key not in self.network_caches:
            self.network_caches[key] = SingleNetworkCache(key)
        self.network_caches[key].set(journey, network)

    def load(self, network_type=None):
        if network_type is not None:
            self.network_caches[network_type] = SingleNetworkCache(network_type)
        else:
            networks_dir = os.path.join(NETWORK_CACHE_DIR, VERSION)
            for net_type in os.listdir(networks_dir):
                self.network_caches[net_type] = SingleNetworkCache(net_type)
                self.network_caches[net_type].load()


network_cache = NetworkCache()
