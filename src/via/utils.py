import math
import os
import glob
import json
import time
from functools import lru_cache
from numbers import Number
from functools import wraps
from itertools import (
    islice,
    chain
)
from typing import (
    Any,
    List,
    Tuple
)

from geopandas.geodataframe import GeoDataFrame
from networkx.classes.multidigraph import MultiDiGraph
import osmnx as ox
import fast_json

from via import logger
from via.settings import (
    MIN_JOURNEY_VERSION,
    MAX_JOURNEY_VERSION
)
from via.constants import (
    METRES_PER_DEGREE,
    DATA_DIR,
    REMOTE_DATA_DIR,
    DEFAULT_EDGE_COLOUR
)
from via.models.gps import GPSPoint


@lru_cache(maxsize=10000)
def is_journey_data_file(potential_journey_file: str) -> bool:
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
        logger.warning('%s json could not be decoded', potential_journey_file)
        return False
    else:
        if not all([
            'uuid' in data,
            'data' in data,
            'transport_type' in data
        ]):
            logger.warning(
                '%s is not a data file as it does not have appropriate data',
                potential_journey_file
            )
            return False

    return True


def get_journeys(
    transport_type=None,
    source=None,
    place=None,
    version_op=None,
    version=None,
    earliest_time=None,
    latest_time=None,
):
    """
    Get local journeys as Journeys

    :kwarg transport_type: bike|car|scooter|whatever else is on the app
    :kwarg source: The data dir to get from
    :kwarg place: The place to get journeys within
    :kwarg version_op: The operator the journey version must pass to
        be returned
    :kwarg version: The version to compare with version_op and the
        journey version
    :rtype: Journey
    """
    from via.models.journeys import Journeys
    return Journeys(
        data=list(
            iter_journeys(
                transport_type=transport_type,
                source=source,
                place=place,
                version_op=version_op,
                version=version,
                earliest_time=earliest_time,
                latest_time=latest_time
            )
        )
    )


def iter_journeys(
    transport_type=None,
    source=None,
    place=None,
    version_op=None,
    version=None,
    earliest_time=None,
    latest_time=None
):
    """
    Get local journeys as iterable of Journey

    :kwarg transport_type: bike|car|scooter|whatever else is on the app
    :kwarg source: The data dir to get from
    :kwarg place: The place to get journeys within
    :kwarg version_op: The operator the journey version must pass to
        be returned
    :kwarg version: The version to compare with version_op and the
        journey version
    """
    from via.models.journey import Journey
    for journey_file in get_data_files(
        transport_type=transport_type,
        source=source
    ):
        journey = Journey.from_file(journey_file)
        if should_include_journey(
            journey,
            place=place,
            version_op=version_op,
            version=version,
            earliest_time=earliest_time,
            latest_time=latest_time
        ):
            yield journey


def should_include_journey(
    journey,
    place=None,
    version_op=None,
    version=None,
    earliest_time=None,
    latest_time=None
):
    if any([
        journey.version < MIN_JOURNEY_VERSION,
        journey.version > MAX_JOURNEY_VERSION
    ]):
        return False

    if version_op is not None:
        if not version_op(journey.version, version):
            return False

    if place is not None:
        if not journey.is_in_place(place):
            return False

    if earliest_time is not None:
        if journey.timestamp < earliest_time:
            return False

    if latest_time is not None:
        if journey.timestamp > latest_time:
            return False

    return journey


def get_data_files(transport_type=None, source=None) -> List[str]:
    """

    :kwarg transport_type: bike|car|scooter|whatever else is on the app
    :kwarg source: The data dir to get from
    :rtype: list
    :return: a list of file paths to journey files
    """
    from via.models.journey import Journey
    files = []

    path = DATA_DIR
    if source == 'remote':
        path = REMOTE_DATA_DIR
    elif source is None:
        path = DATA_DIR

    for filename in glob.iglob(path + '/**/*', recursive=True):
        if is_journey_data_file(filename):
            if transport_type not in {None, 'all'}:
                journey_transport_type = os.path.split(os.path.dirname(filename))[-1]
                if journey_transport_type is not None:
                    if journey_transport_type.lower() == transport_type:
                        files.append(filename)
            else:
                files.append(filename)

    return files


def sleep_until_ready(started: Number, finished: Number, max_seconds=0):
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


def sleep_until(max_seconds: Number):
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


def get_idx_default(lst: list, idx: int, default: Any) -> Any:
    """
    Get the ith elem of a list or a default value if out of range
    """
    assert isinstance(lst, list)
    try:
        return lst[idx]
    except (IndexError, TypeError):
        return default


def get_combined_id(obj: Any, other_obj: Any) -> int:
    """

    :param obj: hashable thing
    :param other_obj: hashable thing
    :rtype: int
    :return: A unque id that will be the same regardless of param order
    """
    return hash(obj) + hash(other_obj)


def get_ox_colours(
    graph: MultiDiGraph,
    colour_map_name: str,
    edge_map=None,
    key_name=None
) -> List:  # TODO: better list hint, not sure what this returns
    """
    NB: only used in local osmnx graphing

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


def get_edge_colours(
    graph: MultiDiGraph,
    colour_map_name: str,
    key_name=None,
    edge_map=None
) -> List:  # TODO: better list hint, not sure what this returns
    """
    NB: only used in local osmnx graphing

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

    if edge_map is not None:
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

    raise Exception('Can not determine what colours to generate. Must give an edge_map or key_name')


def force_list(val: Any) -> List[Any]:
    """
    If the val is not already a list, make it the only element in the list

    :rtype: list
    """
    if not isinstance(val, list):
        return [val]
    return val


def flatten(lst: List) -> List[Any]:
    '''
    Given a nested list, flatten it.

    Usage:
        >>> flatten([[1, 2, 3], [1, 2]])
        [1, 2, 3, 1, 2]

    :param lst: list to be flattened
    :return: Flattened list
    '''
    return list(chain.from_iterable(lst))


def filter_nodes_from_geodataframe(
    nodes_dataframe: GeoDataFrame,
    nodes_to_keep: List[int]
) -> GeoDataFrame:
    to_keep = []
    nodes_to_keep = set(nodes_to_keep)
    for node in nodes_dataframe.index:
        if node in nodes_to_keep:
            to_keep.append(node)
    return nodes_dataframe.loc[to_keep]


def filter_edges_from_geodataframe(
    edges_dataframe: GeoDataFrame,
    edges_to_keep: List[Tuple[int, int, int]]
) -> GeoDataFrame:
    to_keep = []
    edges_to_keep = set([hash(e) for e in edges_to_keep])
    for edge in edges_dataframe.index:
        if hash(edge) in edges_to_keep:
            to_keep.append(edge)
    return edges_dataframe.loc[to_keep]


def update_edge_data(graph: MultiDiGraph, edge_data_map: dict) -> MultiDiGraph:
    """

    :param graph:
    :param edge_data_map: A dict of values to set on the associated
        edge id (key of edge_data_map)
    """

    # TODO: if fewer items in edge_data_map loop over that
    # rather than graph.edges

    for start, end, _ in graph.edges:
        graph_edge_id = get_combined_id(start, end)
        if graph_edge_id in edge_data_map:
            try:
                graph[start][end][0].update(
                    edge_data_map[graph_edge_id]
                )
            except:
                logger.error(f'Could not update edge: {start} {end}')

    return graph


def get_slope(origin: GPSPoint, dst: GPSPoint):
    return (origin.lng - dst.lng) / (origin.lat - dst.lat)


def get_edge_slope(nodes, edge):
    """
    Given an edge, get the slope of it
    """
    origin = nodes[edge[0][0][0]]
    dst = nodes[edge[0][0][1]]

    origin = GPSPoint(origin['y'], origin['x'])
    dst = GPSPoint(dst['y'], dst['x'])

    return get_slope(origin, dst)


def angle_between_slopes(s1, s2, ensure_positive=False, absolute=False):
    """

    :param s1:
    :param s2:
    :kwargs ensure_positive: Ensure the result is always positive
        Useful in comparisons where you don't care about direction
        and want -45 to also equal 135 for example
    """
    degrees = math.degrees(math.atan((s2 - s1) / (1 + (s2 * s1))))
    if absolute:
        degrees = abs(degrees)
    if ensure_positive:
        if degrees < 0:
            degrees = 180 + degrees
    return degrees


def is_within(bbox, potentially_larger_bbox):
    """

    :param bbox:
    :param potentially_larger_bbox:
    """
    return all([
        bbox['north'] <= potentially_larger_bbox['north'],
        bbox['south'] >= potentially_larger_bbox['south'],
        bbox['east'] <= potentially_larger_bbox['east'],
        bbox['west'] >= potentially_larger_bbox['west']
    ])


def area_from_coords(obj):
    if 'north' in obj.keys():
        vert = obj['north'] - obj['south']
        hori = obj['east'] - obj['west']

        return (vert * METRES_PER_DEGREE) * (hori * METRES_PER_DEGREE)

    else:
        raise NotImplementedError()
        # TODO: Allow for normal polys. Below is an example of doing it for a bbox
        #geom = Polygon(
        #    [
        #        (obj['north'], obj['west']),
        #        (obj['north'], obj['east']),
        #        (obj['south'], obj['east']),
        #        (obj['south'], obj['west']),
        #        (obj['north'], obj['west'])
        #    ]
        #)
        #return ops.transform(
        #    partial(
        #        pyproj.transform,
        #        pyproj.Proj('EPSG:4326'),
        #        pyproj.Proj(
        #            proj='aea',
        #            lat_1=geom.bounds[1],
        #            lat_2=geom.bounds[3]
        #        )
        #    ),
        #    geom
        #).area
