import os
import glob
import json
import time
from functools import wraps
from itertools import islice, chain

import osmnx as ox
import fast_json

from bike import logger
from bike.constants import (
    DATA_DIR,
    REMOTE_DATA_DIR,
    DEFAULT_EDGE_COLOUR
)


def get_board():
    try:
        import board
        return board
    except ImportError:
        return None


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
            data = fast_json.loads(potential_journey_file_io.read())
    except (json.decoder.JSONDecodeError, ValueError):
        return False
    else:
        if not all([
            'uuid' in data,
            'data' in data,
            'transport_type' in data
        ]):
            return False

    return True


def get_journeys(source=None, place=None):
    """
    Get local journeys as Journeys

    :kwarg source: The data dir to get from
    :kwarg place: The place to get journeys within
    :rtype: Journey
    """
    from bike.models.journeys import Journeys
    return Journeys(data=list(iter_journeys(source=source, place=place)))


def iter_journeys(source=None, place=None):
    """
    Get local journeys as iterable of Journey

    :kwarg source: The data dir to get from
    :kwarg place: The place to get journeys within
    """
    from bike.models.journey import Journey
    for journey_file in get_data_files(source=source):
        journey = Journey.from_file(journey_file)
        if place is not None:
            if journey.is_in_place(place):
                yield journey
        else:
            yield journey


def get_data_files(source=None):
    """

    :kwarg source: The data dir to get from
    :rtype: list
    :return: a list of file paths to journey files
    """
    files = []

    path = DATA_DIR
    if source == 'remote':
        path = REMOTE_DATA_DIR
    elif source is None:
        path = DATA_DIR

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


def get_ox_colours(graph, colour_map_name, edge_map=None, key_name=None):
    """

    :param graph: MultiDiGraph
    :param colour_map_name: osmnx recognised colour gradient
    :kwarg key_name: The key on the edge data to use as colour intensity data
    :kwarg edge_map: edge_id to data containing colour intensity data
    :rtype: list
    :return: a list of colours indexed by edge order
    """
    if edge_map is not None:
        max_num_colours = max(
            [
                edge_map.get(get_combined_id(u, v), {}).get('avg', -1) for (u, v, _, _) in graph.edges(keys=True, data=True)
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


def get_edge_colours(graph, colour_map_name, key_name=None, edge_map=None):
    """

    :param graph: MultiDiGraph
    :param colour_map_name: osmnx recognised colour gradient
    :kwarg key_name: The key on the edge data to use as colour intensity data
    :kwarg edge_map: edge_id to data containing colour intensity data
    :rtype: list
    :return: a list of colours indexed by edge order
    """
    if key_name is not None:
        colours = get_ox_colours(
            graph,
            colour_map_name,
            key_name=key_name
        )

        return [
            get_idx_default(
                colours,
                d.get(key_name, None),
                DEFAULT_EDGE_COLOUR
            ) for u, v, k, d in graph.edges(
                keys=True,
                data=True
            )
        ]

    elif edge_map is not None:
        colours = get_ox_colours(
            graph,
            colour_map_name,
            edge_map=edge_map
        )

        return [
            get_idx_default(
                colours,
                edge_map.get(get_combined_id(u, v), {}).get('avg', None),
                DEFAULT_EDGE_COLOUR
            ) for (u, v, k, d) in graph.edges(
                keys=True,
                data=True
            )
        ]

    else:
        raise Exception('Can not determine what colours to generate. Must give an edge_map or key_name')


def force_list(val):
    """
    If the val is not already a list, make it the only element in the list

    :rtype: list
    """
    if not isinstance(val, list):
        return [val]
    return val


def split_into(seq, num):
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out


def flatten(lst):
    '''
    Given a nested list, flatten it.

    Usage:
        >>> flatten([[1, 2, 3], [1, 2]])
        [1, 2, 3, 1, 2]

    :param lst: list to be flattened
    :return: Flattened list
    '''
    return list(chain.from_iterable(lst))
