from setuptools import (
    find_packages,
    setup
)

INSTALL_REQUIRES = (
    'adafruit-circuitpython-gps',
    'haversine',
    'adafruit-circuitpython-lis331',
    'osmnx',
    'scikit-learn',
    'requests'
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
            'start_bike = bike.bin.client'
        ]
    }
)
