import json
import pickle
from typing import Any, Dict

from cachetools.func import ttl_cache

from gridfs import GridFS

import networkx as nx

from mappymatch.maps.nx.nx_map import NxMap
from mappymatch.utils.crs import CRS
import shapely.wkt as wkt

from via.utils import get_mongo_interface
from via.settings import NXMAP_FILENAME_PREFIX

DEFAULT_CRS_KEY = "crs"
DEFAULT_GEOMETRY_KEY = "geometry"


@classmethod
def from_dict(cls, d: Dict[str, Any]) -> NxMap:
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


def to_dict(self) -> Dict[str, Any]:
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
    def __init__(self):
        self.mongo_interface = get_mongo_interface()
        self.grid = GridFS(self.mongo_interface)

    @staticmethod
    def get_filename(key):
        return f"{NXMAP_FILENAME_PREFIX}_{key}"

    @ttl_cache(maxsize=10, ttl=60 * 60)
    def get_from_gridfs(self, key):
        return json.loads(
            self.grid.find_one({"filename": self.get_filename(key)}).read()
        )

    def get(self, key: Any):
        if self.grid.find_one({"filename": self.get_filename(key)}):
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

        self.grid.put(
            json.dumps(to_dict(value)).encode("utf8"), filename=self.get_filename(key)
        )


nxmap_cache = NXMapCache()
