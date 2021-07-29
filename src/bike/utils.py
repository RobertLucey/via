import os
import glob
import json
import time
from functools import wraps
from itertools import islice

import osmnx as ox

from bike import logger
from bike.constants import (
    DATA_DIR,
    STAGED_DATA_DIR,
    SENT_DATA_DIR
)


def is_journey_data_file(potential_journey_file: str):
    """

    :param potential_journey_file:
    :rtype: bool
    :return: if the file contains journey data
    """
    if os.path.splitext(potential_journey_file)[1] != '.json':
        return False

    try:
        with open(potential_journey_file, 'r') as potential_journey_file_io:
            data = json.loads(potential_journey_file_io.read())
    except json.decoder.JSONDecodeError:
        return False
    else:
        if not all([
            'uuid' in data,
            'data' in data,
            'transport_type' in data
        ]):
            return False

    return True


def get_journeys(staged=None):
    """
    Get local journeys as Journeys

    :kwarg staged: To only get staged journeys or not (gets sent ones too)
    :rtype: Journey
    """
    from bike.models.journey import Journeys
    return Journeys(data=list(iter_journeys(staged=staged)))


def iter_journeys(staged=None):
    """
    Get local journeys as iterable of Journey

    :kwarg staged: To only get staged journeys or not (gets sent ones too)
    """
    from bike.models.journey import Journey
    for journey_file in get_data_files(staged=staged):
        yield Journey.from_file(journey_file)


def get_data_files(staged=None):
    """

    :kwarg uploaded: To only return files that uploaded None to return all
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
                    'function "%s" took %s %% of the max %s',
                    function.__qualname__,
                    percentage_time,
                    max_seconds
                )
            return result
        return wrapper
    return real_decorator


def window(sequence, window_size=2):
    """
    Returns a sliding window (of width n) over data from the iterable
    """
    seq_iterator = iter(sequence)
    result = tuple(islice(seq_iterator, window_size))
    if len(result) == window_size:
        yield result
    for elem in seq_iterator:
        result = result[1:] + (elem,)
        yield result


def get_idx_default(lst: list, idx: int, default):
    """
    Get the ith elem of a list or a default value if out of range
    """
    assert isinstance(lst, list)
    try:
        return lst[idx]
    except (IndexError, TypeError):
        return default


def get_combined_id(obj, other_obj):
    """

    :param obj: hashable thing
    :param other_obj: hashable thing
    :rtype: int
    :return: A unque id that will be the same regardless of param order
    """
    return hash(obj) + hash(other_obj)


def get_colours(graph, colour_map_name, edge_map=None, key_name=None):
    if edge_map is not None:
        max_num_colours = max(
            [
                edge_map.get(get_combined_id(u, v), -1) for (u, v, _, _) in graph.edges(keys=True, data=True)
            ]
        ) + 1
    elif key_name is not None:
        max_num_colours = max(
            [
                d.get(key_name, -1) for (_, _, _, d) in graph.edges(keys=True, data=True)
            ]
        ) + 1
    else:
        raise Exception('Can not determine what colours to generate. Must give an edge_map or key_name')

    return ox.plot.get_colors(
        n=max_num_colours,
        cmap=colour_map_name
    )
