import datetime
import statistics
from pathlib import Path
from functools import cache
from collections import defaultdict
from packaging import version

from dateutil.parser import parse

from cachetools.func import ttl_cache
from cached_property import cached_property

import networkx as nx

from mappymatch.maps.nx.readers.osm_readers import (
    NetworkType,
    parse_osmnx_graph,
)
from mappymatch.constructs.trace import Trace
from mappymatch.maps.nx.nx_map import NxMap
from mappymatch.matchers.lcss.lcss import LCSSMatcher
from mappymatch.utils.plot import plot_matches

import pandas

from via import settings
from via import logger
from via.utils import window, get_combined_id, get_graph_id
from via.constants import (
    VALID_JOURNEY_MIN_DISTANCE,
    VALID_JOURNEY_MIN_POINTS,
    VALID_JOURNEY_MIN_DURATION,
)
from via.geojson.utils import geojson_from_graph
from via.models.point import FramePoint, FramePoints
from via.models.frame import Frame
from via.edge_cache import get_edge_data
from via.network_cache import network_cache
from via.models.journey_mixins import (
    SnappedRouteGraphMixin,
    BoundingGraphMixin,
)


@ttl_cache(maxsize=25, ttl=60 * 60)
def get_nxmap(bounding_graph):
    return NxMap(parse_osmnx_graph(bounding_graph, NetworkType.BIKE))


@ttl_cache(maxsize=25, ttl=60 * 60)
def get_matcher_by_graph(bounding_graph):
    nx_map = get_nxmap(bounding_graph)
    return LCSSMatcher(
        nx_map,
    )


class Journey(FramePoints, SnappedRouteGraphMixin, BoundingGraphMixin):
    """
    A single journey (or patial journey)

    Relates to one raw file downloaded through pull_journeys
    """

    def __init__(self, *args, **kwargs):
        """

        :kwarg data:
        :kwarg transport_type: What transport type being used, defaults
            to settings.TRANSPORT_TYPE
        :kwarg suspension: If using suspension or not, defaults
            to settings.SUSPENSION
        :kwarg version: What version of the client software was used
        :kwarg network_type: What osm network type to use for nodes/edges
        :kwarg timestamp: The timestamp of the journey
        """
        self.gps_inclusion_iter = 0
        self.too_slow = False

        data = []
        if "data" in kwargs:
            data = kwargs.pop("data")

        kwargs.setdefault("child_class", FramePoint)
        super().__init__(*args, **kwargs)

        self.extend(data)

        self._version = kwargs.get("version", None)

        self.transport_type = str(kwargs.get("transport_type", "unknown")).lower()
        self.suspension = kwargs.get("suspension", None)

        self.network_type = kwargs.get("network_type", "bike")
        self._timestamp = kwargs.get("timestamp", None)

        self.last_gps = None

    def __del__(self):
        attrs_to_del = ["edge_quality_map", "route_graph"]

        for attr in attrs_to_del:
            try:
                delattr(self, attr)
            except Exception:
                pass

    @staticmethod
    def parse(objs):
        """
        Given a dict representation of a Journey (or a Journey object)
        return with a Journey object
        """
        if isinstance(objs, Journey):
            return objs

        if isinstance(objs, dict):
            return Journey(**objs)

        raise NotImplementedError(f"Can't parse journey from type {type(objs)}")

    def set_contexts(self):
        """
        For each of the FramePoints in the journey give each of them
        context of their surrounding points
        """

        if len(self._data) < 7:
            return

        # set context for idx 1 and -2 as 3 (as 0 and -1 will be skipped for context setting)
        self._data[1].set_context(pre=[self._data[0]], post=[self._data[2]])
        self._data[-2].set_context(pre=[self._data[-3]], post=[self._data[-1]])

        # set context for 2 and -3 as 5 (as 1 and -2 will be skipped for context setting)
        self._data[2].set_context(
            pre=[self._data[0], self._data[1]], post=[self._data[3], self._data[4]]
        )
        self._data[-3].set_context(
            pre=[self._data[-5], self._data[-4]], post=[self._data[-2], self._data[-1]]
        )

        # then do normal loop which will skip the ones already set because they'll be on the edge
        for one, two, three, four, five, six, seven in window(self, window_size=7):
            if not four.is_context_populated:
                four.set_context(pre=[one, two, three], post=[five, six, seven])

    def extend(self, objs):
        # Possibly shouldn't set contexts here and should be done explicitly
        for obj in objs:
            self.append(obj)
        self.set_contexts()

    def append(self, obj):
        """
        NB: appending needs to be chronological (can be reversed, just so
        long as it's consistent) as if no accelerometer data it assigns
        the accelerometer data to the previously seen gps

        Though journey data may not have time it will (should) always be
        chronological
        """
        # TODO: warn if not chronological
        if isinstance(obj, FramePoint):
            self._data.append(obj)
        elif isinstance(obj, (dict, Frame)):
            # Most datapoints are only accelerometer so we need to find the
            # closest point with gps in the past to add the accelerometer
            # data to

            frame = Frame.parse(obj)

            frame_gps_populated = frame.gps.is_populated

            if frame_gps_populated:
                if self.gps_inclusion_iter % settings.GPS_INCLUDE_RATIO == 0:
                    self.last_gps = frame.gps
                else:
                    frame.gps = self.last_gps
                self.gps_inclusion_iter += 1
            else:
                if not hasattr(self, "last_gps"):
                    return
                if not self.last_gps:
                    return
                frame.gps = self.last_gps

            if len(self._data) == 0:
                self._data.append(FramePoint(frame.time, frame.gps, frame.acceleration))
                return

            # Annotate points that are too slow / fast in relation to
            # the previous point
            if (
                frame_gps_populated or frame.gps.is_populated
            ) and frame.time is not None:
                metres_per_second = self._data[-1].speed_between(frame)
                if metres_per_second is not None:
                    if any(
                        [
                            metres_per_second < settings.MIN_METRES_PER_SECOND,
                            metres_per_second > settings.MAX_METRES_PER_SECOND,
                        ]
                    ):
                        self.too_slow = True
                    else:
                        self.too_slow = False

            if self.too_slow:
                # Annotate as slow so we don't use it to get paths or use
                # it for accelerometer data
                # A bit more testing to do before putting in
                pass
                # self._data.append(
                #    FramePoint(frame.time, frame.gps, frame.acceleration, slow=True)
                # )
            else:
                if self._data[-1].gps == frame.gps:
                    self._data[-1].append_acceleration(frame.acceleration)
                else:
                    self._data.append(
                        FramePoint(frame.time, frame.gps, frame.acceleration)
                    )
        else:
            raise NotImplementedError("Cannot append to journey of type: {type(obj)}")

    def get_indirect_distance(self, n_seconds: int = 0) -> float:
        """
        NB: Data must be chronological

        :param n_seconds: use the location every n seconds as if the
            location is calculated too frequently the distance
            travelled could be artificially inflated
        :rtype: float
        :return: distance travelled in metres
        """
        previous_used_frame = None
        distances = []

        for frame in self:
            if frame.time is None and n_seconds != 0:
                continue
            if previous_used_frame is None:
                previous_used_frame = frame
            elif n_seconds == 0 or frame.time >= previous_used_frame.time + n_seconds:
                distances.append(previous_used_frame.distance_from(frame))
                previous_used_frame = frame

        return sum(distances)

    def get_avg_speed(self, n_seconds: int = 30) -> float:
        """
        NB: Data must be chronological

        :param n_seconds: use the location every n seconds as if the
                        location is calculated too frequently the distance
                        travelled could be artificially inflated
        :rtype: float
        :return: avg speed in metres per second
        """
        if len(self) < 2:
            raise ValueError(f"Cannot get avg speed of journey with {len(self)} points")
        if self.duration is None or self.duration == 0:
            return None
        return self.get_indirect_distance(n_seconds=n_seconds) / self.duration

    def serialize(
        self,
        minimal: bool = False,
        include_time: bool = True,
        include_context: bool = True,
    ):
        data = {
            "uuid": str(self.uuid),
            "version": str(self.version),
            "data": super().serialize(
                include_time=include_time, include_context=include_context
            ),
            "transport_type": self.transport_type,
            "suspension": self.suspension,
        }

        if minimal is False:
            data.update(
                {
                    "direct_distance": self.direct_distance,
                    "indirect_distance": {
                        1: self.get_indirect_distance(n_seconds=1),
                        5: self.get_indirect_distance(n_seconds=5),
                        10: self.get_indirect_distance(n_seconds=10),
                        30: self.get_indirect_distance(n_seconds=30),
                    },
                    "data_quality": self.data_quality,
                    "duration": self.duration,
                    "avg_speed": self.get_avg_speed(),
                }
            )

        return data

    @property
    def timestamp(self):
        if self._timestamp is None:
            return None
        if isinstance(self._timestamp, datetime.datetime):
            return self._timestamp
        return parse(self._timestamp)

    @cached_property
    def edge_quality_map(self):
        """
        Get a map between edge_hash and road quality of the road. edge_map
        being edge_id and road quality being something that hasn't been
        defined yet TODO

        :rtype: dict
        """
        data = {}
        for edge_id, single_edge_data in self.edge_data.items():
            qualities = [edge["avg_road_quality"] for edge in single_edge_data]
            speed = (
                statistics.mean([val["speed"] for val in single_edge_data])
                if None not in [val["speed"] for val in single_edge_data]
                else None
            )
            if len(qualities) == 0:
                data[edge_id] = {"avg": 0, "count": 0, "speed": speed}
            else:
                data[edge_id] = {
                    "avg": int(statistics.mean(qualities)),
                    "count": len(qualities),
                    "speed": speed,
                }

        return {
            edge_id: d
            for edge_id, d in data.items()
            if d["count"] >= settings.MIN_PER_JOURNEY_USAGE
        }

    @cached_property
    def edge_data(self):
        """
        Get all the edges with their associated data for this journey.

        TODO: replace with a conventional algo for matching

        :rtype: dict
        :return: {edge_id: [{edge_data}, {edge_data}]}
        """
        trace = [(p.gps.lat, p.gps.lng) for p in self.all_points]
        trace = Trace.from_dataframe(pandas.DataFrame(trace), True, 0, 1)

        # This takes a long time, cache it more
        matcher = get_matcher_by_graph(self.bounding_graph)

        match_result = matcher.match_trace(trace)

        data = defaultdict(list)

        for (our_origin, our_destination), match_point in zip(
            window(self, window_size=2), match_result.matches
        ):
            if not match_point or not match_point.road:
                continue

            edge = (
                (match_point.road.road_id.start, match_point.road.road_id.end, 0),
                0,
            )

            our_edge_data = get_edge_data(
                our_origin.uuid, our_destination.uuid, graph=self.route_graph
            )

            data[get_combined_id(edge[0][0], edge[0][1])].append(our_edge_data)

        if len(data) < settings.MIN_EDGES_PER_JOURNEY:
            return defaultdict(list)

        return data

    def write_mappy_path(self, filepath=None):
        """
        Save the mappymatch path. Useful for debugging weird paths.

        :kwarg filepath: Optional filepath to save to, /tmp/{self.uuid}_matches_map.html if not specified
        """
        filepath = f"/tmp/{self.uuid}_matches_map.html" if not filepath else filepath
        mmap_file = Path(filepath)
        trace = [(p.gps.lat, p.gps.lng) for p in self.all_points]
        trace = Trace.from_dataframe(pandas.DataFrame(trace), True, 0, 1)
        matcher = get_matcher_by_graph(self.bounding_graph)
        match_result = matcher.match_trace(trace)
        mmap = plot_matches(match_result.matches)
        mmap.save(str(mmap_file))
        logger.debug("Saved mappymatch path to: %s", filepath)

    @cached_property
    def route_graph(self):
        """
        Get a graph of the journey without snapping to closest node / edge
        """
        graph = nx.Graph()

        combined_edge_data = defaultdict(list)

        for origin, destination in window(self, window_size=2):
            edge_id = get_combined_id(origin.uuid, destination.uuid)

            graph.add_node(origin.uuid, **{"x": origin.gps.lng, "y": origin.gps.lat})
            graph.add_node(
                destination.uuid, **{"x": destination.gps.lng, "y": destination.gps.lat}
            )

            distance = origin.distance_from(destination)

            # NOTE: Maybe road_quality to None if speed is too slow?
            combined_edge_data[edge_id].append(
                {
                    "origin": origin,
                    "destination": destination,
                    "distance": distance,
                    "road_quality": origin.road_quality,
                    "speed": (origin.speed + destination.speed) / 2
                    if (origin.speed is not None and destination.speed is not None)
                    else None
                    # TODO: other bits, speed / elevation maybe?
                }
            )

        merged_edge_data = {}
        for shared_id, values in combined_edge_data.items():
            merged_edge_data[shared_id] = {
                "origin": values[0]["origin"],
                "destination": values[0]["destination"],
                "distance": values[0]["distance"],
                "avg_road_quality": statistics.mean(
                    [val["road_quality"] for val in values]
                ),
                "max_road_quality": max([val["road_quality"] for val in values]),
                "speed": statistics.mean([val["speed"] for val in values])
                if None not in [val["speed"] for val in values]
                else None,
            }

        for shared_id, values in merged_edge_data.items():
            graph.add_edge(
                values["origin"].uuid,
                values["destination"].uuid,
                length=values["distance"],
                avg_road_quality=values["avg_road_quality"],
                max_road_quality=values["max_road_quality"],
                speed=values["speed"],
            )

        return graph

    @property
    def bbox(self) -> dict:
        return {
            "north": self.most_northern,
            "south": self.most_southern,
            "east": self.most_eastern,
            "west": self.most_western,
        }

    @property
    def graph(self):
        """
        Get a graph of the journey but excluding nodes far away from the route

        :rtype: networkx.classes.multidigraph.MultiDiGraph
        """
        return self.bounding_graph

    @property
    def all_points(self):
        """
        Return all the points in this journey.

        May be a bit expensive since it sets contexts. Can probably get away
        with selectively doing this
        """
        self.set_contexts()
        return self._data

    @property
    def version(self):
        """
        Get the version of the app used to generate this data

        :rtype: version.Version
        """
        if not self._version:
            return version.parse("0.0.0")
        if isinstance(self._version, version.Version):
            return self._version
        return version.parse(self._version)

    @property
    def has_enough_data(self):
        """
        Return if the journey has enough data to be included in the final stats
        """
        return all(
            [
                self.get_indirect_distance(n_seconds=0) >= VALID_JOURNEY_MIN_DISTANCE,
                len(self._data) >= VALID_JOURNEY_MIN_POINTS,
                self.duration >= VALID_JOURNEY_MIN_DURATION
                or (self.destination.time is None and self.origin.time is None)
                if self.duration is not None
                else True,
            ]
        )

    @property
    def geojson(self):
        # TODO: Does this *need* to return edge_id (or any other props)?
        # edge_id not used in front end seemingly and other nullables can be
        # handled wherever... edge_id wasn't being returned for any data I
        # tried so this is a hack for now.
        return geojson_from_graph(
            self.snapped_route_graph,
            must_include_props=None,
        )

    @property
    def used_combined_edges(self):
        # used for getting snapped journey route graph
        return list(self.edge_data.keys())
