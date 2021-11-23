import json

from mock import patch
from unittest import TestCase, skip

from via.models.journey import Journey
from via.models.frame import Frame


class JourneyTest(TestCase):

    @patch('via.settings.MIN_METRES_PER_SECOND', 0)
    @patch('via.settings.GPS_INCLUDE_RATIO', 1)
    def setUp(self):
        with open('test/resources/just_route.json') as json_file:
            self.test_data = json.load(json_file)

        self.test_journey = Journey()
        for d in self.test_data:
            self.test_journey.append(
                Frame(
                    d['time'],
                    {'lat': d['lat'], 'lng': d['lng']},
                    1  # acceleration, don't really care at the mo
                )
            )

    def test_set_contexts(self):
        self.assertEqual(
            [i.is_context_populated for i in self.test_journey],
            [False, False, False, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False]
        )

    def test_route_graph(self):
        graph_coordinates = []
        for frame_uuid, frame_data in self.test_journey.route_graph._node.items():
            graph_coordinates.append(
                {
                    'lat': frame_data['y'],
                    'lng': frame_data['x']
                }
            )

        data_no_time = [{'lat': d['lat'], 'lng': d['lng']} for d in self.test_data]

        self.assertEqual(graph_coordinates, data_no_time)

        self.assertEqual(
            list(self.test_journey.route_graph._node.keys()),
            [frame.uuid for frame in self.test_journey]
        )

    def test_serialization(self):
        self.assertEqual(
            self.test_journey.serialize(include_context=False)['data'],
            [{'gps': {'lat': 53.3588887, 'lng': -6.2530891, 'elevation': None}, 'acc': [1], 'time': 0}, {'gps': {'lat': 53.3584649, 'lng': -6.2533216, 'elevation': None}, 'acc': [1], 'time': 10}, {'gps': {'lat': 53.358193, 'lng': -6.253461, 'elevation': None}, 'acc': [1], 'time': 20}, {'gps': {'lat': 53.3581476, 'lng': -6.2534842, 'elevation': None}, 'acc': [1], 'time': 30}, {'gps': {'lat': 53.3579793, 'lng': -6.2526218, 'elevation': None}, 'acc': [1], 'time': 40}, {'gps': {'lat': 53.3579255, 'lng': -6.2523619, 'elevation': None}, 'acc': [1], 'time': 50}, {'gps': {'lat': 53.3577423, 'lng': -6.2525459, 'elevation': None}, 'acc': [1], 'time': 60}, {'gps': {'lat': 53.357707, 'lng': -6.2526408, 'elevation': None}, 'acc': [1], 'time': 70}, {'gps': {'lat': 53.3573489, 'lng': -6.2536058, 'elevation': None}, 'acc': [1], 'time': 80}, {'gps': {'lat': 53.3572005, 'lng': -6.2540083, 'elevation': None}, 'acc': [1], 'time': 90}, {'gps': {'lat': 53.3571312, 'lng': -6.2541836, 'elevation': None}, 'acc': [1], 'time': 100}, {'gps': {'lat': 53.3570936, 'lng': -6.2542868, 'elevation': None}, 'acc': [1], 'time': 110}, {'gps': {'lat': 53.3569809, 'lng': -6.2545955, 'elevation': None}, 'acc': [1], 'time': 120}, {'gps': {'lat': 53.3569514, 'lng': -6.2546764, 'elevation': None}, 'acc': [1], 'time': 130}, {'gps': {'lat': 53.3568576, 'lng': -6.2549334, 'elevation': None}, 'acc': [1], 'time': 140}, {'gps': {'lat': 53.3564663, 'lng': -6.2559997, 'elevation': None}, 'acc': [1], 'time': 150}, {'gps': {'lat': 53.3563727, 'lng': -6.2558978, 'elevation': None}, 'acc': [1], 'time': 160}, {'gps': {'lat': 53.3556449, 'lng': -6.257938, 'elevation': None}, 'acc': [1], 'time': 170}, {'gps': {'lat': 53.3550156, 'lng': -6.2574727, 'elevation': None}, 'acc': [1], 'time': 180}, {'gps': {'lat': 53.3549528, 'lng': -6.2574232, 'elevation': None}, 'acc': [1], 'time': 190}, {'gps': {'lat': 53.35465, 'lng': -6.257203, 'elevation': None}, 'acc': [1], 'time': 200}, {'gps': {'lat': 53.3541819, 'lng': -6.2568679, 'elevation': None}, 'acc': [1], 'time': 210}, {'gps': {'lat': 53.3539818, 'lng': -6.2577681, 'elevation': None}, 'acc': [1], 'time': 220}, {'gps': {'lat': 53.3538836, 'lng': -6.2581941, 'elevation': None}, 'acc': [1], 'time': 230}, {'gps': {'lat': 53.3538163, 'lng': -6.2584321, 'elevation': None}, 'acc': [1], 'time': 240}, {'gps': {'lat': 53.3535786, 'lng': -6.2591722, 'elevation': None}, 'acc': [1], 'time': 250}, {'gps': {'lat': 53.3534972, 'lng': -6.2594117, 'elevation': None}, 'acc': [1], 'time': 260}, {'gps': {'lat': 53.3533742, 'lng': -6.259676, 'elevation': None}, 'acc': [1], 'time': 270}, {'gps': {'lat': 53.3531925, 'lng': -6.2600954, 'elevation': None}, 'acc': [1], 'time': 280}, {'gps': {'lat': 53.3528433, 'lng': -6.2608812, 'elevation': None}, 'acc': [1], 'time': 290}, {'gps': {'lat': 53.3527764, 'lng': -6.2610318, 'elevation': None}, 'acc': [1], 'time': 300}, {'gps': {'lat': 53.352555, 'lng': -6.2613445, 'elevation': None}, 'acc': [1], 'time': 310}, {'gps': {'lat': 53.3519419, 'lng': -6.2610744, 'elevation': None}, 'acc': [1], 'time': 320}, {'gps': {'lat': 53.3503787, 'lng': -6.2603792, 'elevation': None}, 'acc': [1], 'time': 330}, {'gps': {'lat': 53.349819, 'lng': -6.260128, 'elevation': None}, 'acc': [1], 'time': 340}, {'gps': {'lat': 53.3488709, 'lng': -6.2597226, 'elevation': None}, 'acc': [1], 'time': 350}, {'gps': {'lat': 53.3484455, 'lng': -6.2595282, 'elevation': None}, 'acc': [1], 'time': 360}, {'gps': {'lat': 53.3483991, 'lng': -6.2595044, 'elevation': None}, 'acc': [1], 'time': 370}, {'gps': {'lat': 53.3475905, 'lng': -6.2591013, 'elevation': None}, 'acc': [1], 'time': 380}, {'gps': {'lat': 53.3470086, 'lng': -6.258792, 'elevation': None}, 'acc': [1], 'time': 390}, {'gps': {'lat': 53.3469351, 'lng': -6.25911, 'elevation': None}, 'acc': [1], 'time': 400}, {'gps': {'lat': 53.3468825, 'lng': -6.2593428, 'elevation': None}, 'acc': [1], 'time': 410}, {'gps': {'lat': 53.3467107, 'lng': -6.2600776, 'elevation': None}, 'acc': [1], 'time': 420}, {'gps': {'lat': 53.3465574, 'lng': -6.2607335, 'elevation': None}, 'acc': [1], 'time': 430}, {'gps': {'lat': 53.3462881, 'lng': -6.2618852, 'elevation': None}, 'acc': [1], 'time': 440}, {'gps': {'lat': 53.3461284, 'lng': -6.2626132, 'elevation': None}, 'acc': [1], 'time': 450}, {'gps': {'lat': 53.3456213, 'lng': -6.2625161, 'elevation': None}, 'acc': [1], 'time': 460}, {'gps': {'lat': 53.3456018, 'lng': -6.2628751, 'elevation': None}, 'acc': [1], 'time': 470}, {'gps': {'lat': 53.3448972, 'lng': -6.2627671, 'elevation': None}, 'acc': [1], 'time': 480}, {'gps': {'lat': 53.3448847, 'lng': -6.2633611, 'elevation': None}, 'acc': [1], 'time': 490}, {'gps': {'lat': 53.3442105, 'lng': -6.2633394, 'elevation': None}, 'acc': [1], 'time': 500}, {'gps': {'lat': 53.3441912, 'lng': -6.26387, 'elevation': None}, 'acc': [1], 'time': 510}, {'gps': {'lat': 53.3441799, 'lng': -6.2642788, 'elevation': None}, 'acc': [1], 'time': 520}, {'gps': {'lat': 53.3441775, 'lng': -6.2644509, 'elevation': None}, 'acc': [1], 'time': 530}, {'gps': {'lat': 53.3438399, 'lng': -6.26444, 'elevation': None}, 'acc': [1], 'time': 540}, {'gps': {'lat': 53.3429968, 'lng': -6.2644216, 'elevation': None}, 'acc': [1], 'time': 550}, {'gps': {'lat': 53.3421317, 'lng': -6.2646944, 'elevation': None}, 'acc': [1], 'time': 560}, {'gps': {'lat': 53.3414662, 'lng': -6.265404, 'elevation': None}, 'acc': [1], 'time': 570}, {'gps': {'lat': 53.3406712, 'lng': -6.2656141, 'elevation': None}, 'acc': [1], 'time': 580}, {'gps': {'lat': 53.3404613, 'lng': -6.2656749, 'elevation': None}, 'acc': [1], 'time': 590}, {'gps': {'lat': 53.3398737, 'lng': -6.2657997, 'elevation': None}, 'acc': [1], 'time': 600}, {'gps': {'lat': 53.3395894, 'lng': -6.2658639, 'elevation': None}, 'acc': [1], 'time': 610}, {'gps': {'lat': 53.3391577, 'lng': -6.2659588, 'elevation': None}, 'acc': [1], 'time': 620}, {'gps': {'lat': 53.338532, 'lng': -6.2661022, 'elevation': None}, 'acc': [1], 'time': 630}, {'gps': {'lat': 53.3383892, 'lng': -6.2660752, 'elevation': None}, 'acc': [1], 'time': 640}, {'gps': {'lat': 53.3377832, 'lng': -6.2658551, 'elevation': None}, 'acc': [1], 'time': 650}, {'gps': {'lat': 53.3376138, 'lng': -6.2657971, 'elevation': None}, 'acc': [1], 'time': 660}, {'gps': {'lat': 53.3374278, 'lng': -6.2657367, 'elevation': None}, 'acc': [1], 'time': 670}, {'gps': {'lat': 53.3369777, 'lng': -6.2656096, 'elevation': None}, 'acc': [1], 'time': 680}, {'gps': {'lat': 53.3364281, 'lng': -6.2654495, 'elevation': None}, 'acc': [1], 'time': 690}, {'gps': {'lat': 53.336174, 'lng': -6.2653568, 'elevation': None}, 'acc': [1], 'time': 700}, {'gps': {'lat': 53.3354833, 'lng': -6.2652056, 'elevation': None}, 'acc': [1], 'time': 710}, {'gps': {'lat': 53.3347258, 'lng': -6.2652546, 'elevation': None}, 'acc': [1], 'time': 720}, {'gps': {'lat': 53.3341412, 'lng': -6.2652779, 'elevation': None}, 'acc': [1], 'time': 730}, {'gps': {'lat': 53.333871, 'lng': -6.2651742, 'elevation': None}, 'acc': [1], 'time': 740}, {'gps': {'lat': 53.3337555, 'lng': -6.265012, 'elevation': None}, 'acc': [1], 'time': 750}, {'gps': {'lat': 53.3335892, 'lng': -6.2650038, 'elevation': None}, 'acc': [1], 'time': 760}, {'gps': {'lat': 53.332599, 'lng': -6.2647978, 'elevation': None}, 'acc': [1], 'time': 770}]
        )
        self.assertEqual(
            self.test_journey.serialize()['direct_distance'],
            3024.84802816048
        )
        self.assertEqual(
            self.test_journey.serialize()['duration'],
            770
        )
        self.assertEqual(
            self.test_journey.serialize()['indirect_distance'],
            {
                1: 3734.354622435669,
                5: 3734.354622435669,
                10: 3734.354622435669,
                30: 3410.250751428646
            }
        )
        #self.assertEqual(
        #    self.test_journey.serialize()['data_quality'],
        #    0.0
        #)

    @patch('via.models.journey.Journey.get_indirect_distance', return_value=1000)
    @patch('via.models.journey.Journey.duration', 10)
    def test_get_avg_speed(self, mock_get_indirect_distance):
        journey = Journey()
        self.assertEqual(
            journey.get_avg_speed(),
            100
        )

    def test_origin(self):
        self.assertEqual(
            self.test_journey.origin.serialize(),
            {'acc': [1], 'gps': {'lat': 53.3588887, 'lng': -6.2530891, 'elevation': None}, 'time': 0, 'context': {'pre': [], 'post': []}}
        )

    def test_destination(self):
        self.assertEqual(
            self.test_journey.destination.serialize(),
            {'acc': [1], 'gps': {'lat': 53.332599, 'lng': -6.2647978, 'elevation': None}, 'time': 770, 'context': {'pre': [], 'post': []}}
        )

    def test_duration(self):
        self.assertEqual(
            self.test_journey.duration,
            770
        )

    @patch('via.settings.MIN_METRES_PER_SECOND', 0)
    @patch('via.settings.GPS_INCLUDE_RATIO', 1)
    def test_parse(self):
        self.assertEqual(
            Journey.parse(self.test_journey).serialize(),
            self.test_journey.serialize()
        )

        self.assertEqual(
            Journey.parse(self.test_journey.serialize()).serialize(),
            self.test_journey.serialize()
        )

        with self.assertRaises(NotImplementedError):
            Journey.parse(None)

    @skip('todo')
    def test_edge_quality_map(self):
        # TODO: need to have real data / not random data for the road quality
        pass

    @patch('via.settings.MIN_METRES_PER_SECOND', 0)
    @patch('via.settings.GPS_INCLUDE_RATIO', 1)
    def test_toggle_gps_acc(self):
        """
        If I don't sort out the phone thing cause I don't want to this should
        make up for it
        """
        test_data = [
            {'time': 0, 'acc': 1, 'gps': {'lat': None, 'lng': None}},
            {'time': 1, 'acc': 1, 'gps': {'lat': None, 'lng': None}},
            {'time': 2, 'acc': None, 'gps': {'lat': 1, 'lng': 2}},
            {'time': 3, 'acc': 1, 'gps': {'lat': None, 'lng': None}},
            {'time': 4, 'acc': 1, 'gps': {'lat': None, 'lng': None}},
            {'time': 5, 'acc': 1, 'gps': {'lat': None, 'lng': None}},
            {'time': 6, 'acc': 1, 'gps': {'lat': None, 'lng': None}},
            {'time': 7, 'acc': None, 'gps': {'lat': 1.1, 'lng': 2.2}},
        ]

        journey = Journey()
        for dp in test_data:
            journey.append(dp)

        print(journey.serialize())
        self.assertEqual(
            journey.serialize(),
            {
                'version': '0.0.0',
                'uuid': str(journey.uuid),
                'data': [
                    {'gps': {'lat': 1, 'lng': 2, 'elevation': None}, 'acc': [1, 1, 1, 1], 'time': 2, 'context': {'pre': [], 'post': []}},
                    {'gps': {'lat': 1.1, 'lng': 2.2, 'elevation': None}, 'acc': [], 'time': 7, 'context': {'pre': [], 'post': []}}
                ],
                'transport_type': 'unknown',
                'suspension': None,
                'is_culled': False,
                'is_sent': False,
                'direct_distance': 24860.633301979688,
                'indirect_distance': {
                    1: 24860.633301979688,
                    5: 24860.633301979688,
                    10: 0,
                    30: 0
                },
                'data_quality': 1,  # TODO
                'duration': 5,
                'avg_speed': 0.0
            }
        )

    def test_country(self):
        self.assertEqual(self.test_journey.country, 'IE')
