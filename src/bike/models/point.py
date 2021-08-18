import statistics

from bike.models.generic import (
    GenericObject,
    GenericObjects
)
from bike.models.gps import GPSPoint


class FramePoint(GenericObject):
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
        super().__init__()
        self.time = time
        self.gps = GPSPoint.parse(gps)

        if isinstance(acceleration, list):
            self.acceleration = acceleration
        else:
            self.acceleration = [acceleration]

    @staticmethod
    def parse(obj):
        if isinstance(obj, FramePoint):
            return obj
        elif isinstance(obj, dict):
            return FramePoint(
                obj.get('time', None),
                obj['gps'],
                obj['acc']
            )
        else:
            raise NotImplementedError(
                'Can\'t parse Point from type %s' % (type(obj))
            )

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

    def serialize(self, exclude_time=False):
        data = {
            'gps': self.gps.serialize(),
            'acc': list(self.acceleration)
        }
        if not exclude_time:
            data['time'] = round(self.time, 2)

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

        :rtype: bike.models.Frame
        :return: The first frame of the journey
        """
        return self[0]

    @property
    def destination(self):
        """

        :rtype: bike.models.Frame
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

    def serialize(self, exclude_time=False):
        return [frame.serialize(exclude_time=exclude_time) for frame in self]
