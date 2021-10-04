import hashlib
from typing import Tuple

from haversine import (
    haversine,
    Unit
)

HAVERSINE_CACHE = {}


class GPSPoint():
    """
    GPSPoint is an object containing geospatial data in three directions.

    Should be used instead of tuples of (lat, lng) or whatever since
    sometimes libraries expect (lng, lat)
    """

    def __init__(self, lat: float, lng: float, elevation=None):
        """

        :param lat:
        :param lng:
        :kwarg elevation: Optional elevation in metres
        """
        self.lat = lat
        self.lng = lng
        self.elevation = elevation

    def __eq__(self, oth):
        return self.lat == oth.lat and self.lng == oth.lng

    @staticmethod
    def parse(obj):
        if isinstance(obj, GPSPoint):
            return obj

        if isinstance(obj, list):
            return GPSPoint(
                obj[0],
                obj[1]
            )
        elif isinstance(obj, dict):
            return GPSPoint(
                obj['lat'],
                obj['lng'],
                elevation=obj.get('elevation', None)
            )

        raise NotImplementedError(
            'Can\'t parse gps from type %s' % (type(obj))
        )

    def distance_from(self, point) -> float:
        """

        :param point: GPSPoint or tuple of (lat, lng)
        :rtype: float
        :return: Distance between points in metres
        """
        if isinstance(point, GPSPoint):
            point = point.point

        key = hash((self.point, point))
        if key not in HAVERSINE_CACHE:
            HAVERSINE_CACHE[key] = haversine(
                self.point,
                point,
                unit=Unit.METERS
            )

        return HAVERSINE_CACHE[key]

    def slope_between(self, dst):
        from via.models.point import FramePoint
        if isinstance(dst, FramePoint):
            dst = dst.gps
        try:
            return (self.lng - dst.lng) / (self.lat - dst.lat)
        except ZeroDivisionError:
            return 0

    def serialize(self):
        return {
            'lat': self.lat,
            'lng': self.lng,
            'elevation': self.elevation
        }

    @property
    def content_hash(self) -> str:
        """
        A content hash that will act as an id for the data, handy for caching
        """
        return hashlib.md5(
            f'{self.lat} {self.lng} {self.elevation}'.encode()
        ).hexdigest()

    @property
    def point(self) -> Tuple[float]:
        """

        :rtype: tuple
        :return: tuple of (lat, lng)
        """
        return (self.lat, self.lng)

    @property
    def is_populated(self) -> bool:
        """
        Is the gps data populated. Often when there is no satelite
        or starting up this will not be populated.

        Does not consider elevation since it's not important

        :rtype: bool
        """
        return isinstance(self.lat, (int, float)) and isinstance(self.lng, (int, float)) and self.lat != 0 and self.lng != 0
