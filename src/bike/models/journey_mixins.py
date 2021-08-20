import os

import fast_json

import shapely

from networkx.readwrite import json_graph
import osmnx as ox

from bike.utils import (
    window,
    filter_nodes_from_geodataframe,
    filter_edges_from_geodataframe,
    update_edge_data
)
from bike.nearest_edge import nearest_edge
from bike.constants import GEOJSON_DIR


class SnappedRouteGraphMixin():

    @property
    def snapped_route_graph(self):
        """
        Get the route graph, snapping to the nearest edge
        """
        bounding_graph = self.graph

        nearest_edge.get(bounding_graph, self.all_points, return_dist=False)

        edges = []
        used_node_ids = []
        for (our_origin, our_destination) in window(self.all_points, window_size=2):
            edge = nearest_edge.get(
                bounding_graph,
                [
                    our_origin
                ]
            )
            edges.append(tuple(edge[0]))
            used_node_ids.extend([edge[0][0], edge[0][1]])

        graph_nodes, graph_edges = ox.graph_to_gdfs(
            bounding_graph,
            fill_edge_geometry=True
        )

        # Filter only the nodes and edges on the route and ignore the
        # buffer used to get context
        graph = ox.graph_from_gdfs(
            filter_nodes_from_geodataframe(graph_nodes, used_node_ids),
            filter_edges_from_geodataframe(graph_edges, edges)
        )

        return update_edge_data(graph, self.edge_quality_map)


class GeoJsonMixin():

    @property
    def geojson(self):
        """
        Write and return a GeoJSON object string of the graph.
        """
        geojson_file = os.path.join(
            GEOJSON_DIR,
            self.content_hash + '.geojson'
        )

        if os.path.exists(geojson_file):
            geojson_features = None
            with open(geojson_file, 'r') as json_file:
                geojson_features = fast_json.loads(json_file.read())
        else:
            json_links = json_graph.node_link_data(
                self.snapped_route_graph
            )['links']

            geojson_features = {
                'type': 'FeatureCollection',
                'features': []
            }

            for link in json_links:
                if 'geometry' not in link:
                    continue

                feature = {
                    'type': 'Feature',
                    'properties': {}
                }

                for k in link:
                    if k == 'geometry':
                        feature['geometry'] = shapely.geometry.mapping(
                            link['geometry']
                        )
                    else:
                        feature['properties'][k] = link[k]

                geojson_features['features'].append(feature)

            if not os.path.exists(geojson_file):
                os.makedirs(
                    os.path.join(GEOJSON_DIR),
                    exist_ok=True
                )

            with open(geojson_file, 'w') as json_file:
                fast_json.dump(
                    geojson_features,
                    json_file,
                    indent=4
                )

        return geojson_features
