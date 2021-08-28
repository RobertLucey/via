import hashlib
import statistics
from numbers import Number

import reverse_geocoder
from shapely.geometry import (
    MultiPoint,
    Point
)

from via.settings import MIN_ACC_SCORE
from via.place_cache import place_cache
from via.models.generic import (
    GenericObject,
    GenericObjects
)
from via.models.gps import GPSPoint


class Context(object):

    def __init__(self, *args, **kwargs):
        raise Exception()

    @property
    def is_context_populated(self):
        return self.context_pre != [] and self.context_post != []

    # have some function to get the direction we're coming from / going to so we can better tell what road the point is on

    def set_context(self, pre=None, post=None):
        if not self.is_context_populated:
            self.context_pre = pre
            self.context_post = post

    @property
    def angle_incoming(self):
        """
        From earliest pre to current
        """
        pass

    @property
    def angle_outgoing(self):
        pass

    @property
    def dist_to_earliest(self):
        pass

    @property
    def dist_to_latest(self):
        pass

    def serialize(self, include_time=True):
        return {
            'pre': [p.serialize(include_time=include_time, include_context=False) for p in self.pre],
            'post': [p.serialize(include_time=include_time, include_context=False) for p in self.post]
        }


class FramePoint(GenericObject, Context):
    """
    Data which snaps to the gps giving something like
    {gps: (1, 2), acc: [1,2,3], time: 1}

    Rather than
    {gps: (1, 2), acc: 1, time: 1}
    {gps: (1, 2), acc: 2, time: 2}
    {gps: (1, 2), acc: 3, time: 3}
    """

    def __init__(self, time, gps, acceleration):
        """

        :param time:
        :param gps: GPSPoint or dict serialization of GPSPoint
        :param acceneration:
        """

        self.context_pre = []
        self.context_post = []

        super().__init__()

        self.time = time
        self.gps = GPSPoint.parse(gps)

        if isinstance(acceleration, list):
            self.acceleration = [acc for acc in acceleration if acc >= MIN_ACC_SCORE]
        else:
            if acceleration is None:
                acceleration = 0
            assert isinstance(acceleration, Number)
            self.acceleration = [acc for acc in [acceleration] if acc >= MIN_ACC_SCORE]

    def append_acceleration(self, acc):
        if isinstance(acc, list):
            for item in acc:
                self.append_acceleration(item)
        elif isinstance(acc, type(None)):
            return
        else:
            if acc >= MIN_ACC_SCORE:
                self.acceleration.append(acc)

    @staticmethod
    def parse(obj):
        if isinstance(obj, FramePoint):
            return obj

        if isinstance(obj, dict):
            return FramePoint(
                obj.get('time', None),
                obj['gps'],
                obj['acc'] if obj['acc'] >= MIN_ACC_SCORE else None
            )
        else:
            raise NotImplementedError(
                'Can\'t parse Point from type %s' % (type(obj))
            )

    def speed_between(self, point):
        metres_per_second = None
        distance = self.distance_from(point.gps)
        if distance != 0:
            time_diff = point.time - self.time
            metres_per_second = distance / time_diff
        return metres_per_second

    def distance_from(self, point):
        """

        :param point: GPSPoint or tuple of (lat, lng) or Frame object
        :rtype: float
        :return: Distance between points in metres
        """
        if isinstance(point, FramePoint):
            point = point.gps
        return self.gps.distance_from(point)

    @property
    def is_complete(self):
        """
        Does the point contain all expected data
        """
        return isinstance(self.time, float) and self.gps.is_populated and self.acceleration != []

    @property
    def road_quality(self):
        try:
            return int(statistics.mean(self.acceleration) * 100)
        except:
            return 0

    def serialize(self, include_time=True, include_context=True):
        data = {
            'gps': self.gps.serialize(),
            'acc': list(self.acceleration),
        }
        if include_time:
            data['time'] = round(self.time, 2)
        if include_context:
            data['context'] = {
                'pre': [p.serialize(include_time=include_time, include_context=False) for p in self.context_pre],
                'post': [p.serialize(include_time=include_time, include_context=False) for p in self.context_post],
            }
        return data

    @property
    def gps_hash(self):
        return self.gps.content_hash


class FramePoints(GenericObjects):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('child_class', FramePoint)
        super().__init__(*args, **kwargs)

    @property
    def most_northern(self):
        return max([frame.gps.lat for frame in self])

    @property
    def most_southern(self):
        return min([frame.gps.lat for frame in self])

    @property
    def most_eastern(self):
        return max([frame.gps.lng for frame in self])

    @property
    def most_western(self):
        return min([frame.gps.lng for frame in self])

    @property
    def data_quality(self):
        """
        Get the percentage of frames that are good. Should
        automatically disregard journeys with low data quality

        :rtype: float
        :return: The percent between 0 and 1
        """
        return 1  # TODO

    @property
    def origin(self):
        """

        :rtype: via.models.Frame
        :return: The first frame of the journey
        """
        return self[0]

    @property
    def destination(self):
        """

        :rtype: via.models.Frame
        :return: The last frame of the journey
        """
        return self[-1]

    @property
    def duration(self):
        """

        :rtype: float
        :return: The number of seconds the journey took
        """
        return self.destination.time - self.origin.time

    @property
    def direct_distance(self):
        """

        :rtype: float
        :return: distance from origin to destination in metres
        """
        return self[0].distance_from(self[-1])

    def serialize(self, include_time=False, include_context=True):
        return [frame.serialize(include_time=include_time, include_context=include_context) for frame in self]

    def get_multi_points(self):
        """
        Get a shapely.geometry.MultiPoint of all the points
        """
        unique_points = []
        prev = None
        for frame in self:
            if frame.gps.is_populated:
                if prev is not None:
                    if prev.gps.lat != frame.gps.lat:
                        unique_points.append(
                            Point(
                                frame.gps.lng,
                                frame.gps.lat
                            )
                        )

            prev = frame

        return MultiPoint(
            unique_points
        )

    @property
    def content_hash(self):
        return hashlib.md5(
            str([
                point.serialize(include_time=True, include_context=True) for point in self
            ]).encode()
        ).hexdigest()

    @property
    def country(self):
        """
        Get what country this journey started in

        :return: a two letter country code
        :rtype: str
        """
        return reverse_geocoder.search(
            (
                self.origin.gps.lat,
                self.origin.gps.lng
            )
        )[0]['cc']

    def is_in_place(self, place_name: str):
        """
        Get if a journey is entirely within the bounds of some place.
        Does this by rect rather than polygon so it isn't exact but mainly
        to be used to focus on a single city.

        :param place_name: An osmnx place name. For example "Dublin, Ireland"
            To see if the place name is valid try graph_from_place(place).
            Might be good to do that in here and throw an ex if it's not found
        """
        place_bounds = place_cache.get(place_name)
        try:
            return all([
                self.most_northern < place_bounds['north'],
                self.most_southern > place_bounds['south'],
                self.most_eastern < place_bounds['east'],
                self.most_western > place_bounds['west']
            ])
        except ValueError:
            return False
