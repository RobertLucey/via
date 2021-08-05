import mock

from unittest import TestCase

from bike.models.accelerometer import AccelerometerPoint


class MockIC2():

    def __init__(self):
        pass


class MockBoard():

    def __init__(self):
        self.TX = 0
        self.RX = 1
        self.IC2 = MockIC2()


class MockInterface():

    def __init__(self):
        pass

    @property
    def acceleration(self):
        return (0, 1, 2)


class AcceleratorTest(TestCase):

    @mock.patch('bike.acceleration.AccelerometerInterface.get_interface', return_value=MockInterface())
    @mock.patch('bike.utils.get_board', return_value=MockBoard())
    def test_get_lat_lng(self, mock_get_board, mock_get_interface):
        from bike.acceleration import AccelerometerInterface
        interface = AccelerometerInterface()
        lat_lng = interface.get_acceleration()
        self.assertIsInstance(
            lat_lng,
            AccelerometerPoint
        )
