import uuid

from haversine import haversine, Unit

from bike.models.generic import (
    GenericObject,
    GenericObjects
)


class Frame(GenericObject):

    def __init__(self, time, gps, acceleration):
        self.uuid = uuid.uuid4()
        self.time = time
        self.gps = gps
        self.acceleration = acceleration

    @property
    def lat(self):
        return self.gps[0]

    @property
    def lng(self):
        return self.gps[1]

    def distance_from_point(self, point):
        if isinstance(point, Frame):
            point = point.gps
        return haversine(self.gps, point, unit=Unit.METERS)

    @property
    def is_complete(self):
        return all([
            isinstance(self.time, float),
            len(self.gps) == 2,
            all([isinstance(dp, float) for dp in self.gps]),
            len(self.acceleration) == 3,
            all([isinstance(dp, float) for dp in self.acceleration])
        ])

    def serialize(self):
        return {
            'time': self.time,
            'gps': self.gps,
            'acc': self.acceleration
        }


class Frames(GenericObjects):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('child_class', Frame)
        super(Frames, self).__init__(*args, **kwargs)
