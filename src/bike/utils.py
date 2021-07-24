import os
import glob
import json
import time
from functools import wraps
from itertools import islice

from bike import logger
from bike.constants import (
    DATA_DIR,
    STAGED_DATA_DIR,
    SENT_DATA_DIR
)
from bike.models.frame import Frame


def is_journey_data_file(fp: str):
    """

    :param fp:
    :rtype: bool
    :return: if the file contains journey data
    """
    if os.path.splitext(os.path.basename(fp))[1] != '.json':
        return False

    try:
        data = json.loads(open(fp, 'r').read())
    except:
        return False
    else:
        if not all([
            'uuid' in data,
            'data' in data,
            'transport_type' in data
        ]):
            return False

    return True


def iter_journeys(staged=None):
    for journey_file in get_data_files(staged=staged):
        yield journey_from_file(journey_file)


def get_data_files(staged=None):
    """

    :kwarg uploaded: To only return files that uploaded
                    None to return all
    :rtype: list
    :return: a list of file paths to journey files
    """
    files = []

    path = DATA_DIR
    if staged is True:
        path = STAGED_DATA_DIR
    elif staged is False:
        path = SENT_DATA_DIR

    for filename in glob.iglob(path + '/**/*', recursive=True):
        if is_journey_data_file(filename):
            files.append(filename)

    return files


def get_raw_journey_data(data_file: str):
    """
    Just reads the file but abstracted so we can handle compression since
    I'm not sure how big these files will get

    :param data_file:
    :rtype: list
    :return: All data collected from a journey
    """
    return json.loads(open(data_file, 'r').read())


def journey_from_file(journey_fp: str):
    # FIXME: all this is gross. Make a static method of Journey or something

    from bike.models.journey import Journey

    journey_data = get_raw_journey_data(journey_fp)

    journey = Journey(
        transport_type=journey_data['transport_type'],
        suspension=journey_data['suspension'],
        is_culled=journey_data['is_culled']
    )
    journey.uuid = journey_data['uuid']

    for dp in journey_data['data']:
        journey.append(
            Frame(
                dp['time'],
                dp['gps'],
                dp['acc']
            )
        )

    return journey


def sleep_until_ready(started, finished, max_seconds=0):
    """
    Given a starting time of the kickoff, if there is still time
    to wait, sleep that time, otherwise warn of being overdue.

    :param started:
    :param finished:
    :kwarg max_seconds:
    """
    time_diff = float(finished - started)

    wait_remainder = max_seconds - time_diff
    if wait_remainder > 0:
        time.sleep(wait_remainder)


def timing(function):
    """
    Decorator wrapper to log execution time, for profiling purposes.
    """
    @wraps(function)
    def wrapped(*args, **kwargs):
        start_time = time.monotonic()
        ret = function(*args, **kwargs)
        end_time = time.monotonic()
        logger.debug(
            'timing of "%s"  \t%s',
            function.__qualname__,
            end_time - start_time
        )
        return ret
    return wrapped


def sleep_until(max_seconds):
    """
    Decorator which sleeps until a given x seconds from starting if possible.
    """
    def real_decorator(function):
        def wrapper(*args, **kwargs):
            started = time.monotonic()
            result = function(*args, **kwargs)
            finished = time.monotonic()
            sleep_until_ready(started, finished, max_seconds=max_seconds)

            time_diff = finished - started
            percentage_time = (float(time_diff) / max_seconds) * 100
            if percentage_time > 100:
                # If it's getting up there, then log
                logger.debug(
                    'function "%s" took %s % of the max %s',
                    function.__qualname__,
                    percentage_time,
                    max_seconds
                )
            return result
        return wrapper
    return real_decorator


def window(seq, n=2):
    """
    Returns a sliding window (of width n) over data from the iterable
    """
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result
