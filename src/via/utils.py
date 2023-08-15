import hashlib
import os
from functools import lru_cache, cache
from itertools import islice
from typing import Any, List, Tuple

import pymongo

from geopandas.geodataframe import GeoDataFrame
from networkx.classes.multidigraph import MultiDiGraph

from via import logger
from via.settings import (
    MIN_JOURNEY_VERSION,
    MAX_JOURNEY_VERSION,
    MAX_JOURNEY_METRES_SQUARED,
    MONGO_RAW_JOURNEYS_COLLECTION,
)
from via.constants import METRES_PER_DEGREE
from via.models.gps import GPSPoint


@cache
def get_mongo_interface():
    """
    Returns the MongoDB DB interface. Here so it can be moved to utils.
    """
    db_url = os.environ.get("MONGODB_URL", "localhost")
    client = pymongo.MongoClient(db_url)
    return client[os.environ.get("MONGODB_DATABASE", "localhost")]


def get_journeys(
    transport_type: str = None,
    source: str = None,
    place: str = None,
    version_op: str = None,
    version: str = None,
    earliest_time: int = None,
    latest_time: int = None,
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
    :kwarg earliest_time:
    :kwarg latest_time:
    :rtype: Journeys
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
                latest_time=latest_time,
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
    latest_time=None,
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
    :kwarg earliest_time:
    :kwarg latest_time:
    :rtype: Journey
    """
    from via.models.journey import Journey

    mongo_interface = get_mongo_interface()

    # TODO: react to the following:
    # journey,
    # place=place,
    # version_op=version_op,
    # version=version,
    # earliest_time=earliest_time,
    # latest_time=latest_time,

    for raw_journey in getattr(mongo_interface, MONGO_RAW_JOURNEYS_COLLECTION).find():
        yield Journey(**raw_journey)


def should_include_journey(
    journey,
    place: str = None,
    version_op: str = None,
    version: str = None,
    earliest_time: int = None,
    latest_time: int = None,
) -> bool:
    if any(
        [journey.version < MIN_JOURNEY_VERSION, journey.version > MAX_JOURNEY_VERSION]
    ):
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

    # is is larger than 50km2
    # in time will split these into smaller journeys internally
    if journey.area > MAX_JOURNEY_METRES_SQUARED:
        return False

    if not journey.has_enough_data:
        return False

    return True


def window(sequence: List[Any], window_size: int = 2) -> List[Any]:
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


def get_combined_id(obj: Any, other_obj: Any) -> int:
    """

    :param obj: hashable thing
    :param other_obj: hashable thing
    :rtype: int
    :return: A unque id that will be the same regardless of param order
    """
    return hash(obj) + hash(other_obj)


def filter_nodes_from_geodataframe(
    nodes_dataframe: GeoDataFrame, nodes_to_keep: List[int]
) -> GeoDataFrame:
    nodes_to_keep = set(nodes_to_keep)
    to_keep = [node for node in nodes_dataframe.index if hash(node) in nodes_to_keep]
    return nodes_dataframe.loc[to_keep]


def filter_edges_from_geodataframe(
    edges_dataframe: GeoDataFrame, edges_to_keep: List[Tuple[int, int, int]]
) -> GeoDataFrame:
    edges_to_keep = set([hash(e) for e in edges_to_keep])
    to_keep = [edge for edge in edges_dataframe.index if hash(edge) in edges_to_keep]
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
                graph[start][end][0].update(edge_data_map[graph_edge_id])
            except KeyError:
                logger.error("Could not update edge: %s %s", start, end)

    return graph


def is_within(bbox: dict, potentially_larger_bbox: dict) -> bool:
    """

    :param bbox:
    :param potentially_larger_bbox:
    :return: Is the first param within the second
    :rtype: bool
    """
    return all(
        [
            bbox["north"] <= potentially_larger_bbox["north"],
            bbox["south"] >= potentially_larger_bbox["south"],
            bbox["east"] <= potentially_larger_bbox["east"],
            bbox["west"] >= potentially_larger_bbox["west"],
        ]
    )


def area_from_coords(obj: dict) -> float:
    """
    Returns the area of a box in metres per second
    """
    if "north" in obj.keys():
        vert = obj["north"] - obj["south"]
        hori = obj["east"] - obj["west"]

        return (vert * METRES_PER_DEGREE) * (hori * METRES_PER_DEGREE)

    raise NotImplementedError()
    # TODO: Allow for normal polys. Below is an example of doing it for a bbox
    # geom = Polygon(
    #    [
    #        (obj['north'], obj['west']),
    #        (obj['north'], obj['east']),
    #        (obj['south'], obj['east']),
    #        (obj['south'], obj['west']),
    #        (obj['north'], obj['west'])
    #    ]
    # )
    # return ops.transform(
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
    # ).area


@lru_cache(maxsize=5)
def get_graph_id(graph: MultiDiGraph, unreliable: bool = False) -> str:
    """

    TODO: have a supporting function that just gets the quick unreliable
          hash so we don't cache the graph itself

    :param graph:
    :kwarg unreliable: use hash which can be different from run to run
    """
    if unreliable:
        return hash(tuple(graph._node))
    return hashlib.md5(str(tuple(graph._node)).encode()).hexdigest()
