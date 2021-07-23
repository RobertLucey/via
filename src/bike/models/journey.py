import uuid
import json
import os

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
    SUSPENSION
)
from bike.models.frame import Frames


class Journey():

    def __init__(self, **kwargs):
        self.uuid = str(uuid.uuid4())
        self.frames = Frames()
        self.is_culled = False

        self.transport_type = kwargs.get('transport_type', TRANSPORT_TYPE)
        self.suspension = kwargs.get('suspension', SUSPENSION)

    def append(self, frame):
        self.frames.append(frame)

    @property
    def origin(self):
        return self.frames[0]

    @property
    def destination(self):
        return self.frames[-1]

    @property
    def duration(self):
        return self.frames[-1].time - self.frames[0].time

    @property
    def quality(self):
        # Mixed with the deviation between times?
        return len([f for f in self.frames if f.is_complete]) / float(len(self.frames))

    @property
    def filepath(self):
        return os.path.join(STAGED_DATA_DIR, str(self.uuid) + '.json')

    @property
    def direct_distance(self):
        return self.frames[0].distance_from_point(self.frames[-1])

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

        for frame in self.frames:
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
            'data': self.frames.serialize(),
            'transport_type': self.transport_type,
            'suspension': self.suspension,
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

    def save(self):
        logger.info('Saving %s', self.uuid)
        if self.is_culled:
            logger.error('Can not save culled journeys')
            raise Exception('Can not save culled journeys')

        with open(self.filepath, 'w') as f:
            json.dump(
                self.serialize(minimal=True),
                f
            )

    def cull_distance(self):
        """
        Remove the start and end of the journey, the start to remove
        will be until you are x metres away, the end to remove will be the
        last time you are x metres away from the destination
        """
        first_frame_away_idx = None
        last_frame_away_idx = None

        for idx, frame in enumerate(self.frames):
            if frame.distance_from_point(self.origin) > EXCLUDE_METRES_BEGIN_AND_END:
                first_frame_away_idx = idx
                break

        for idx, frame in enumerate(reversed(self.frames)):
            if frame.distance_from_point(self.destination) > EXCLUDE_METRES_BEGIN_AND_END:
                last_frame_away_idx = len(self.frames) - idx
                break

        if any(
            [
                first_frame_away_idx is None,
                last_frame_away_idx is None
            ]
        ):
            raise Exception('Not a long enough journey to get any meaningful data from')

        self.frames = self.frames[first_frame_away_idx:last_frame_away_idx]

    def cull_time(self, origin_time, destination_time):
        """
        Remove the start and end of a journey, the start to remove will be
        the first x minutes, the end to remove will be the last x minutes
        """
        if MINUTES_TO_CUT != 0:
            min_time = origin_time
            max_time = destination_time

            tmp_frames = Frames()
            for frame in self.frames:
                if any([
                    frame.time > min_time + (60 * MINUTES_TO_CUT),
                    frame.time < max_time - (60 * MINUTES_TO_CUT)
                ]):
                    continue
                tmp_frames.append(frame)

            self.frames = tmp_frames

        if self.is_culled:
            return

    def cull(self):

        origin_time = self.origin.time
        destination_time = self.destination.time

        orig_frame_count = len(self.frames)

        self.cull_distance()
        self.cull_time(origin_time, destination_time)

        new_frame_count = len(self.frames)

        self.is_culled = True

        logger.info(
            'Culled %s removed %s % frames',
            self.uuid,
            (new_frame_count / orig_frame_count) * 100
        )

    def send(self):
        logger.info('Sending %s', self.uuid)
        if not self.is_culled:
            self.cull()

        # TODO: networkey stuff

        os.rename(
            self.filepath,
            os.path.join(SENT_DATA_DIR, os.path.basename(self.filepath))
        )

    @property
    def graph(self):
        """
        Get a graph of the journey since routes are only to the closest
        node of a premade graph

        Fairly possible I just don't understand osmnx properly and am
        doing this badly
        """
        graph = nx.Graph()

        for (origin, destination) in window(self.frames):
            graph.add_node(
                origin.uuid,
                **{'x': origin.lng, 'y': origin.lat}
            )
            graph.add_node(
                destination.uuid,
                **{'x': destination.lng, 'y': destination.lat}
            )
            graph.add_edge(origin.uuid, destination.uuid)

        return graph
