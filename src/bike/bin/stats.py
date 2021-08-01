import argparse
import statistics
from collections import defaultdict

from bike.utils import (
    get_journeys,
    get_combined_id
)


def print_coverage(journeys, args):
    bounding_graph = journeys.graph
    used_edges = journeys.edge_quality_map
    total_length = 0
    used_length = 0
    for (u, v, k, d) in bounding_graph.edges(keys=True, data=True):
        combined_id = get_combined_id(u, v)
        if combined_id in used_edges and used_edges[combined_id]['count'] >= args.min_edge_usage:
            used_length += d['length']
        total_length += d['length']

    coverage_perc = (used_length / total_length) * 100

    print('Coverage: %s%%' % (round(coverage_perc, 2)))


def print_condition(journeys, args):
    bounding_graph = journeys.graph
    used_edges = journeys.edge_quality_map

    merged_edge_data = {}

    for (u, v, k, d) in bounding_graph.edges(keys=True, data=True):
        combined_id = get_combined_id(u, v)
        if combined_id in used_edges and used_edges[combined_id]['count'] >= args.min_edge_usage:
            merged_edge_data[combined_id] = {
                **used_edges[combined_id],
                **d
            }

    name_quality_map = defaultdict(list)
    for edge in merged_edge_data.values():
        if 'name' in edge:
            if not isinstance(edge['name'], list):
                names = [edge['name']]
            else:
                names = edge['name']

            for name in names:
                name_quality_map[name].append(edge['avg'])

    name_quality_map = {
        k: statistics.mean(v) for k, v in name_quality_map.items()
    }
    name_quality_map = sorted(
        name_quality_map.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for street_name, quality in name_quality_map:
        print('%s: %s' % (street_name.ljust(30), round(quality, 2)))


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
        '--coverage',
        action='store_true',
        dest='coverage',
        help='Get the coverage by length of the bounding box, to see what that box is and a visual represenation of the routes use plot_journeys'
    )
    parser.add_argument(
        '--condition-by-street',
        action='store_true',
        dest='condition_by_street',
        help='List the condition by the street name'
    )
    args = parser.parse_args()

    journeys = get_journeys()

    if args.coverage:
        print_condition(journeys, args)
    elif args.condition_by_street:
        print_condition(journeys, args)
    else:
        raise Exception('Must specify a stat to get')


if __name__ == '__main__':
    main()
