import numbers


class AccelerometerPoint():

    def __init__(self, *args):

        if isinstance(args[0], numbers.Number):
            self.vertical = args[0]
        elif isinstance(args[0], (list, tuple)):
            self.vertical = list(args[0])
        else:
            self.vertical = None

    @staticmethod
    def parse(obj):
        if isinstance(obj, (int, float, type(None))):
            return AccelerometerPoint(
                obj
            )
        elif isinstance(obj, (list, tuple)):
            return [AccelerometerPoint(o) for o in obj]
        elif isinstance(obj, AccelerometerPoint):
            return obj
        else:
            raise NotImplementedError(
                'Can\'t parse AccelerometerPoint from type %s' % (type(obj))
            )

    def serialize(self):
        return self.vertical

    @property
    def is_populated(self):
        if self.vertical is not None:
            return True

        return False

    @property
    def quality(self):
        if isinstance(self.vertical, (int, float)):
            return self.vertical
        return False
