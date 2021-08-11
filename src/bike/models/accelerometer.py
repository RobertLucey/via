import numbers


class AccelerometerPoint():

    def __init__(self, *args):

        # FIXME: This is is gross

        self.x = None
        self.y = None
        self.z = None
        self.vertical = None

        if len(args) == 3:
            self.x = args[0]
            self.y = args[1]
            self.z = args[2]
        elif len(args) == 1:
            self.vertical = args[0]
        else:
            raise Exception('Can\'t init AccelerometerPoint')

    @staticmethod
    def parse(obj):
        if isinstance(obj, AccelerometerPoint):
            return obj
        elif isinstance(obj, dict):
            return AccelerometerPoint(
                obj['x'],
                obj['y'],
                obj['z']
            )
        elif isinstance(obj, (list, tuple)):
            if len(obj) == 0:
                return AccelerometerPoint(None)
            else:
                return AccelerometerPoint(
                    obj[0],
                    obj[1],
                    obj[2]
                )
        elif isinstance(obj, (numbers.Number, type(None))):
            return AccelerometerPoint(
                obj
            )
        else:
            raise NotImplementedError(
                'Can\'t parse AccelerometerPoint from type %s' % (type(obj))
            )

    def serialize(self):
        if isinstance(self.vertical, numbers.Number) or not self.xyz_populated:
            return self.vertical
        return {
            'x': self.x,
            'y': self.y,
            'z': self.z
        }

    @property
    def xyz_populated(self):
        return all([
            isinstance(self.x, numbers.Number),
            isinstance(self.y, numbers.Number),
            isinstance(self.z, numbers.Number)
        ])

    @property
    def is_populated(self):
        """
        Is the xyz acceleromeer data populated.
        """
        if isinstance(self.vertical, numbers.Number):
            return True

        return self.xyz_populated

    @property
    def quality(self):
        if isinstance(self.vertical, numbers.Number):
            return self.vertical
        else:
            return self.x + self.y + self.z
