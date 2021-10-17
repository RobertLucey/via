import argparse
import threading

import bottle
from bottle import response

from via import logger
from via.pull_journeys import pull_journeys

from via.geojson.generate import generate_geojson

from via.api import *
from via.api.info import *
from via.api.journeys import *


class EnableCors(object):
    name = 'enable_cors'
    api = 2

    def apply(self, fn, context):
        def _enable_cors(*args, **kwargs):
            # set CORS headers
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

            if bottle.request.method != 'OPTIONS':
                # actual request; reply with the actual response
                return fn(*args, **kwargs)

        return _enable_cors


def update_journeys():
    logger.info('Pulling journeys')
    pull_journeys()
    threading.Timer(60 * 60, update_journeys).start()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--port',
        dest='port',
        default=8080
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        dest='debug'
    )
    parser.add_argument(
        '--reloader',
        action='store_true',
        dest='reloader'
    )
    args = parser.parse_args()

    update_journeys()
    generate_geojson(
        None,
        version=None
    )

    bottle.debug(args.debug)
    bottle.install(EnableCors())
    bottle.run(
        host='0.0.0.0',
        port=args.port,
        debug=args.debug,
        reloader=args.reloader,
        server='gunicorn'
    )


if __name__ == '__main__':
    main()
