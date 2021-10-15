from setuptools import (
    find_packages,
    setup
)

INSTALL_REQUIRES = (
    'cached_property',
    'backoff',
    'packaging',
    'reverse_geocoder',
    'fast_json',
    'boto3',
    'backoff',
    'haversine',
    'osmnx',
    'scikit-learn',
    'requests',
    'geopandas',
    'imagehash',
    'pillow',
    'bottle'
)

setup(
    name='via-api',
    version='0.0.2',
    python_requires='>=3.6',
    description='Analysing and serving crowdsourced road quality data',
    author='Robert Lucey',
    url='https://github.com/RobertLucey/via',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=INSTALL_REQUIRES,
    entry_points={
        'console_scripts': [
            'pull_journeys = via.bin.pull_journeys:main',
            'plot_journeys = via.bin.plot_journeys:main',
            'road_coverage = via.bin.road_coverage:main',
            'condition_by_street = via.bin.condition_by_street:main',
            'generate_geojson = via.bin.generate_geojson:main',
            'via_bottle = via.bin.bottle_entry:main'
        ]
    }
)
