import fast_json

from bike import logger
from bike.models.point import (
    FramePoint,
    FramePoints
)


class Partial(FramePoints):
    """
    When sending never includes time as it can't be used for anything but
    stitching together a journey which we don't want
    """

    def __init__(self, *args, **kwargs):
        """

        :kwarg transport_type: What transport type being used, defaults
            to settings.TRANSPORT_TYPE
        :kwarg suspension: If using suspension or not, defaults
            to settings.SUSPENSION
        """
        kwargs.setdefault('child_class', FramePoint)
        super().__init__(*args, **kwargs)

        self.is_partial = True

        self.transport_type = kwargs.get('transport_type', None)
        self.suspension = kwargs.get('suspension', None)

        self.network_type = 'bike'

    @staticmethod
    def parse(obj):
        if isinstance(obj, Partial):
            return obj
        elif isinstance(obj, dict):
            return Partial(
                **obj
            )

        # TODO: do this from an object serialization
        raise NotImplementedError(
            'Can\'t parse Partial from type %s' % (type(obj))
        )

    @staticmethod
    def from_file(filepath: str):
        """
        Given a file get a Partial object. Since we don't save there will
        be no local partial files

        :param filepath: Path to a saved journey file
        :rtype: bike.models.journey.Journey
        """
        logger.debug('Loading partial from %s', filepath)
        with open(filepath, 'r') as journey_file:
            return Partial(
                **fast_json.loads(journey_file.read())
            )

    def serialize(self, *args, **kwargs):
        frame_data = super().serialize(exclude_time=True)
        return {
            'uuid': str(self.uuid),
            'data': frame_data,
            'transport_type': self.transport_type,
            'suspension': self.suspension,
            'is_partial': self.is_partial
        }
