import os

import fast_json

from via.constants import GEOJSON_DIR
from via.utils import get_journeys


def main():

    os.makedirs(
        os.path.join(GEOJSON_DIR),
        exist_ok=True
    )

    config = [
        {'transport_type': None, 'name': 'all'},
        {'transport_type': 'bike', 'name': 'bike'},
        {'transport_type': 'car', 'name': 'car'},
        {'transport_type': 'bus', 'name': 'bus'}
    ]
    for config_item in config:
        geojson_file = os.path.join(
            GEOJSON_DIR,
            f'{config_item["name"]}.geojson'
        )

        journeys = get_journeys(transport_type=config_item['transport_type'])
        with open(geojson_file, 'w') as json_file:
            fast_json.dump(
                journeys.geojson,
                json_file,
                indent=4
            )


if __name__ == '__main__':
    main()