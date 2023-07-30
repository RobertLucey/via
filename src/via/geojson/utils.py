import datetime
import urllib
from packaging.version import Version
import dateutil.parser

import shapely
from networkx.readwrite import json_graph

from via.constants import USELESS_GEOJSON_PROPERTIES


def parse_start_date(earliest_date: str) -> str:
    if earliest_date is None:
        return "2021-01-01"

    if isinstance(earliest_date, str):
        earliest_date = dateutil.parser.parse(earliest_date)

    if isinstance(earliest_date, datetime.date):
        earliest_date = datetime.datetime.combine(
            earliest_date, datetime.datetime.min.time()
        )

    if isinstance(earliest_date, datetime.datetime):
        earliest_date = datetime.datetime.combine(
            earliest_date.date(), datetime.datetime.min.time()
        )

        if earliest_date < datetime.datetime(2021, 1, 1):
            earliest_date = datetime.datetime(2021, 1, 1)

    return str(earliest_date.date())


def parse_end_date(latest_date: str) -> str:
    if latest_date is None:
        return "2023-12-31"

    if isinstance(latest_date, str):
        latest_date = dateutil.parser.parse(latest_date)

    if isinstance(latest_date, datetime.date):
        latest_date = datetime.datetime.combine(
            latest_date, datetime.datetime.min.time()
        )

    if isinstance(latest_date, datetime.datetime):
        latest_date = datetime.datetime.combine(
            latest_date.date(), datetime.datetime.min.time()
        )

        if latest_date > datetime.datetime(2023, 12, 31):
            latest_date = datetime.datetime(2023, 12, 31)

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


def get_point(properties: dict = None, gps=None) -> dict:
    return {
        "type": "Feature",
        "properties": properties if isinstance(properties, dict) else {},
        "geometry": {"type": "Point", "coordinates": [gps.lng, gps.lat]},
    }
