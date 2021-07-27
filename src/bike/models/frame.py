import random

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

    def distance_from(self, point):
        if isinstance(point, Frame):
            point = point.gps
        return self.gps.distance_from(point)

    @property
    def is_complete(self):
        return all([
            isinstance(self.time, float),
            self.gps.is_populated,
            len(self.acceleration) == 3,
            all(isinstance(dp, float) for dp in self.acceleration)
        ])

    @property
    def road_quality(self):
        # FIXME: base this number off accelerometer data
        return random.randint(0, 9)

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
        return max([frame.gps.lat for frame in self])

    @property
    def most_southern(self):
        return min([frame.gps.lat for frame in self])

    @property
    def most_eastern(self):
        return min([frame.gps.lng for frame in self])

    @property
    def most_western(self):
        return max([frame.gps.lng for frame in self])

    @property
    def data_quality(self):
        # Mixed with the deviation between times?
        return len([f for f in self if f.is_complete]) / float(len(self))
