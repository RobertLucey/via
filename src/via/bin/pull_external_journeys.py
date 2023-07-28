from urllib.parse import urlencode
from collections import OrderedDict

import requests

from via.utils import get_mongo_interface
from via.settings import MONGO_RAW_JOURNEYS_COLLECTION
from via.models.journey import Journey


URLS = [
    #'http://localhost:8000/get_raw_journeys'
]


def main():
    for url in URLS:
        page = 1
        page_size = 5
        still_has_data = True

        while still_has_data:
            query_string = urlencode(OrderedDict(page=page, page_size=page_size))
            query_url = f"{url}?{query_string}"

            print(query_url)

            journeys_data = requests.get(query_url).json()

            page += 1

            if not journeys_data:
                still_has_data = False
            else:
                for journey_data in journeys_data:
                    # validate the journey
                    Journey(
                        data=journeys_data,
                        is_culled=True,
                        transport_type=journey_data["transport_type"],
                        suspension=journey_data["suspension"],
                        version=journey_data["version"],
                    )

                    mongo_interface = get_mongo_interface()
                    result = getattr(
                        mongo_interface, MONGO_RAW_JOURNEYS_COLLECTION
                    ).find_one({"uuid": journey_data["uuid"]})

                    if not result:
                        getattr(
                            mongo_interface, MONGO_RAW_JOURNEYS_COLLECTION
                        ).insert_one(journey_data)
                    else:
                        print(f'already exists: {journey_data["uuid"]}')


if __name__ == "__main__":
    main()
