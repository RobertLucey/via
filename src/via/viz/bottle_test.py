from via.viz.dummy_data import full_journey
import bottle


@bottle.route('/hello')
def hello():
    return "Hello!!"


@bottle.route('/')
@bottle.route('/hello/<name>')
def greet(name='Stranger'):
    return bottle.template('Hello {{name}}, how are you??', name=name)


@bottle.route('/static/:filename#.*#')
def send_static(filename):
    return bottle.static_file(filename, root='static/')


@bottle.route('/pull_journeys')
def pull_journeys():
    print("Pulling journeys")

    earliest_time = bottle.request.query.earliest_time
    latest_time = bottle.request.query.latest_time
    journey_type = bottle.request.query.journey_type
    limit = bottle.request.query.limit

    return {
        'req': {
            'earliest_time': earliest_time,
            'latest_time': latest_time,
            'journey_type': journey_type,
            'limit': limit
        },
        'resp': {
            'geojson': full_journey
        },
        'status': 'sure'
    }


@bottle.route('/')
def send_index():
    return send_static('index.html')


bottle.debug(True)
bottle.run(host="localhost", port=8080, debug=True, reloader=True)
