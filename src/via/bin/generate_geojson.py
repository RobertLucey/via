import argparse
import os
import operator

import fast_json

from via import logger
from via.constants import GEOJSON_DIR
from via.utils import (
    get_journeys,
    should_include_journey
)
from via.models.journeys import Journeys


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--transport-type',
        dest='transport_type',
        default=None,
        help='bike/car/scooter or whatever else is on the app. Generates all if not specified'
    )
    parser.add_argument(
        '--versions',
        dest='versions',
        action='store_true'
    )
    args = parser.parse_args()

    os.makedirs(
        os.path.join(GEOJSON_DIR),
        exist_ok=True
    )

    if args.transport_type in {None, 'all'}:
        config = [
            {'transport_type': 'all', 'name': 'all', 'versions': args.versions},
            {'transport_type': 'bike', 'name': 'bike', 'versions': args.versions},
            {'transport_type': 'car', 'name': 'car', 'versions': args.versions},
            {'transport_type': 'bus', 'name': 'bus', 'versions': args.versions}
        ]
    else:
        config = [
            {'transport_type': args.transport_type, 'name': args.transport_type}
        ]

    for config_item in config:
        logger.info(f'Generating geojson for "{config_item["transport_type"]}"')

        journeys = get_journeys(transport_type=config_item['transport_type'])

        if args.versions:
            versions = set([j.version for j in journeys])

            for version in versions:
                geojson_file = os.path.join(
                    GEOJSON_DIR,
                    f'{config_item["name"]}_ge_{version}.geojson'
                )

                journeys = Journeys(
                    data=[
                        journey for journey in journeys if should_include_journey(
                            journey,
                            version_op=operator.ge,
                            version=version
                        )
                    ]
                )

                with open(geojson_file, 'w') as json_file:
                    fast_json.dump(
                        journeys.geojson,
                        json_file
                    )
        else:
            geojson_file = os.path.join(
                GEOJSON_DIR,
                f'{config_item["name"]}.geojson'
            )

            with open(geojson_file, 'w') as json_file:
                fast_json.dump(
                    journeys.geojson,
                    json_file
                )


if __name__ == '__main__':
    main()
