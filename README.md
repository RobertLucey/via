# Bike

Road quality assessment from cycling around, tools to analyse data from https://github.com/RobertLucey/road-quality-aggregator

Also I'm going to rename this at some point for obvious reasons

## Usage

To get a quick start into playing with journeys you can use one of the test resource journeys. I'll put up an actual one once I get hardware delivered

Run `pull_journeys` before doing anything to make sure you have some data to work with.

```{python}
from bike.models.journey import Journey

sample_journey = Journey.from_file('test/resources/abc46949-7f23-474f-bf7c-e313f3c74e5d.json')
print(sample_journey.serialize())  # Show some details of the journey
sample_journey.plot_route()  # Show the route on a map
```

Here's how to show the road conditions on a map, aggregating all journeys

```{python}
from bike.utils import get_journeys

journeys = get_journeys()
journeys.plot_routes(
    use_closest_edge_from_base=True,
    apply_condition_colour=True,
    plot_kwargs={
        'bgcolor': 'w',
        'edge_linewidth': 5,
        'show': True
    }
)
```
