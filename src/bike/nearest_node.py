import osmnx as ox


class NearestNodeCache():

    def __init__(self):
        self.data = {}

    def get(self, graph, frames, return_dist=False):
        """

        :param graph:
        :param frames: list of frames to get nearest nodes of
        :kwarg return_dist: to return the distance alongside the node id
        :rtype: list or list of tuples
        :return: list of of node ids or tuple of node_id and distance
        """
        frame_ids_to_get = [
            frame.uuid for frame in frames if self.data.get(frame.uuid, None) is None
        ]

        id_frame_map = {f.uuid: f for f in frames}

        requested_frame_node_map = {
            f.uuid: self.data.get(f.uuid, None) for f in frames
        }

        if frame_ids_to_get != []:
            results = ox.distance.nearest_nodes(
                graph,
                [id_frame_map[frame_id].gps.lng for frame_id in frame_ids_to_get],
                [id_frame_map[frame_id].gps.lat for frame_id in frame_ids_to_get],
                return_dist=True
            )

            frame_id_result_map = dict(
                zip(
                    frame_ids_to_get,
                    list(
                        zip(
                            results[0],
                            results[1]
                        )
                    )
                )
            )

            for frame_id, node_data in frame_id_result_map.items():
                self.data[frame_id] = node_data

        requested_frame_node_map = {
            f.uuid: self.data.get(f.uuid, None) for f in frames
        }

        if return_dist:
            return requested_frame_node_map.values()
        return [v[0] for v in requested_frame_node_map.values()]


nearest_node = NearestNodeCache()
