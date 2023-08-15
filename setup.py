from setuptools import (
    find_packages,
    setup
)

INSTALL_REQUIRES = (
    'cached_property',
    'packaging',
    'reverse_geocoder',
    'haversine',
    'osmnx',
    'requests',
    'geopandas',
    'python-logging-loki',
    'fastapi[all]',
    'pydantic',
    'pymongo',
    'cachetools',
    'mappymatch'
)

setup(
    name='via-api',
    version='2.7.0',
    python_requires='>=3.6',
    description='Analysing and serving crowdsourced road quality data',
    long_description='Analysing and serving crowdsourced road quality data',
    author='Robert Lucey',
    url='https://github.com/RobertLucey/via',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=INSTALL_REQUIRES,
    entry_points={
        'console_scripts': [
            'via_pull_journeys = via.bin.pull_external_journeys:main',
            'via_generate_geojson = via.bin.generate_geojson:main',
            'via_backup_raw_journeys = via.bin.backup_raw_journeys:main'
        ]
    }
)
