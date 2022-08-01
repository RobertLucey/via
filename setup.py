from setuptools import (
    find_packages,
    setup
)

INSTALL_REQUIRES = (
    'road-collisions-ireland>=0.0.9',
    'cached_property',
    'packaging',
    'reverse_geocoder',
    'fast_json',
    'boto3',
    'haversine',
    'osmnx',
    'scikit-learn',
    'requests',
    'geopandas',
    'python-logging-loki'
)

setup(
    name='via-api',
    version='1.0.0',
    python_requires='>=3.6,<3.10',
    description='Analysing and serving crowdsourced road quality data',
    long_description='Analysing and serving crowdsourced road quality data',
    author='Robert Lucey',
    url='https://github.com/RobertLucey/via',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=INSTALL_REQUIRES,
    entry_points={
        'console_scripts': [
            'pull_journeys = via.bin.pull_journeys:main',
            'generate_geojson = via.bin.generate_geojson:main',
            'generate_collision_geojson = via.bin.generate_collision_geojson:main'
        ]
    }
)
