import numbers

from haversine import (
    haversine,
    Unit
)


class GPSPoint():
    """
    GPSPoint is an object containing geospatial data in three directions.

    Should be used instead of tuples of (lat, lng) or whatever since
    sometimes libraries expect (lng, lat)
    """

    def __init__(self, lat, lng, elevation=None):
        """

        :param lat:
        :param lng:
        :kwarg elevation: Optional elevation in metres
        """
        self.lat = lat
        self.lng = lng
        self.elevation = elevation

    @staticmethod
    def parse(obj):
        if isinstance(obj, GPSPoint):
            return obj
        elif isinstance(obj, dict):
            return GPSPoint(
                obj['lat'],
                obj['lng'],
                elevation=obj.get('elevation', None)
            )
        elif isinstance(obj, list):
            return GPSPoint(
                obj[0],
                obj[1]
            )
        else:
            raise NotImplementedError(
                'Can\'t parse gps from type %s' % (type(obj))
            )

    def distance_from(self, point):
        """

        :param point: GPSPoint or tuple of (lat, lng)
        :rtype: float
        :return: Distance between points in metres
        """
        if isinstance(point, GPSPoint):
            point = point.point
        return haversine(self.point, point, unit=Unit.METERS)

    def serialize(self):
        return {
            'lat': self.lat,
            'lng': self.lng,
            'elevation': self.elevation
        }

    @property
    def point(self):
        """

        :rtype: tuple
        :return: tuple of (lat, lng)
        """
        return (self.lat, self.lng)

    @property
    def is_populated(self):
        """
        Is the gps data populated. Often when there is no satelite
        or starting up this will not be populated.

        Does not consider elevation since it's not important

        :rtype: bool
        """
        return all([
            isinstance(self.lat, numbers.Number),
            isinstance(self.lng, numbers.Number),
            self.lat != 0,
            self.lng != 0
        ])
