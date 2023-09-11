import pickle
from typing import Any, Dict

import ujson
from cachetools.func import ttl_cache

import networkx as nx

from mappymatch.maps.nx.nx_map import NxMap
from mappymatch.utils.crs import CRS
import shapely.wkt as wkt

from via.db import db
from via.settings import NXMAP_FILENAME_PREFIX, MAX_CACHE_SIZE

DEFAULT_CRS_KEY = "crs"
DEFAULT_GEOMETRY_KEY = "geometry"

# from_dict and to_dict are taken from the master version from mappymap. Once they update should be able to remove them


@classmethod
def from_dict(cls, d: Dict[str, Any]) -> NxMap:  # pragma: nocover
    """
    Build a NxMap instance from a dictionary
    """
    geom_key = d["graph"].get("geometry_key", DEFAULT_GEOMETRY_KEY)

    for link in d["links"]:
        geom_wkt = link[geom_key]
        link[geom_key] = wkt.loads(geom_wkt)

    crs_key = d["graph"].get("crs_key", DEFAULT_CRS_KEY)
    crs = CRS.from_wkt(d["graph"][crs_key])
    d["graph"][crs_key] = crs

    g = nx.readwrite.json_graph.node_link_graph(d)

    return NxMap(g)


def to_dict(self) -> Dict[str, Any]:  # pragma: nocover
    """
    Convert the map to a dictionary
    """
    graph_dict = nx.readwrite.json_graph.node_link_data(self.g)

    # convert geometries to well know text
    for link in graph_dict["links"]:
        geom = link[self._geom_key]
        link[self._geom_key] = geom.wkt

    # convert crs to well known text
    crs_key = graph_dict["graph"].get("crs_key", DEFAULT_CRS_KEY)
    graph_dict["graph"][crs_key] = self.crs.to_wkt()

    return graph_dict


class NXMapCache:
    @staticmethod
    def get_filename(key):
        return f"{NXMAP_FILENAME_PREFIX}_{key}"

    @ttl_cache(maxsize=MAX_CACHE_SIZE, ttl=60 * 60)
    def get_from_gridfs(self, key):
        return ujson.loads(
            db.gridfs.find_one({"filename": self.get_filename(key)}).read()
        )

    def get(self, key: Any):
        if db.gridfs.find_one({"filename": self.get_filename(key)}):
            try:
                NxMap.from_dict = from_dict
            except:
                return None
            else:
                return NxMap.from_dict(self.get_from_gridfs(key))

        return None

    def set(self, key: Any, value: Any):
        if self.get(key):
            return None

        db.gridfs.put(
            ujson.dumps(to_dict(value)).encode("utf8"), filename=self.get_filename(key)
        )


nxmap_cache = NXMapCache()
