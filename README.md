# Bike

[![Build Status](https://travis-ci.com/RobertLucey/bike.svg?branch=master)](https://travis-ci.com/RobertLucey/mauve)

Main intention for road quality assessment from cycling around but can also be used for finding interesting statistics about travel habits

I'll put a parts list and an installer together but until I have the hardware all together and tested out this is all up in the air and probably doesn't work

Also I'm going to rename this at some point for obvious reasons

## Features

- Cuts off the first and last 5 minutes (configurable) from your ride so nobody knows where you're coming and going to by sharing your ride info
	- Additionally it cuts first x metres and last x metres. Whichever happens last, time or distance for the start or end takes effect
- Doesn't store the actual time of day, only relative time from the start of the turning on of the device
- Local analysis tools so you don't need to upload your journeys if you don't want to

## Requirements

TODO: Need to make sure the parts work once they arrive

## Installation

TODO: Make an image but also install a guide because people shouldn't random img files

## Usage

### Installation

TODO: What pins go where, installing the deb / flash / whatever

### Scripting

To get a quick start into playing with journeys you can use one of the test resource journeys. I'll put up an actual one once I get hardware delivered

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



## Future

- Build an image so can handily install
- Configure wifi so files uploaded when home without having to do anything
- Some sort of backend to upload journeys to / visualize problematic areas
- Visualization / Stats over multiple journeys
