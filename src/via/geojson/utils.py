import copy
import shapely
from networkx.readwrite import json_graph
from networkx.classes.multidigraph import MultiDiGraph

from via.constants import USELESS_GEOJSON_PROPERTIES, EMPTY_GEOJSON


def geojson_from_graph(graph: MultiDiGraph, must_include_props: list = None) -> dict:
    """

    :param graph:
    :kwarg must_include_props:
    :return:
    :rtype: {type: str, features: [{...}, {...}]}
    """
    json_links = json_graph.node_link_data(graph)["links"]

    geojson_features = copy.deepcopy(EMPTY_GEOJSON)

    for link in json_links:
        if "geometry" not in link:
            continue

        feature = {"type": "Feature", "properties": {}}

        for k in link:
            if k == "geometry":
                feature["geometry"] = shapely.geometry.mapping(link["geometry"])
            else:
                feature["properties"][k] = link[k]
        for useless_property in USELESS_GEOJSON_PROPERTIES:
            if useless_property in feature.get("properties", {}).keys():
                del feature["properties"][useless_property]
        geojson_features["features"].append(feature)

    if must_include_props is not None:
        geojson_features["features"] = [
            f
            for f in geojson_features["features"]
            if len(set(f["properties"].keys()).intersection(set(must_include_props)))
            == len(must_include_props)
        ]

    return geojson_features
