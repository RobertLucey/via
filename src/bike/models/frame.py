from haversine import haversine, Unit

from bike.models.generic import (
    GenericObject,
    GenericObjects
)
from bike.models.gps import GPSPoint


class Frame(GenericObject):

    def __init__(self, time, gps, acceleration):
        super().__init__()
        self.time = time
        self.gps = GPSPoint(gps['lat'], gps['lng'])  # TODO: elevation
        self.acceleration = acceleration

    @staticmethod
    def parse(obj):
        if isinstance(obj, Frame):
            return obj
        if isinstance(obj, dict):
            return Frame(
                obj['time'],
                obj['gps'],
                obj['acc']
            )
        raise ValueError()

    def distance_from_point(self, point):
        if isinstance(point, Frame):
            point = point.gps.point
        return haversine(self.gps.point, point, unit=Unit.METERS)

    @property
    def is_complete(self):
        return all([
            isinstance(self.time, float),
            self.gps.is_populated,
            len(self.acceleration) == 3,
            all(isinstance(dp, float) for dp in self.acceleration)
        ])

    def serialize(self):
        return {
            'time': round(self.time, 2),
            'gps': self.gps.serialize(),
            'acc': self.acceleration
        }


class Frames(GenericObjects):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('child_class', Frame)
        super().__init__(*args, **kwargs)

    @property
    def most_northern(self):
        return max([frame.lat for frame in self])

    @property
    def most_southern(self):
        return min([frame.lat for frame in self])

    @property
    def most_eastern(self):
        return min([frame.lng for frame in self])

    @property
    def most_western(self):
        return max([frame.lng for frame in self])

    @property
    def quality(self):
        # Mixed with the deviation between times?
        return len([f for f in self if f.is_complete]) / float(len(self))
