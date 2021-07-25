import json
import os

import osmnx as ox
import networkx as nx

from bike import logger
from bike.utils import window
from bike.constants import (
    STAGED_DATA_DIR,
    SENT_DATA_DIR
)
from bike.settings import (
    EXCLUDE_METRES_BEGIN_AND_END,
    MINUTES_TO_CUT,
    TRANSPORT_TYPE,
    SUSPENSION,
    DELETE_ON_SEND
)
from bike.models.frame import (
    Frame,
    Frames
)
from bike.models.generic import GenericObjects


class Journey(Frames):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('child_class', Frame)
        super(Journey, self).__init__(*args, **kwargs)

        self.is_culled = kwargs.get('is_culled', False)

        self.transport_type = kwargs.get('transport_type', TRANSPORT_TYPE)
        self.suspension = kwargs.get('suspension', SUSPENSION)

    @staticmethod
    def parse(obj):
        if isinstance(obj, Journey):
            return obj
        else:
            raise NotImplementedError('Can\'t parse journey from type %s' % (type(obj)))

    @staticmethod
    def from_file(filepath: str):
        return Journey(
            **json.loads(open(filepath, 'r').read())
        )

    def get_indirect_distance(self, n_seconds=1):
        """

        :param n_seconds: use the location every n seconds as if the
                        location is calculated too frequently the distance
                        travelled could be artificially inflated
        :rtype: float
        :return: distance travelled in metres
        """
        last_frame = None
        distances = []

        for frame in self:
            if last_frame is None:
                last_frame = frame
            elif frame.time >= last_frame.time + n_seconds:
                distances.append(
                    last_frame.distance_from_point(
                        frame
                    )
                )
                last_frame = frame

        return sum(distances)

    def get_avg_speed(self, n_seconds=1):
        """

        :param n_seconds: use the location every n seconds as if the
                        location is calculated too frequently the distance
                        travelled could be artificially inflated
        :rtype: float
        :return: avg speed in metres per second
        """
        return self.get_indirect_distance(n_seconds=n_seconds) / self.duration

    def serialize(self, minimal=False):
        data = {
            'uuid': str(self.uuid),
            'data': super().serialize(),
            'transport_type': self.transport_type,
            'suspension': self.suspension,
            'is_culled': self.is_culled
        }

        if minimal is False:
            data.update(
                {
                    'direct_distance': self.direct_distance,
                    'indirect_distance': {
                        1: self.get_indirect_distance(n_seconds=1),
                        5: self.get_indirect_distance(n_seconds=5),
                        10: self.get_indirect_distance(n_seconds=10)
                    },
                    'quality': self.quality,
                    'duration': self.duration
                }
            )

        return data

    def cull_distance(self):
        """
        Remove the start and end of the journey, the start to remove
        will be until you are x metres away, the end to remove will be the
        last time you are x metres away from the destination
        """
        first_frame_away_idx = None
        last_frame_away_idx = None

        for idx, frame in enumerate(self):
            if frame.distance_from_point(self.origin) > EXCLUDE_METRES_BEGIN_AND_END:
                first_frame_away_idx = idx
                break

        for idx, frame in enumerate(reversed(self)):
            if frame.distance_from_point(self.destination) > EXCLUDE_METRES_BEGIN_AND_END:
                last_frame_away_idx = len(self) - idx
                break

        if any(
            [
                first_frame_away_idx is None,
                last_frame_away_idx is None
            ]
        ):
            raise Exception('Not a long enough journey to get any meaningful data from')

        self._data = self[first_frame_away_idx:last_frame_away_idx]

    def cull_time(self, origin_time, destination_time):
        """
        Remove the start and end of a journey, the start to remove will be
        the first x minutes, the end to remove will be the last x minutes
        """
        if MINUTES_TO_CUT != 0:
            min_time = origin_time
            max_time = destination_time

            tmp_frames = Frames()
            for frame in self:
                if any([
                    frame.time < min_time + (60 * MINUTES_TO_CUT),
                    frame.time > max_time - (60 * MINUTES_TO_CUT)
                ]):
                    continue
                tmp_frames.append(frame)

            self._data = tmp_frames

    def cull(self):

        if self.is_culled:
            logger.warning('Attempted to cull an already culled journey: %s', self.uuid)
            return

        origin_time = self.origin.time
        destination_time = self.destination.time

        orig_frame_count = len(self)

        self.cull_distance()
        self.cull_time(origin_time, destination_time)

        new_frame_count = len(self)

        self.is_culled = True

        logger.info(
            'Culled %s kept %s %% frames',
            self.uuid,
            (new_frame_count / orig_frame_count) * 100
        )

    def save(self):
        logger.info('Saving %s', self.uuid)
        if self.is_culled:
            logger.error('Can not save culled journeys')
            raise Exception('Can not save culled journeys')

        filepath = os.path.join(STAGED_DATA_DIR, str(self.uuid) + '.json')

        os.makedirs(
            os.path.dirname(filepath),
            exist_ok=True
        )

        with open(filepath, 'w') as f:
            json.dump(
                self.serialize(minimal=True),
                f
            )

    def send(self):
        logger.info('Sending %s', self.uuid)
        if not self.is_culled:
            self.cull()

        # TODO: networkey stuff

        if DELETE_ON_SEND:
            os.remove(self.filepath)
        else:
            os.rename(
                self.filepath,
                os.path.join(SENT_DATA_DIR, os.path.basename(self.filepath))
            )

    def plot_route(self):
        base = self.bounding_graph
        base.add_nodes_from(self.route_graph.nodes(data=True))
        base.add_edges_from(self.route_graph.edges(data=True))
        ox.plot_graph_route(base, self.route)

    @property
    def route(self):
        """
        Get a list of nodes representing the journey.

        Only useful once route_graph is merged with a more detailed graph
        """
        return list(self.route_graph._node.keys())

    @property
    def route_graph(self):
        """
        Get a graph of the journey since routes are only to the closest
        node of a premade graph

        Fairly possible I just don't understand osmnx properly and am
        doing this badly
        """
        graph = nx.Graph()

        for (origin, destination) in window(self):
            graph.add_node(
                origin.uuid,
                **{'x': origin.lng, 'y': origin.lat}
            )
            graph.add_node(
                destination.uuid,
                **{'x': destination.lng, 'y': destination.lat}
            )
            graph.add_edge(
                origin.uuid,
                destination.uuid,
                length=origin.distance_from_point(destination)
            )

        return graph

    @property
    def bounding_graph(self):
        """
        Get a graph of the journey as the box that contains the route
        """
        return ox.graph_from_bbox(
            self.most_northern,
            self.most_southern,
            self.most_eastern,
            self.most_western,
            network_type='bike'
        )

    @property
    def origin(self):
        return self[0]

    @property
    def destination(self):
        return self[-1]

    @property
    def duration(self):
        return self.destination.time - self.origin.time

    @property
    def direct_distance(self):
        return self[0].distance_from_point(self[-1])


class Journeys(GenericObjects):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('child_class', Journey)
        super(Journeys, self).__init__(*args, **kwargs)

    @property
    def most_northern(self):
        return max([journey.most_northern for journey in self])

    @property
    def most_southern(self):
        return min([journey.most_southern for journey in self])

    @property
    def most_eastern(self):
        return min([journey.most_eastern for journey in self])

    @property
    def most_western(self):
        return min([journey.most_western for journey in self])

    @property
    def bounding_graph(self):
        """
        Get a graph that contains all journeys
        """
        return ox.graph_from_bbox(
            self.most_northern,
            self.most_southern,
            self.most_eastern,
            self.most_western,
            network_type='bike'
        )
