# Bike

Road quality assessment from cycling around, tools to analyse data from https://github.com/RobertLucey/road-quality-aggregator

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

Might want to split these into their own commands at some point

```
usage: stats.py [-h] [--min-edge-usage MIN_EDGE_USAGE] [--coverage]
                [--condition-by-street] [--place PLACE]

optional arguments:
  -h, --help            show this help message and exit
  --min-edge-usage MIN_EDGE_USAGE
                        The minimum number of times an edge has to be used for
                        it to be included in the final data (1 per journey)
  --coverage            Get the coverage by length of the bounding box, to see
                        what that box is and a visual represenation of the
                        routes use plot_journeys
  --condition-by-street
                        List the condition by the street name
  --place PLACE         What place to limit the data to (so you don't try to
                        visualize too big an area). Must be an osmnx
                        recognised place / format for example "Dublin,
                        Ireland"
```
