import argparse
import statistics
from collections import defaultdict

from bike.utils import (
    get_journeys,
    get_combined_id,
    force_list
)


def print_condition(journeys, min_edge_usage):
    """

    :param journeys:
    :param min_edge_usage:
    """

    for key, journey in journeys.get_mega_journeys().items():

        bounding_graph = journey.graph
        used_edges = journey.edge_quality_map

        merged_edge_data = {}

        for (u, v, k, d) in bounding_graph.edges(keys=True, data=True):
            combined_id = get_combined_id(u, v)
            if all([
                combined_id in used_edges,
                used_edges.get(combined_id, {}).get('count', -1) >= min_edge_usage
            ]):
                merged_edge_data[combined_id] = {
                    **used_edges[combined_id],
                    **d
                }

        name_quality_map = defaultdict(list)
        for edge in merged_edge_data.values():
            for name in force_list(edge.get('name', [])):
                name_quality_map[name].append(edge['avg'])

        name_quality_map = {
            k: statistics.mean(v) for k, v in name_quality_map.items()
        }
        name_quality_map = sorted(
            name_quality_map.items(),
            key=lambda x: x[1],
            reverse=True
        )

        print('==========\nFrom %s' % (key))

        for street_name, quality in name_quality_map:
            print('%s: %s' % (street_name.ljust(30), round(quality, 2)))

        print()


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--min-edge-usage',
        dest='min_edge_usage',
        type=int,
        help='The minimum number of times an edge has to be used for it to be included in the final data (1 per journey)',
        default=1
    )
    parser.add_argument(
        '--place',
        dest='place',
        default='Dublin, Ireland',
        help='What place to limit the data to (so you don\'t try to visualize too big an area). Must be an osmnx recognised place / format for example "Dublin, Ireland"'
    )
    args = parser.parse_args()

    journeys = get_journeys('remote', place=args.place)
    print_condition(journeys, args.min_edge_usage)


if __name__ == '__main__':
    main()
