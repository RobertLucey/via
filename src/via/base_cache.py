import os
import logging
import threading
import datetime
import pickle
from typing import List, Any

import fast_json

from via import logger
from via import settings
from via.constants import CACHE_DIR
from via.settings import CLEAN_MEMORY
from via.utils import get_size


class BaseCache():

    def __init__(self, cache_type: str = None, fn: str = None):
        assert cache_type is not None
        self.loaded = False
        self.data = {}
        self.lock = threading.RLock()
        self.last_save_len = -1
        self.cache_type = cache_type
        self.fn = fn
        self.last_accessed = datetime.datetime.utcnow()

    def get(self, k: Any):
        self.load()
        self.last_accessed = datetime.datetime.utcnow()
        self.lock.acquire()
        data = self.data.get(k, None)
        self.lock.release()
        return data

    def set(self, k, v, skip_save=False):
        self.load()
        self.lock.acquire()
        self.data[k] = v
        self.lock.release()
        if not skip_save:
            self.save()
        self.last_accessed = datetime.datetime.utcnow()

    def create_dirs(self):
        if not os.path.exists(self.fp):
            logger.debug(f'Creating cache dir: {self.fp}')
            os.makedirs(
                os.path.dirname(self.fp),
                exist_ok=True
            )

    def save(self):
        self.lock.acquire()
        if len(self.data) <= self.last_save_len:
            self.lock.release()
            return
        logger.info(f'Saving cache {self.fp}')
        self.create_dirs()
        with open(self.fp, 'wb') as f:
            pickle.dump(self.data, f)
        self.last_save_len = len(self.data)
        self.lock.release()

    def load(self):
        if self.loaded:
            return

        logger.info(f'Loading cache {self.fp}')
        if not os.path.exists(self.fp):
            self.create_dirs()
            self.save()

        self.lock.acquire()
        with open(self.fp, 'rb') as f:
            self.data = pickle.load(f)

        self.loaded = True
        self.last_save_len = len(self.data)

        if logger.level <= logging.DEBUG:
            logger.debug(
                'Size of %s cache: %sMB',
                self.fp,
                get_size(self.data) / (1000 ** 2)
            )
        self.lock.acquire()

    def unload(self):
        self.lock.acquire()
        self.data = {}
        self.lock.release()
        self.loaded = False

    @staticmethod
    def from_file(cache_type: str, filepath: str, load: bool = True, fn: str = None):
        cache = BaseCache(
            cache_type=cache_type,
            fn=os.path.basename(filepath)
        )

        if load:
            cache.load()

        return cache

    @property
    def dir(self) -> str:
        return os.path.join(CACHE_DIR, self.cache_type, settings.VERSION)

    @property
    def fp(self) -> str:
        return os.path.join(self.dir, f'{self.fn}')

    @property
    def since_last_accessed(self):
        return (datetime.datetime.utcnow() - self.last_accessed).total_seconds()


class BaseCaches():

    def __init__(self, *args, **kwargs):
        assert kwargs.get('cache_type', None) is not None
        self.loaded = False
        self.data = {}
        self.lock = threading.RLock()
        self.last_save_len = -1
        self.cache_type = kwargs['cache_type']
        self.child_class = kwargs.get('child_class', BaseCache)

        # set up references
        self.refs = {}
        os.makedirs(self.dir, exist_ok=True)
        if not os.path.exists(self.refs_path):
            with open(self.refs_path, 'w') as refs_file:
                refs_file.write(fast_json.dumps({}))
        with open(self.refs_path, 'r') as refs_file:
            self.refs = fast_json.loads(refs_file.read())

        if CLEAN_MEMORY:
            self.memory_cleaner()

    def get(self, k: Any):
        self.load()

        self.lock.acquire(timeout=1)
        data = None
        if k in self.refs and self.refs[k] in self.data:
            data = self.data[self.refs[k]].get(k)
        self.lock.release()
        return data

    def get_fn(self, obj):
        raise NotImplementedError()

    def set(self, k: Any, v: Any, skip_save: bool = False):
        fn = self.get_fn(v)

        self.lock.acquire(timeout=1)
        if fn not in self.data:
            self.data[fn] = self.child_class(fn=fn)
        self.data[fn].set(k, v)
        len_refs = len(self.refs)
        self.refs[k] = fn
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

        self.lock.acquire(timeout=1)
        try:
            for c in self.caches:
                self.data[c.fn] = c
        except:
            self.data = {}
        self.lock.release()

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

        self.lock.acquire(timeout=1)
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
    def dir(self) -> str:
        return os.path.join(CACHE_DIR, self.cache_type, settings.VERSION)

    @property
    def caches(self) -> List[BaseCache]:
        """
        Get all the caches within the directory of this cache type
        """
        return [
            self.child_class.from_file(
                self.cache_type,
                os.path.join(self.dir, f),
                load=False
            ) for f in os.listdir(self.dir)
        ]

    @property
    def refs_path(self) -> str:
        """
        Get the reference file path for this type of cache
        """
        return os.path.join(self.dir, 'refs.json')
