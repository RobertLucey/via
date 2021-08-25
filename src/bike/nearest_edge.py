import os
import osmnx as ox

import fast_json

from bike.constants import EDGE_CACHE_DIR


class NearestEdgeCache():
    # TODO: split these in a grid of lat / lng 0.5 by the first gps of the upper right or something. Not very important as files are small
    # TODO: just store uuids as string so no silly casting

    def __init__(self):
        self.loaded = False
        self.data = {}
        self.last_save_len = -1

    def get(self, graph, frames, return_dist=False):
        """

        :param graph:
        :param frames: list of frames to get nearest edges of
        :kwarg return_dist: to return the distance alongside the edge id
        :rtype: list or list of tuples
        :return: list of of edge ids or tuple of edge_id and distance
        """

        if not self.loaded:
            self.load()

        frame_ids_to_get = [
            str(frame.gps_hash) for frame in frames if self.data.get(str(frame.gps_hash), None) is None
        ]

        id_frame_map = {str(f.gps_hash): f for f in frames}

        requested_frame_edge_map = {
            str(f.gps_hash): self.data.get(str(f.gps_hash), None) for f in frames
        }

        if frame_ids_to_get != []:
            results = ox.distance.nearest_edges(
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

            for frame_id, edge_data in frame_id_result_map.items():
                edge_data = list(edge_data)
                edge_data[0] = [int(i) for i in edge_data[0]]
                edge_data[1] = float(edge_data[1])
                self.data[frame_id] = edge_data

        requested_frame_edge_map = {
            str(f.gps_hash): self.data.get(str(f.gps_hash), None) for f in frames
        }

        if return_dist:
            return requested_frame_edge_map.values()
        return [v[0] for v in requested_frame_edge_map.values()]

    def save(self):
        if any([
            not os.path.exists(self.fp),
            len(self.data) > self.last_save_len and self.last_save_len >= 0
        ]):

            with open(self.fp, 'w') as f:
                f.write(fast_json.dumps(self.data))
        self.last_save_len = len(self.data)

    def load(self):
        if not os.path.exists(self.fp):
            os.makedirs(
                os.path.dirname(self.fp),
                exist_ok=True
            )
            self.save()
        with open(self.fp, 'r') as f:
            self.data = fast_json.loads(f.read())
        self.loaded = True
        self.last_save_len = len(self.data)

    @property
    def fp(self):
        # TODO: split by lat lng regions
        return os.path.join(EDGE_CACHE_DIR, 'cache.json')


nearest_edge = NearestEdgeCache()