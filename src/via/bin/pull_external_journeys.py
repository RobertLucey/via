import requests
from urllib.parse import urlencode
from collections import OrderedDict

from via.utils import get_mongo_interface
from via.settings import MONGO_RAW_JOURNEYS_COLLECTION


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
            query_url = f'{url}?{query_string}'

            print(query_url)

            data = requests.get(query_url).json()

            page += 1

            if not data:
                still_has_data = False
            else:
                for d in data:

                    # TODO: validate the data

                    db = get_mongo_interface()
                    result = getattr(db, MONGO_RAW_JOURNEYS_COLLECTION).find_one({"uuid": d['uuid']})

                    if not result:
                        getattr(db, MONGO_RAW_JOURNEYS_COLLECTION).insert_one(d)
                    else:
                        print(f'already exists: {d["uuid"]}')


if __name__ == "__main__":
    main()
