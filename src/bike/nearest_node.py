import osmnx as ox


class NearestNodeCache():

    def __init__(self):
        self.data = {}

    def get(self, graph, frame, return_dist=False):
        try:
            node_data = self.data[frame.uuid]
        except KeyError:
            self.data[frame.uuid] = ox.get_nearest_node(
                graph,
                (frame.gps.lat, frame.gps.lng),
                method='haversine',
                return_dist=True
            )
            node_data = self.data[frame.uuid]

        if not return_dist:
            return node_data[0]
        return node_data


nearest_node = NearestNodeCache()
