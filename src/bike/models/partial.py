import json
import random
import os

import backoff
import requests
import fast_json

from bike import logger
from bike.utils import split_into
from bike.constants import (
    STAGED_DATA_DIR,
    SENT_DATA_DIR,
    PARTIAL_DATA_DIR
)
from bike.settings import (
    PARTIAL_RANDOMIZE_DATA_ORDER,
    TRANSPORT_TYPE,
    SUSPENSION,
    DELETE_ON_SEND,
    UPLOAD_URL,
    UPLOAD_EXCLUDE_TIME,
    PARTIAL_SPLIT_INTO
)
from bike.models.point import FramePoint, FramePoints
from bike.models.frame import (
    Frame,
    Frames
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

        self.transport_type = kwargs.get('transport_type', TRANSPORT_TYPE)
        self.suspension = kwargs.get('suspension', SUSPENSION)

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

    def save(self):
        """
        This should not be done locally as it would just duplicate data.
        The journeys the data comes from should be the things that are
        marked as saved.

        This should only be used on the server
        """
        logger.info('Saving partial %s', self.uuid)

        filepath = os.path.join(PARTIAL_DATA_DIR, str(self.uuid) + '.json')

        os.makedirs(
            os.path.dirname(filepath),
            exist_ok=True
        )

        with open(filepath, 'w') as journey_file:
            json.dump(
                self.serialize(minimal=True),
                journey_file
            )

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_time=5
    )
    def send(self):
        logger.info('Sending partial %s', self.uuid)
        requests.post(
            url=UPLOAD_URL,
            json=self.serialize(exclude_time=True)
        )

    def serialize(self, *args, **kwargs):
        frame_data = super().serialize(exclude_time=True)
        return {
            'uuid': str(self.uuid),
            'data': random.sample(frame_data, len(frame_data)) if PARTIAL_RANDOMIZE_DATA_ORDER else frame_data,
            'transport_type': self.transport_type,
            'suspension': self.suspension,
            'is_partial': self.is_partial
        }

    #def post_send(self):
    #    filepath = os.path.join(STAGED_DATA_DIR, str(self.uuid) + '.json')
    #    if DELETE_ON_SEND:
    #        os.remove(filepath)
    #        logger.debug('Deleted: %s', filepath)
    #    else:
    #        sent_filepath = os.path.join(SENT_DATA_DIR, str(self.uuid) + '.json')
    #        os.rename(
    #            filepath,
    #            sent_filepath
    #        )
    #        logger.debug('Moved %s -> %s', filepath, sent_filepath)


def partials_from_journey(journey):
    """

    :param journey: megajourney to split into partials
    :rtype: list
    :return: a list of partials that make up the entire mega journey
    """
    if len(journey.included_journeys) < 2:
        logger.warning(
            'Getting partial from a journey that only has %s included journeys' % (
                len(journey.included_journeys)
            )
        )

    split_data = split_into(
        random.sample(journey._data, len(journey._data)),
        PARTIAL_SPLIT_INTO
    )
    partials = []
    for partial_sample in split_data:
        partial = Partial()
        partial.extend(partial_sample)
        partial.transport_type = journey.transport_type
        partial.suspension = journey.suspension
        partials.append(partial)

    return partials
