import hashlib
from numbers import Number

import numpy
from cached_property import cached_property

from via import settings
from via import logger
from via.place_cache import place_cache
from via.models.generic import GenericObject, GenericObjects
from via.models.gps import GPSPoint


class Context:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.context_pre = []
        self.context_post = []

    def __del__(self):
        attrs_to_del = ["content_hash"]

        for attr in attrs_to_del:
            try:
                delattr(self, attr)
            except Exception:
                pass

    def set_context(self, pre=None, post=None):
        if not self.is_context_populated:
            self.context_pre = pre
            self.context_post = post

    @property
    def is_context_populated(self) -> bool:
        """
        Do we have context forward and back?
        Not all context but at least some on either side
        """
        return self.context_pre != [] and self.context_post != []


class FramePoint(Context, GenericObject):
    """
    Data which snaps to the gps giving something like
    {gps: (1, 2), acc: [1,2,3], time: 1}

    Rather than
    {gps: (1, 2), acc: 1, time: 1}
    {gps: (1, 2), acc: 2, time: 2}
    {gps: (1, 2), acc: 3, time: 3}
    """

    def __init__(self, time, gps, acceleration, slow=None):
        """

        :param time:
        :param gps: GPSPoint or dict serialization of GPSPoint
        :param acceneration:
        :kwarg slow: If at this point the person is going slow
        """
        super().__init__()

        self.time = time
        self.gps = GPSPoint.parse(gps)
        self._slow = slow

        if isinstance(acceleration, list):
            self.acceleration = [
                acc for acc in acceleration if acc >= settings.MIN_ACC_SCORE
            ]
        else:
            if acceleration is None:
                acceleration = 0
            assert isinstance(acceleration, Number)
            self.acceleration = [
                acc for acc in [acceleration] if acc >= settings.MIN_ACC_SCORE
            ]

    @property
    def slow(self):
        if self.speed is None:
            return False  # Is this fair?

        if self._slow is not None:
            return self._slow

        return self._slow is False or (
            isinstance(self.speed, float)
            and self.speed <= settings.MIN_METRES_PER_SECOND
        )

    @property
    def speed(self):
        """
        Get the speed at this point (in metres per second) from the
        first and last context of this object

        Should have an option to get from the immediately surrounding points

        :rtype: float
        """
        if self.is_context_populated:
            origin = self.context_pre[0]
            dst = self.context_post[-1]

            if origin.time is None or dst.time is None:
                return None

            metres_per_second = 0
            distance = origin.distance_from(dst.gps)
            if distance != 0:
                time_diff = dst.time - origin.time
                metres_per_second = distance / time_diff
            return round(metres_per_second, 2)

        return None

    def append_acceleration(self, acc):
        if self.slow:
            return
        elif isinstance(acc, type(None)):
            return
        else:
            if acc >= settings.MIN_ACC_SCORE:
                self.acceleration.append(acc)

    @staticmethod
    def parse(obj):
        """
        Given a dict representation of a FramePoint (or a FramePoint object)
        return with a FramePoint object
        """
        if isinstance(obj, FramePoint):
            return obj

        if isinstance(obj, dict):
            return FramePoint(
                obj.get("time", None),
                obj["gps"],
                [acc for acc in obj["acc"] if acc >= settings.MIN_ACC_SCORE],
            )
        raise NotImplementedError(f"Can't parse Point from type {type(obj)}")

    def speed_between(self, point: GPSPoint) -> float:
        """
        Get the speed between this and another point (as the crow flies) in
        metres per second

        :param point: A FramePoint obj
        :return: metres per second
        :rtype: float
        """
        metres_per_second = None
        distance = self.distance_from(point.gps)
        if distance != 0:
            time_diff = point.time - self.time
            if time_diff == 0:
                return 0
            metres_per_second = distance / time_diff
        return metres_per_second

    def distance_from(self, point: GPSPoint) -> float:
        """

        :param point: GPSPoint or tuple of (lat, lng) or Frame object
        :rtype: float
        :return: Distance between points in metres
        """
        if isinstance(point, FramePoint):
            point = point.gps
        return self.gps.distance_from(point)

    @property
    def road_quality(self) -> int:
        """
        Get the average quality at this point (and a little before)

        :return: mean of acceleration points
        :rtype: float
        """
        if self.slow:
            return 0
        if self.acceleration == []:
            return 0
        return int(numpy.mean(self.acceleration) * 100)

    def serialize(
        self, include_time: bool = True, include_context: bool = True
    ) -> dict:
        data = {
            "gps": self.gps.serialize(),
            "acc": list(self.acceleration),
            "slow": self.slow,
        }
        if include_time:
            if self.time is not None:
                data["time"] = round(self.time, 2)
            else:
                data["time"] = None
        if include_context:
            data["context"] = {
                "pre": [
                    p.serialize(include_time=include_time, include_context=False)
                    for p in self.context_pre
                ],
                "post": [
                    p.serialize(include_time=include_time, include_context=False)
                    for p in self.context_post
                ],
            }
        return data

    @property
    def gps_hash(self) -> int:
        """
        Get the hash of the GPS of this point`
        """
        return self.gps.content_hash

    @cached_property
    def content_hash(self) -> int:
        """
        Get the hash of the contents of this point`
        """
        input_string = f"{self.acceleration} {self.gps.point} {self.time}"
        encoded_int = 0

        for char in input_string:
            encoded_int = (encoded_int << 8) + ord(char)
            encoded_int %= 1000000000

        return encoded_int


class FramePoints(GenericObjects):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("child_class", FramePoint)
        super().__init__(*args, **kwargs)

    @property
    def most_northern(self) -> float:
        """
        Get the max lat of all points
        """
        return max([frame.gps.lat for frame in self])

    @property
    def most_southern(self) -> float:
        """
        Get the min lat of all points
        """
        return min([frame.gps.lat for frame in self])

    @property
    def most_eastern(self) -> float:
        """
        Get the max lng of all points
        """
        return max([frame.gps.lng for frame in self])

    @property
    def most_western(self) -> float:
        """
        Get the min lng of all points
        """
        return min([frame.gps.lng for frame in self])

    @property
    def bbox(self) -> dict:
        return {
            "north": self.most_northern,
            "south": self.most_southern,
            "east": self.most_eastern,
            "west": self.most_western,
        }

    @property
    def data_quality(self) -> float:
        """
        Get the percentage of frames that are good. Should
        automatically disregard journeys with low data quality

        :rtype: float
        :return: The percent between 0 and 1
        """
        return 1.0  # TODO

    @property
    def origin(self):
        """
        Get the FramePoint at the start of the journey

        :rtype: via.models.Frame
        :return: The first frame of the journey
        """
        return self[0]

    @property
    def destination(self):
        """
        Get the FramePoint at the end of the journey

        :rtype: via.models.Frame
        :return: The last frame of the journey
        """
        return self[-1]

    @property
    def duration(self) -> float:
        """

        :rtype: float
        :return: The number of seconds the journey took
        """
        if self.destination.time is None or self.origin.time is None:
            return None
        return self.destination.time - self.origin.time

    @property
    def direct_distance(self) -> float:
        """

        :rtype: float
        :return: distance from origin to destination in metres
        """
        return self[0].distance_from(self[-1])

    def serialize(
        self, include_time: bool = False, include_context: bool = True
    ) -> list:
        return [
            frame.serialize(include_time=include_time, include_context=include_context)
            for frame in self
        ]

    @property
    def gps_hash(self) -> str:
        """
        Get the hash of all the GPSs of all of the points
        """
        return hashlib.md5(
            str([point.gps.content_hash for point in self]).encode()
        ).hexdigest()

    @property
    def content_hash(self) -> str:
        """
        Get the hash of all the data of all of the points
        """
        return hashlib.md5(
            str([point.content_hash for point in self]).encode()
        ).hexdigest()

    def is_in_place(self, place_name: str) -> bool:
        """
        Get if a journey is entirely within the bounds of some place.
        Does this by rect rather than polygon so it isn't exact but mainly
        to be used to focus on a single city.

        :param place_name: An osmnx place name. For example "Dublin, Ireland"
            To see if the place name is valid try graph_from_place(place).
            Might be good to do that in here and throw an ex if it's not found
        """
        return place_cache.is_in_place(self.bbox, place_name)
