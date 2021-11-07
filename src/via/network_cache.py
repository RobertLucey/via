import datetime
import logging
import os
import pickle
import threading

import fast_json
import osmnx as ox
from networkx.classes.multidigraph import MultiDiGraph

from via import settings
from via.constants import NETWORK_CACHE_DIR
from via import logger
from via.utils import (
    is_within,
    area_from_coords,
    get_graph_id,
    get_size
)
from via.place_cache import place_cache


class SingleNetworkCache():

    def __init__(self, network_type: str, fn=None):
        self.fn = fn
        self.network_type = network_type
        self.loaded = False
        self.networks_loaded = False
        self.data = {}
        self.networks = {}
        self.last_save_len = -1
        self.last_accessed = datetime.datetime.utcnow()

    @staticmethod
    def from_file(cache_type: str, filepath: str, load: bool = True, fn: str = None):
        cache = SingleNetworkCache(
            network_type=cache_type,
            fn=os.path.basename(filepath)
        )

        if load:
            cache.load()

        return cache

    def get_by_id(self, graph_id):
        if graph_id not in self.data:
            return None
        self.load_networks(network_id=graph_id)
        return {
            **self.data[graph_id],
            'network': self.networks[graph_id]
        }

    def get_at_point(self, gps_point):
        self.last_accessed = datetime.datetime.utcnow()

        self.load()

        point_bbox = {
            'north': gps_point.lat,
            'south': gps_point.lat,
            'east': gps_point.lng,
            'west': gps_point.lng
        }
        candidates = []
        for k, net in self.data.items():
            if is_within(point_bbox, net['bbox']):
                candidates.append(k)
                break

        if not len(candidates):
            return None

        self.load_networks(network_id=candidates[0])
        # FIXME: return the smallest network
        return self.networks[candidates[0]]

    def load_networks(self, network_id=None):
        if self.networks_loaded:
            return

        if network_id in self.networks:
            return

        os.makedirs(
            os.path.join(self.dir, 'networks'),
            exist_ok=True
        )
        network_files = os.listdir(os.path.join(self.dir, 'networks'))

        for network_filename in network_files:
            if os.path.splitext(network_filename)[0] in self.data.keys():
                network_filepath = os.path.join(self.dir, 'networks', network_filename)
                graph_id = os.path.splitext(os.path.basename(network_filepath))[0]
                if graph_id in self.networks:
                    # already loaded from a specific network_id previously
                    continue
                if network_id is not None:
                    if graph_id != network_id:
                        continue
                with open(network_filepath, 'rb') as network_file:
                    self.networks[graph_id] = pickle.load(network_file)

        if network_id is None:
            # It's only fully loaded when no network specified
            self.networks_loaded = True

    def get(self, journey) -> MultiDiGraph:
        self.last_accessed = datetime.datetime.utcnow()

        self.load()

        # if not poly and we find within a bbox we should be able to do that
        # truncate_graph_polygon. Don't need to save that poly graph if we
        # want to optimize for storage. Can see how it does anyways

        if self.network_type != 'poly':
            candidates = []
            for k, net in self.data.items():
                if is_within(journey.bbox, net['bbox']):
                    candidates.append((k, net))

            if candidates != []:
                logger.debug(f'{journey.gps_hash}: Using a larger network rather than generating')
                selection = sorted(
                    candidates,
                    key=lambda x: area_from_coords(x[1]['bbox'])
                )[0]

                self.load_networks(network_id=selection[0])

                return self.networks[selection[0]]

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

                self.data[get_graph_id(network)] = {
                    'gps_hash': journey.gps_hash,
                    'bbox': {
                        'north': bbox['north'],
                        'south': bbox['south'],
                        'east': bbox['east'],
                        'west': bbox['west'],
                    }
                }
                self.networks[get_graph_id(network)] = network
                self.save()
                return network

        for net_id, net in self.data.items():
            if journey.gps_hash == net['gps_hash']:
                self.load_networks(network_id=net_id)
                return self.networks[net_id]

        return None

    def set(self, journey, network: MultiDiGraph, skip_save=False):
        self.last_accessed = datetime.datetime.utcnow()

        self.load()

        self.data[get_graph_id(network)] = {
            'gps_hash': journey.gps_hash,
            'bbox': journey.bbox
        }

        # need to set networks to loaded or it may be overridden on a load
        self.load_networks()
        self.networks[get_graph_id(network)] = network

        if not skip_save:
            self.save()

    def save(self):
        if any([
            not os.path.exists(self.fp),
            len(self.data) > self.last_save_len and self.last_save_len >= 0
        ]):
            logger.debug(f'Saving cache {self.fp}')

            os.makedirs(
                os.path.join(self.dir, 'networks'),
                exist_ok=True
            )

            for k, net in self.networks.items():
                network_filepath = os.path.join(self.dir, 'networks', f'{k}.pickle')
                if not os.path.exists(network_filepath):
                    with open(network_filepath, 'wb') as network_file:
                        pickle.dump(net, network_file)

            with open(self.fp, 'wb') as network_file:
                pickle.dump(self.data, network_file)

    def load(self):
        if self.loaded:
            return

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
        logger.debug('Size of network cache: %sMB', get_size(self.data) / (1000 ** 2))

    def unload(self):
        self.networks = {}
        self.networks_loaded = False

    @property
    def dir(self) -> str:
        return os.path.join(NETWORK_CACHE_DIR, settings.VERSION, self.network_type)

    @property
    def fp(self) -> str:
        return os.path.join(self.dir, f'{self.fn}')

    @property
    def since_last_accessed(self):
        return (datetime.datetime.utcnow() - self.last_accessed).total_seconds()


class GroupedNetworkCaches():

    def __init__(self, *args, **kwargs):
        assert kwargs.get('cache_type', None) is not None
        self.loaded = False
        self.data = {}
        self.last_save_len = -1
        self.cache_type = kwargs['cache_type']
        self.child_class = SingleNetworkCache
        self.lock = threading.RLock()

        # set up references
        self.refs = {}
        os.makedirs(self.dir, exist_ok=True)
        if not os.path.exists(self.refs_path):
            with open(self.refs_path, 'w') as refs_file:
                refs_file.write(fast_json.dumps({}))
        with open(self.refs_path, 'r') as refs_file:
            self.refs = fast_json.loads(refs_file.read())

        if settings.CLEAN_MEMORY:
            self.memory_cleaner()

    def get_by_id(self, graph_id):
        self.load()
        self.lock.acquire()
        for obj in self.data.values():
            graph = obj.get_by_id(graph_id)
            if graph is not None:
                self.lock.release()
                return graph

        self.lock.release()

    def get_at_point(self, gps_point):
        self.load()
        network_at_point = None
        self.lock.acquire()
        for v in self.data.values():
            p = v.get_at_point(gps_point)
            if p:
                network_at_point = p
        self.lock.release()
        return network_at_point

    def get(self, obj):
        self.load()

        # if journey also do gps_hash
        from via.models.journey import Journey
        from via.models.journeys import Journeys
        if isinstance(obj, (Journey, Journeys)):
            self.lock.acquire()
            for k, v in self.data.items():
                result = v.get(obj)
                if result is not None:
                    self.lock.release()
                    return result
            self.lock.release()
        else:
            self.lock.acquire()
            if obj.gps_hash in self.refs and self.refs[obj.gps_hash] in self.data:
                self.lock.release()
                return self.data[self.refs[obj.gps_hash]].get(obj)
            self.lock.release()
        return None

    def set(self, k, v, skip_save=False):
        x = round(
            min(
                [d['x'] for d in dict(v.nodes(data=True)).values()]
            ),
            2
        )
        y = round(
            min(
                [d['y'] for d in dict(v.nodes(data=True)).values()]
            ),
            2
        )
        fn = '%s_%s' % (x, y)
        self.lock.acquire()
        if fn not in self.data:
            self.data[fn] = self.child_class(network_type=self.cache_type, fn=fn)
        self.data[fn].set(k, v)
        len_refs = len(self.refs)

        # k is collisions, so needs to be serializable
        self.refs[k.gps_hash] = fn

        if len_refs < len(self.refs):
            if not skip_save:
                self.data[fn].save()
                self.save_refs()

        self.lock.release()

    def save_refs(self):
        with open(self.refs_path, 'w') as refs_file:
            refs_file.write(fast_json.dumps(self.refs))

    def load(self):
        """
        Load all the caches of this type, note that this does not load
        data, it loads only references so that things can be lazily loaded
        """
        if self.loaded:
            return

        logger.debug('loading %s', self.cache_type)

        try:
            for c in self.caches:
                self.data[c.fn] = c
        except:
            self.data = {}

        self.loaded = True

    def memory_cleaner(self):
        """
        Clean up memory from caches that haven't been used in a while
        """
        logger.debug('Cleaning memory: %s', self.cache_type)

        if logger.level <= logging.DEBUG:
            # since get_size is a little slow, don't want to waste time if
            # we're not going to log about it
            try:
                initial_memory = get_size(self)
            except:
                initial_memory = -1

        # TODO: locking
        self.lock.acquire()
        for v in self.data.values():
            if v.since_last_accessed > 60:
                v.unload()
        self.lock.release()

        if logger.level <= logging.DEBUG:
            try:
                post_memory = get_size(self)
            except:
                post_memory = -1
            logger.debug(
                'Cleaned memory, reduced %s by %s%% (%s -> %s)',
                self.cache_type,
                ((float(post_memory) - initial_memory) / initial_memory) * 100,
                initial_memory,
                post_memory
            )

        cleaner = threading.Timer(
            60 * 2,
            self.memory_cleaner
        )
        cleaner.daemon = True
        cleaner.start()

    @property
    def caches(self):
        """
        Get all the caches within the directory of this cache type
        """

        return [
            self.child_class.from_file(
                cache_type=self.cache_type,
                filepath=os.path.join(self.dir, f),
                load=False
            ) for f in os.listdir(self.dir) if f not in {'refs.json', 'networks'}
        ]

    @property
    def dir(self) -> str:
        return os.path.join(NETWORK_CACHE_DIR, settings.VERSION, self.cache_type)

    @property
    def refs_path(self) -> str:
        """
        Get the reference file path for this type of cache
        """
        return os.path.join(self.dir, 'refs.json')


class NetworkCache():

    def __init__(self):
        self.network_caches = {}
        self.loaded = False

    def get_at_point(self, key, gps_point):
        if key not in self.network_caches:
            self.network_caches[key] = GroupedNetworkCaches(cache_type=key)
        return self.network_caches[key].get_at_point(gps_point)

    def get_by_id(self, graph_id):
        for cache in self.network_caches.values():
            network = cache.get_by_id(graph_id)
            if network is not None:
                return network['network']

    def get(self, key: str, journey) -> MultiDiGraph:
        self.load()
        if key not in self.network_caches:
            self.network_caches[key] = GroupedNetworkCaches(cache_type=key)
        return self.network_caches[key].get(journey)

    def set(
        self,
        key: str,
        journey,
        network: MultiDiGraph,
        skip_save=False
    ):
        if key not in self.network_caches:
            self.network_caches[key] = GroupedNetworkCaches(cache_type=key)
        self.network_caches[key].set(journey, network, skip_save=skip_save)

    def load(self, network_type=None):
        if self.loaded:
            return

        if network_type is not None:
            self.network_caches[network_type] = GroupedNetworkCaches(
                cache_type=network_type
            )
        else:
            networks_dir = os.path.join(NETWORK_CACHE_DIR, settings.VERSION)
            os.makedirs(networks_dir, exist_ok=True)
            for net_type in os.listdir(networks_dir):
                self.network_caches[net_type] = GroupedNetworkCaches(
                    cache_type=net_type
                )
                self.network_caches[net_type].load()

        self.loaded = True

    def save(self):
        for k, v in self.network_caches.items():
            v.save()


network_cache = NetworkCache()
