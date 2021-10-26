import os
from typing import List, Any
import pickle
import json

from via import logger
from via import settings
from via.constants import CACHE_DIR
from via.utils import get_size


class BaseCache():

    def __init__(self, cache_type: str = None, fn: str = None):
        assert cache_type is not None
        self.loaded = False
        self.data = {}
        self.last_save_len = -1
        self.cache_type = cache_type
        self.fn = fn

    def get(self, k: Any):
        if not self.loaded:
            self.load()

        return self.data.get(k, None)

    def set(self, k, v, skip_save=False):
        if not self.loaded:
            self.load()
        self.data[k] = v
        if not skip_save:
            self.save()

    def create_dirs(self):
        if not os.path.exists(self.fp):
            logger.debug(f'Creating cache dir: {self.fp}')
            os.makedirs(
                os.path.dirname(self.fp),
                exist_ok=True
            )

    def save(self):
        if len(self.data) <= self.last_save_len:
            return
        logger.info(f'Saving cache {self.fp}')
        self.create_dirs()
        with open(self.fp, 'wb') as f:
            pickle.dump(self.data, f)
        self.last_save_len = len(self.data)

    def load(self):
        logger.info(f'Loading cache {self.fp}')
        if not os.path.exists(self.fp):
            self.create_dirs()
            self.save()

        with open(self.fp, 'rb') as f:
            self.data = pickle.load(f)
        self.loaded = True
        self.last_save_len = len(self.data)
        logger.debug(
            'Size of %s cache: %sMB',
            self.fp,
            get_size(self.data) / (1000 ** 2)
        )

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


class BaseCaches():

    def __init__(self, *args, **kwargs):
        assert kwargs.get('cache_type', None) is not None
        self.loaded = False
        self.data = {}
        self.last_save_len = -1
        self.cache_type = kwargs['cache_type']
        self.child_class = kwargs.get('child_class', BaseCache)

        # set up references
        self.refs = {}
        os.makedirs(self.dir, exist_ok=True)
        if not os.path.exists(self.refs_path):
            with open(self.refs_path, 'w') as refs_file:
                refs_file.write(json.dumps({}))
        with open(self.refs_path, 'r') as refs_file:
            self.refs = json.loads(refs_file.read())

    def get(self, k: Any):
        self.load()
        if k in self.refs and self.refs[k] in self.data:
            return self.data[self.refs[k]].get(k)
        return None

    def set(self, k: Any, v: Any, skip_save: bool = False):
        fn = '%s_%s.pickle' % (
            round(min(v[0].geometry.x), 1),
            round(min(v[0].geometry.y), 1)
        )
        if fn not in self.data:
            self.data[fn] = self.child_class(fn=fn)
        self.data[fn].set(k, v)
        len_refs = len(self.refs)
        self.refs[k] = fn
        if len_refs < len(self.refs):
            if not skip_save:
                self.data[fn].save()
                self.save_refs()

    def save_refs(self):
        with open(self.refs_path, 'w') as refs_file:
            refs_file.write(json.dumps(self.refs))

    def load(self):
        """
        Load all the caches of this type, note that this does not load
        data, it loads only references so that things can be lazily loaded
        """
        if self.loaded:
            return

        try:
            for c in self.caches:
                self.data[c.fn] = c
        except:
            self.data = {}

        self.loaded = True

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
