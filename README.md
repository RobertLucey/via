# Bike

Road quality assessment from cycling around, tools to analyse data collected from the android app https://github.com/RobertLucey/road-quality-aggregator

All uploaded data is public and no accounts required. Neat privacy to make it very difficult / impossible (depending on your settings and how many trips have been taken in the area) to find the route of an individual journey as well as its origin / destination

Also I'm going to rename this at some point for obvious reasons

## Usage

To get a quick start into playing with journeys you can use one of the test resource journeys. I'll put up an actual one once I get hardware delivered
Run `pull_journeys` before doing anything to make sure you have some data to work with.

### Plot the road quality of a city

I would like to get the `--min-edge-usage` from stats into this now that I think about it

```
usage: plot_journeys.py [-h] [--condition] [--closest-edge] [--place PLACE]

optional arguments:
  -h, --help      show this help message and exit
  --condition     Show the condition of the roads, otherwise just plot the
                  paths
  --closest-edge  Use the closest route to the coordinates plotted on the
                  actual journey. If no, similar journeys are not likely to
                  overlap
  --place PLACE   What place to limit the data to (so you don't try to
                  visualize too big an area). Must be an osmnx recognised
                  place / format for example "Dublin, Ireland"
```

### Get some stats of journeys

### Road Coverage

This will give a % of how much of the roads there is data of. You can make sure that there are at least 10 points of info for a road to be counted as having sufficient data to be counted

```
usage: road_coverage.py [-h] [--min-edge-usage MIN_EDGE_USAGE] [--place PLACE]

optional arguments:
  -h, --help            show this help message and exit
  --min-edge-usage MIN_EDGE_USAGE
                        The minimum number of times an edge has to be used for
                        it to be included in the final data (1 per journey)
  --place PLACE         What place to limit the data to (so you don't try to
                        visualize too big an area). Must be an osmnx
                        recognised place / format for example "Dublin,
                        Ireland"
```

### Condition by Street

Get a list of the worst roads and their values

```
usage: condition_by_street.py [-h] [--min-edge-usage MIN_EDGE_USAGE]
                              [--place PLACE]

optional arguments:
  -h, --help            show this help message and exit
  --min-edge-usage MIN_EDGE_USAGE
                        The minimum number of times an edge has to be used for
                        it to be included in the final data (1 per journey)
  --place PLACE         What place to limit the data to (so you don't try to
                        visualize too big an area). Must be an osmnx
                        recognised place / format for example "Dublin,
                        Ireland"
```
