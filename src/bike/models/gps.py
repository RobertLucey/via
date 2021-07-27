from haversine import (
    haversine,
    Unit
)


class GPSPoint():

    def __init__(self, lat, lng, elevation=None):
        self.lat = lat
        self.lng = lng
        self.elevation = elevation

    def distance_from(self, point):
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
        return (self.lat, self.lng)

    @property
    def is_populated(self):
        return all([
            isinstance(self.lat, float),
            isinstance(self.lng, float)
        ])
