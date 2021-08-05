import mock

from unittest import TestCase

from bike.models.gps import GPSPoint


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

    def send_command(self, *args, **kwargs):
        pass

    def update(self):
        pass

    def has_fix(self):
        return True

    def latitude(self):
        return 0.1

    def longitude(self):
        return 0.2


class GPSTest(TestCase):

    @mock.patch('bike.gps.GPSInterface.get_interface', return_value=MockInterface())
    @mock.patch('bike.utils.get_board', return_value=MockBoard())
    def test_get_lat_lng(self, mock_get_board, mock_get_interface):
        from bike.gps import GPSInterface
        interface = GPSInterface()
        lat_lng = interface.get_lat_lng()
        self.assertIsInstance(
            lat_lng,
            GPSPoint
        )
