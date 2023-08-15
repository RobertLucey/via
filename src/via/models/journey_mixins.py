from collections import defaultdict

import osmnx
from networkx.classes.multidigraph import MultiDiGraph

from via import settings
from via import logger
from via.utils import (
    filter_nodes_from_geodataframe,
    filter_edges_from_geodataframe,
    update_edge_data,
    get_graph_id,
    area_from_coords,
    get_combined_id,
)
from via.network_cache import network_cache
from via.bounding_graph_gdfs_cache import bounding_graph_gdfs_cache


class SnappedRouteGraphMixin:
    @property
    def snapped_route_graph(self) -> MultiDiGraph:
        """ """
        bounding_graph = self.graph
        used_edges = []
        used_node_ids = []

        for start, end, _ in bounding_graph.edges:
            graph_edge_id = get_combined_id(start, end)
            if graph_edge_id in self.used_combined_edges:
                used_node_ids.extend([start, end])
                used_edges.append(tuple([start, end, 0]))

        if bounding_graph_gdfs_cache.get(get_graph_id(bounding_graph)) is None:
            bounding_graph_gdfs_cache.set(
                get_graph_id(bounding_graph),
                osmnx.graph_to_gdfs(bounding_graph, fill_edge_geometry=True),
            )

        graph_nodes, graph_edges = bounding_graph_gdfs_cache.get(
            get_graph_id(bounding_graph)
        )

        graph = osmnx.graph_from_gdfs(
            filter_nodes_from_geodataframe(graph_nodes, used_node_ids),
            filter_edges_from_geodataframe(graph_edges, used_edges),
        )

        return update_edge_data(graph, self.edge_quality_map)


class BoundingGraphMixin:
    def get_bounding_graph(self, use_graph_cache: bool = True) -> MultiDiGraph:
        logger.debug(
            "Plotting bounding graph (n,s,e,w) (%s, %s, %s, %s)",
            self.most_northern,
            self.most_southern,
            self.most_eastern,
            self.most_western,
        )

        if use_graph_cache is False or network_cache.get(self) is None:
            logger.debug("bbox > %s not found in cache, generating...", self.gps_hash)
            network = osmnx.graph_from_bbox(
                self.most_northern,
                self.most_southern,
                self.most_eastern,
                self.most_western,
                network_type=self.network_type,
                simplify=True,
            )
            network_cache.set(network, self.bbox)

        return network_cache.get(self)

    @property
    def bounding_graph(self):
        """
        Get a rectangular graph which contains the journey
        """
        return self.get_bounding_graph(use_graph_cache=True)

    @property
    def area(self) -> float:
        """
        Get the area of the bounding box in m^2
        """
        return area_from_coords(self.bbox)
