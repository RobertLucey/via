import datetime
import urllib
from packaging.version import Version
import dateutil.parser

import shapely
from networkx.readwrite import json_graph

from via.constants import USELESS_GEOJSON_PROPERTIES


def parse_start_date(earliest_date: str) -> str:
    if earliest_date is None:
        raise ValueError("earliest_date cannot be None")

    if isinstance(earliest_date, str):
        earliest_date = dateutil.parser.parse(earliest_date)
    elif isinstance(earliest_date, datetime.date):
        earliest_date = datetime.datetime.combine(
            earliest_date, datetime.datetime.min.time()
        )

    return str(earliest_date.date())


def parse_end_date(latest_date: str) -> str:
    if latest_date is None:
        raise ValueError("latest_date cannot be None")

    if isinstance(latest_date, str):
        latest_date = dateutil.parser.parse(latest_date)
    elif isinstance(latest_date, datetime.date):
        latest_date = datetime.datetime.combine(
            latest_date, datetime.datetime.min.time()
        )

    return str(latest_date.date())


def geojson_from_graph(graph, must_include_props: list = None) -> dict:
    json_links = json_graph.node_link_data(graph)["links"]

    geojson_features = {"type": "FeatureCollection", "features": []}

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
