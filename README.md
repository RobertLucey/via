# Via

<img src="/assets/logo.png" alt="via logo" style="height: 100px; width:100px;"/>

Road quality assessment from cycling / driving / bussing around, tools to analyse data collected from the android app https://github.com/RobertLucey/road-quality-aggregator

All uploaded data is public and no accounts required. Neat privacy to make it very difficult / impossible (depending on your settings and how many trips have been taken in the area) to find the route of an individual journey as well as its origin / destination

## Usage

To get a quick start into playing with journeys you can use one of the test resource journeys. I'll put up an actual one once I get hardware delivered
Run `pull_journeys` before doing anything to make sure you have some data to work with.

### Plot the road quality of a city

```
usage: plot_journeys.py [-h] [--closest-edge]
                        [--transport-type TRANSPORT_TYPE] [--place PLACE]
                        [--min-edge-usage MIN_EDGE_USAGE]

optional arguments:
  -h, --help            show this help message and exit
  --closest-edge        Use the closest route to the coordinates plotted on
                        the actual journey. If no, similar journeys are not
                        likely to overlap
  --transport-type TRANSPORT_TYPE
                        bike/car/scoorter or whatever else is on the app
  --place PLACE         What place to limit the data to (so you don't try to
                        visualize too big an area). Must be an osmnx
                        recognised place / format for example "Dublin,
                        Ireland"
  --min-edge-usage MIN_EDGE_USAGE
                        The minimum number of times an edge has to be used for
                        it to be included in the final data (1 per journey)
```

### Generate geojson files

```
usage: generate_geojson.py [-h] [--transport-type TRANSPORT_TYPE]

optional arguments:
  -h, --help            show this help message and exit
  --transport-type TRANSPORT_TYPE
                        bike/car/scooter or whatever else is on the app.
                        Generates all if not specified
```

### Get some stats of journeys


### Condition by Street

Get a list of the worst roads and their values

```
usage: condition_by_street.py [-h] [--min-edge-usage MIN_EDGE_USAGE]
                              [--transport-type TRANSPORT_TYPE]
                              [--place PLACE]

optional arguments:
  -h, --help            show this help message and exit
  --min-edge-usage MIN_EDGE_USAGE
                        The minimum number of times an edge has to be used for
                        it to be included in the final data (1 per journey)
  --transport-type TRANSPORT_TYPE
                        bike/car/scoorter or whatever else is on the app
  --place PLACE         What place to limit the data to (so you don't try to
                        visualize too big an area). Must be an osmnx
                        recognised place / format for example "Dublin,
                        Ireland"
```

### Docker

A web interface has been Dockerized and is available [here](https://hub.docker.com/repository/docker/conorjf/via-web).
The easiest way to run locally is to use the available `docker-compose` file.
Note that you will need some AWS credentials to pass to this. These should be
placed in a `.env` file in the same working directory as `docker-compose.yaml`
as follows:

```
AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXXX
```
