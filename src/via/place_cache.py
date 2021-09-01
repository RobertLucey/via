# used for finding place bounds, wuld take too long to actually get
# graphs from osmnx

from typing import Mapping

import osmnx as ox

from via.utils import is_within


class PlaceCache():

    def __init__(self):
        self.data = {
            'dublin ireland': {
                'north': 53.626487,
                'south': 53.3018049,
                'east': -6.1366563,
                'west': -6.433500
            }
        }

    def get_by_bbox(self, cmp_bbox):
        for name, bbox in self.data.items():
            if is_within(cmp_bbox, bbox):
                return {
                    'name': name,
                    'bbox': bbox
                }
        return None

    def get(self, place_name: str) -> Mapping[str, float]:
        """
        Get the lat long bounds of a place

        :param place_name: An osmnx recognised place name
            (for example "Dublin, Ireland")
        :return: A dict of north, south, east, and west
            lats and lngs
        """
        place_name = place_name.lower().replace(',', '')
        try:
            return self.data[place_name]
        except KeyError:
            place_graph = ox.graph_from_place(
                place_name,
                network_type='all'
            )

            lats = []
            lngs = []
            for _, node_data in place_graph._node.items():
                lats.append(node_data['y'])
                lngs.append(node_data['x'])

            self.data[place_name] = {
                'north': max(lats),
                'south': min(lats),
                'east': max(lngs),
                'west': min(lngs)
            }
            return self.data[place_name]


place_cache = PlaceCache()
