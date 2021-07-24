from haversine import haversine, Unit

from bike.models.generic import (
    GenericObject,
    GenericObjects
)


class Frame(GenericObject):

    def __init__(self, time, gps, acceleration):
        super(Frame, self).__init__()
        self.time = time
        self.gps = gps
        self.acceleration = acceleration

    @staticmethod
    def parse(obj):
        if isinstance(obj, Frame):
            return obj
        elif isinstance(obj, dict):
            return Frame(
                obj['time'],
                obj['gps'],
                obj['acc']
            )
        else:
            raise ValueError()

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
