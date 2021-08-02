class AccelerometerPoint():

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

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
            return AccelerometerPoint(
                obj[0],
                obj[1],
                obj[2]
            )
        else:
            raise NotImplementedError(
                'Can\'t parse AccelerometerPoint from type %s' % (type(obj))
            )

    def serialize(self):
        return {
            'x': self.x,
            'y': self.y,
            'z': self.z
        }

    @property
    def is_populated(self):
        """
        Is the xyz acceleromeer data populated.
        """
        return all([
            isinstance(self.x, float),
            isinstance(self.y, float),
            isinstance(self.z, float)
        ])
