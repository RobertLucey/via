import statistics
import hashlib
from collections import defaultdict
from typing import List

from networkx.classes.multidigraph import MultiDiGraph

from via import logger
from via.geojson.utils import geojson_from_graph
from via.models.generic import GenericObjects
from via.models.journey import Journey
from via.models.journey_mixins import (
    SnappedRouteGraphMixin,
    BoundingGraphMixin,
)


def get_journey_edge_quality_map(journey):
    edge_quality_map = defaultdict(list)
    for edge_hash, edge_quality in journey.edge_quality_map.items():
        edge_quality_map[edge_hash].append(edge_quality)

    return dict(edge_quality_map)


class Journeys(GenericObjects, SnappedRouteGraphMixin, BoundingGraphMixin):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("child_class", Journey)
        super().__init__(*args, **kwargs)

        self.network_type = "bike"

    @property
    def edge_quality_map(self):
        """
        Get a map between edge_hash and road quality of the road. edge_map
        being edge id and road quality being something that hasn't been
        defined yet TODO

        :rtype: dict
        """

        journey_edge_quality_maps = [get_journey_edge_quality_map(i) for i in self]

        edge_quality_map = defaultdict(list)
        for journey_edge_quality_map in journey_edge_quality_maps:
            for edge_id, quals in journey_edge_quality_map.items():
                edge_quality_map[edge_id].extend(quals)

        return {
            edge_id: {
                "avg": int(statistics.mean([d["avg"] for d in data])),
                "count": len(data),
                "edge_id": edge_id,
                "speed": statistics.mean([val["speed"] for val in data])
                if None not in [val["speed"] for val in data]
                else None,
            }
            for edge_id, data in edge_quality_map.items()
        }

    @property
    def most_northern(self) -> float:
        """
        Get the most northerly latitude over all journeys
        """
        return max([journey.most_northern for journey in self])

    @property
    def most_southern(self) -> float:
        """
        Get the most southerly latitude over all journeys
        """
        return min([journey.most_southern for journey in self])

    @property
    def most_eastern(self) -> float:
        """
        Get the most easterly longitude over all journeys
        """
        return max([journey.most_eastern for journey in self])

    @property
    def most_western(self) -> float:
        """
        Get the most westerly longitude over all journeys
        """
        return min([journey.most_western for journey in self])

    def get_graph(self, use_graph_cache=True):
        return self.get_bounding_graph(use_graph_cache=use_graph_cache)

    @property
    def graph(self) -> MultiDiGraph:
        return self.get_graph(use_graph_cache=True)

    @property
    def gps_hash(self) -> str:
        """
        Get the hash of all the GPSs of the points in all the journeys
        """
        return hashlib.md5(
            str([journey.gps_hash for journey in self]).encode()
        ).hexdigest()

    @property
    def content_hash(self) -> str:
        """
        Get the hash of the contents of all the journeys
        """
        return hashlib.md5(
            str([journey.content_hash for journey in self]).encode()
        ).hexdigest()

    @property
    def used_combined_edges(self):
        # used for getting snapped journey route graph
        used_combined_edges = []
        for journey in self:
            used_combined_edges.extend(list(journey.edge_data.keys()))
        return used_combined_edges

    @property
    def bbox(self):
        return {
            "north": self.most_northern,
            "south": self.most_southern,
            "east": self.most_eastern,
            "west": self.most_western,
        }

    @property
    def geojson(self):
        region_map = defaultdict(Journeys)

        for journey in self:
            region_name = journey.region

            if region_name:
                region_map[region_name].append(journey)
            else:
                logger.warning(
                    f"Journey {journey.uuid} has no place_2 region. Excluding form results"
                )

        if len(region_map) > 1:
            geo_features = []
            for region_name, journeys in region_map.items():
                logger.debug(
                    "Getting geojson features of journeys group in region: %s",
                    region_name,
                )

                geojson = journeys.geojson

                geo_features.extend(geojson["features"])

            geo_features = {"type": "FeatureCollection", "features": geo_features}
            return geo_features

        return geojson_from_graph(
            self.snapped_route_graph, must_include_props=["count", "avg", "edge_id"]
        )
