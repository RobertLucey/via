import argparse
import json
import random

import osmnx as ox

from bike.models.journey import Journey


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--num',
        dest='num',
        type=int,
        default=5
    )
    parser.add_argument(
        '--place',
        dest='place',
        type=str,
        default='Dublin, Ireland'
    )
    args = parser.parse_args()

    graph = ox.graph_from_place(args.place)

    all_nodes = json.loads(str(graph.nodes))

    for i in range(args.num):
        path = ox.distance.shortest_path(
            graph,
            random.choice(all_nodes),
            random.choice(all_nodes)
        )

        journey = Journey()

        for idx, node in enumerate(path):
            journey.append(
                {
                    'acc': (0, 0, 0),
                    'gps': {
                        'lat': graph._node[node]['y'],
                        'lng': graph._node[node]['x'],
                        'elevation': None
                    },
                    'time': idx * 5
                }
            )

        journey.save()


if __name__ == '__main__':
    main()
