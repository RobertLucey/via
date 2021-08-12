from setuptools import (
    find_packages,
    setup
)

INSTALL_REQUIRES = (
    'reverse_geocoder',
    'fast_json',
    'boto3',
    'backoff',
    'adafruit-circuitpython-gps',
    'haversine',
    'adafruit-circuitpython-lis331',
    'osmnx',
    'scikit-learn',
    'requests',
    'geopandas'
)

setup(
    name='bike',
    version='0.0.1',
    python_requires='>=3.6',
    description='Bike',
    author='Robert Lucey',
    url='https://github.com/RobertLucey/bike',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=INSTALL_REQUIRES,
    entry_points={
        'console_scripts': [
            'pull_journeys = bike.bin.pull_journeys:main'
        ]
    }
)
