import os
import threading
import datetime

from via import logger
from via.settings import VERSION
from via.constants import COLLISION_EDGE_CACHE_DIR
from via.utils import (
    read_json,
    write_json
)


class CollisionEdgeCache():
    # TODO: split these in a grid of lat / lng 0.5 by the first gps of the upper right or something. Not very important as files are small
    # TODO: just store uuids as string so no silly casting

    def __init__(self):
        self.loaded = False
        self.data = {}
        self.last_save_len = -1
        self.last_saved_time = datetime.datetime.utcnow()
        self.saver()

    def saver(self):
        """
        Saves every now and then if necessary, there were too many happening
        each time an edge was set and was annoying
        """
        self.load()

        if all([
            self.last_save_len < len(self.data),
            (datetime.datetime.utcnow() - self.last_saved_time).total_seconds() > 5
        ]):
            self.save()

        saver = threading.Timer(
            10,
            self.saver
        )
        saver.daemon = True
        saver.start()

    def save(self):
        logger.debug('Saving cache %s', self.filepath)
        write_json(self.filepath, self.data)
        self.last_save_len = len(self.data)
        self.last_saved_time = datetime.datetime.utcnow()

    def get(self, edge_id):
        # this returns the gps_hashes
        self.load()
        return self.data.get(str(edge_id), [])

    def set(self, edge_id, collision_id):
        if edge_id in self.data:
            self.data[str(edge_id)].append(str(collision_id))
        else:
            self.data[str(edge_id)] = [str(collision_id)]

    def load(self):
        if self.loaded:
            return

        logger.debug('Loading cache %s', self.filepath)
        if not os.path.exists(self.filepath):
            os.makedirs(
                os.path.dirname(self.filepath),
                exist_ok=True
            )
            self.save()
        self.data = read_json(self.filepath)
        self.loaded = True
        self.last_save_len = len(self.data)

    @property
    def filepath(self):
        # TODO: split by lat lng regions
        return os.path.join(COLLISION_EDGE_CACHE_DIR, VERSION, 'cache.json')


collision_edge_cache = CollisionEdgeCache()
