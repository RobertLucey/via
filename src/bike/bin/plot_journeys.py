import argparse

from bike.utils import get_journeys


def main():
    '''
    Plot the map of journeys
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--condition',
        action='store_true',
        dest='condition',
        help='Show the condition of the roads'
    )
    parser.add_argument(
        '--closest-edge',
        action='store_true',
        dest='closest_edge',
        help='Use the closest route to the coordinates plotted on the actual journey. If no, similar journeys are not likely to overlap'
    )
    args = parser.parse_args()

    journeys = get_journeys()
    journeys.plot_routes(
        use_closest_edge_from_base=args.closest_edge,
        apply_condition_colour=args.condition,
        plot_kwargs={
            'bgcolor': 'w',
            'edge_linewidth': 5,
            'show': True
        }
    )


if __name__ == '__main__':
    main()
