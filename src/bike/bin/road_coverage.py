import argparse

from bike.utils import (
    get_journeys,
    get_combined_id
)


def print_coverage(journeys, min_edge_usage):
    """

    :param journeys:
    :param min_edge_usage:
    """

    for key, journey in journeys.get_mega_journeys().items():
        bounding_graph = journey.bounding_graph
        used_edges = journey.edge_quality_map
        used_edge_ids = []
        total_length = 0
        used_length = 0
        for (u, v, k, d) in bounding_graph.edges(keys=True, data=True):
            combined_id = get_combined_id(u, v)
            if combined_id in used_edge_ids:
                continue
            used_edge_ids.append(combined_id)
            if all([
                combined_id in used_edges,
                used_edges.get(combined_id, {}).get('count', -1) >= min_edge_usage
            ]):
                used_length += d['length']
            total_length += d['length']
        coverage_perc = (used_length / total_length) * 100
        print('Coverage %s: %s%%' % (key, round(coverage_perc, 2)))


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
    print_coverage(journeys, args.min_edge_usage)


if __name__ == '__main__':
    main()
