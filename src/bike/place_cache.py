# used for finding place bounds, wuld take too long to actually get
# graphs from osmnx

import osmnx as ox


class PlaceCache():

    def __init__(self):
        self.data = {
            'dublin ireland': {
                'north': 53.4095829,
                'south': 53.3018049,
                'east': -6.1366563,
                'west': -6.3867115
            }
        }

    def get(self, place_name):
        place_name = place_name.lower().replace(',', '')
        try:
            return self.data[place_name]
        except KeyError:
            place_graph = ox.graph_from_place('place_name', network_type='bike')

            lats = []
            lngs = []
            for k, v in place_graph._node.items():
                lats.append(v['y'])
                lngs.append(v['x'])

            self._data[place_name] = {
                'north': max(lats),
                'south': min(lats),
                'east': max(lngs),
                'west': min(lngs)
            }
            return self.data[place_name]


place_cache = PlaceCache()
