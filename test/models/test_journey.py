import json

import mock

from unittest import TestCase

from bike.settings import (
    MINUTES_TO_CUT,
    EXCLUDE_METRES_BEGIN_AND_END
)
from bike.models.journey import Journey
from bike.models.frame import Frame


class JourneyTest(TestCase):

    def setUp(self):
        with open('test/resources/dublin_route.json') as json_file:
            self.test_data = json.load(json_file)

        self.test_journey = Journey()
        for d in self.test_data:
            self.test_journey.append(
                Frame(
                    d['time'],
                    (d['lat'], d['lng']),
                    ()  # acceleration, don't really care at the mo
                )
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
            [frame.uuid for frame in self.test_journey.frames]
        )

    def test_serialization(self):
        self.assertEqual(
            self.test_journey.serialize()['data'],
            [{'acc': (), 'gps': (53.3588887, -6.2530891), 'time': 0}, {'acc': (), 'gps': (53.3584649, -6.2533216), 'time': 10}, {'acc': (), 'gps': (53.358193, -6.253461), 'time': 20}, {'acc': (), 'gps': (53.3581476, -6.2534842), 'time': 30}, {'acc': (), 'gps': (53.3579793, -6.2526218), 'time': 40}, {'acc': (), 'gps': (53.3579255, -6.2523619), 'time': 50}, {'acc': (), 'gps': (53.3577423, -6.2525459), 'time': 60}, {'acc': (), 'gps': (53.357707, -6.2526408), 'time': 70}, {'acc': (), 'gps': (53.3573489, -6.2536058), 'time': 80}, {'acc': (), 'gps': (53.3572005, -6.2540083), 'time': 90}, {'acc': (), 'gps': (53.3571312, -6.2541836), 'time': 100}, {'acc': (), 'gps': (53.3570936, -6.2542868), 'time': 110}, {'acc': (), 'gps': (53.3569809, -6.2545955), 'time': 120}, {'acc': (), 'gps': (53.3569514, -6.2546764), 'time': 130}, {'acc': (), 'gps': (53.3568576, -6.2549334), 'time': 140}, {'acc': (), 'gps': (53.3564663, -6.2559997), 'time': 150}, {'acc': (), 'gps': (53.3563727, -6.2558978), 'time': 160}, {'acc': (), 'gps': (53.3556449, -6.257938), 'time': 170}, {'acc': (), 'gps': (53.3550156, -6.2574727), 'time': 180}, {'acc': (), 'gps': (53.3549528, -6.2574232), 'time': 190}, {'acc': (), 'gps': (53.35465, -6.257203), 'time': 200}, {'acc': (), 'gps': (53.3541819, -6.2568679), 'time': 210}, {'acc': (), 'gps': (53.3539818, -6.2577681), 'time': 220}, {'acc': (), 'gps': (53.3538836, -6.2581941), 'time': 230}, {'acc': (), 'gps': (53.3538163, -6.2584321), 'time': 240}, {'acc': (), 'gps': (53.3535786, -6.2591722), 'time': 250}, {'acc': (), 'gps': (53.3534972, -6.2594117), 'time': 260}, {'acc': (), 'gps': (53.3533742, -6.259676), 'time': 270}, {'acc': (), 'gps': (53.3531925, -6.2600954), 'time': 280}, {'acc': (), 'gps': (53.3528433, -6.2608812), 'time': 290}, {'acc': (), 'gps': (53.3527764, -6.2610318), 'time': 300}, {'acc': (), 'gps': (53.352555, -6.2613445), 'time': 310}, {'acc': (), 'gps': (53.3519419, -6.2610744), 'time': 320}, {'acc': (), 'gps': (53.3503787, -6.2603792), 'time': 330}, {'acc': (), 'gps': (53.349819, -6.260128), 'time': 340}, {'acc': (), 'gps': (53.3488709, -6.2597226), 'time': 350}, {'acc': (), 'gps': (53.3484455, -6.2595282), 'time': 360}, {'acc': (), 'gps': (53.3483991, -6.2595044), 'time': 370}, {'acc': (), 'gps': (53.3475905, -6.2591013), 'time': 380}, {'acc': (), 'gps': (53.3470086, -6.258792), 'time': 390}, {'acc': (), 'gps': (53.3469351, -6.25911), 'time': 400}, {'acc': (), 'gps': (53.3468825, -6.2593428), 'time': 410}, {'acc': (), 'gps': (53.3467107, -6.2600776), 'time': 420}, {'acc': (), 'gps': (53.3465574, -6.2607335), 'time': 430}, {'acc': (), 'gps': (53.3462881, -6.2618852), 'time': 440}, {'acc': (), 'gps': (53.3461284, -6.2626132), 'time': 450}, {'acc': (), 'gps': (53.3456213, -6.2625161), 'time': 460}, {'acc': (), 'gps': (53.3456018, -6.2628751), 'time': 470}, {'acc': (), 'gps': (53.3448972, -6.2627671), 'time': 480}, {'acc': (), 'gps': (53.3448847, -6.2633611), 'time': 490}, {'acc': (), 'gps': (53.3442105, -6.2633394), 'time': 500}, {'acc': (), 'gps': (53.3441912, -6.26387), 'time': 510}, {'acc': (), 'gps': (53.3441799, -6.2642788), 'time': 520}, {'acc': (), 'gps': (53.3441775, -6.2644509), 'time': 530}, {'acc': (), 'gps': (53.3438399, -6.26444), 'time': 540}, {'acc': (), 'gps': (53.3429968, -6.2644216), 'time': 550}, {'acc': (), 'gps': (53.3421317, -6.2646944), 'time': 560}, {'acc': (), 'gps': (53.3414662, -6.265404), 'time': 570}, {'acc': (), 'gps': (53.3406712, -6.2656141), 'time': 580}, {'acc': (), 'gps': (53.3404613, -6.2656749), 'time': 590}, {'acc': (), 'gps': (53.3398737, -6.2657997), 'time': 600}, {'acc': (), 'gps': (53.3395894, -6.2658639), 'time': 610}, {'acc': (), 'gps': (53.3391577, -6.2659588), 'time': 620}, {'acc': (), 'gps': (53.338532, -6.2661022), 'time': 630}, {'acc': (), 'gps': (53.3383892, -6.2660752), 'time': 640}, {'acc': (), 'gps': (53.3377832, -6.2658551), 'time': 650}, {'acc': (), 'gps': (53.3376138, -6.2657971), 'time': 660}, {'acc': (), 'gps': (53.3374278, -6.2657367), 'time': 670}, {'acc': (), 'gps': (53.3369777, -6.2656096), 'time': 680}, {'acc': (), 'gps': (53.3364281, -6.2654495), 'time': 690}, {'acc': (), 'gps': (53.336174, -6.2653568), 'time': 700}, {'acc': (), 'gps': (53.3354833, -6.2652056), 'time': 710}, {'acc': (), 'gps': (53.3347258, -6.2652546), 'time': 720}, {'acc': (), 'gps': (53.3341412, -6.2652779), 'time': 730}, {'acc': (), 'gps': (53.333871, -6.2651742), 'time': 740}, {'acc': (), 'gps': (53.3337555, -6.265012), 'time': 750}, {'acc': (), 'gps': (53.3335892, -6.2650038), 'time': 760}, {'acc': (), 'gps': (53.332599, -6.2647978), 'time': 770}]
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
            }
        )
        self.assertEqual(
            self.test_journey.serialize()['quality'],
            0.0
        )
        self.assertEqual(
            self.test_journey.serialize()['suspension'],
            True
        )
        self.assertEqual(
            self.test_journey.serialize()['transport_type'],
            'mountain'
        )

    @mock.patch('bike.models.journey.Journey.get_indirect_distance', return_value=1000)
    @mock.patch('bike.models.journey.Journey.duration', 10)
    def test_get_avg_speed(self, mock_get_indirect_distance):
        journey = Journey()
        self.assertEqual(
            journey.get_avg_speed(),
            100
        )

    def test_origin(self):
        self.assertEqual(
            self.test_journey.origin.serialize(),
            {'acc': (), 'gps': (53.3588887, -6.2530891), 'time': 0}
        )

    def test_destination(self):
        self.assertEqual(
            self.test_journey.destination.serialize(),
            {'acc': (), 'gps': (53.332599, -6.2647978), 'time': 770}
        )

    def test_cull_distance(self):
        # TODO: ensure it doesn't cut too much

        origin_frame = self.test_journey.origin
        destination_frame = self.test_journey.destination

        origin_frames = len(self.test_journey.frames)

        self.test_journey.cull_distance()

        self.assertLess(
            len(self.test_journey.frames),
            origin_frames
        )

        for frame in self.test_journey.frames:
            if frame.distance_from_point(origin_frame) < EXCLUDE_METRES_BEGIN_AND_END:
                self.fail()

        for frame in self.test_journey.frames:
            if frame.distance_from_point(destination_frame) < EXCLUDE_METRES_BEGIN_AND_END:
                self.fail()

    def test_cull_time(self):
        # TODO: ensure it doesn't cut too much

        origin_frame = self.test_journey.origin
        destination_frame = self.test_journey.destination

        origin_frames = len(self.test_journey.frames)

        self.test_journey.cull_time(origin_frame.time, destination_frame.time)

        self.assertLess(
            len(self.test_journey.frames),
            origin_frames
        )

        for frame in self.test_journey.frames:
            if frame.time - origin_frame.time < 60 * MINUTES_TO_CUT:
                self.fail()

        for frame in self.test_journey.frames:
            if destination_frame.time - frame.time < 60 * MINUTES_TO_CUT:
                self.fail()

    def test_cull(self):
        # TODO: ensure it doesn't cut too much

        origin_frame = self.test_journey.origin
        destination_frame = self.test_journey.destination

        origin_frames = len(self.test_journey.frames)

        self.test_journey.cull()

        self.assertTrue(self.test_journey.is_culled)

        self.assertLess(
            len(self.test_journey.frames),
            origin_frames
        )

        for frame in self.test_journey.frames:
            if frame.distance_from_point(origin_frame) < EXCLUDE_METRES_BEGIN_AND_END:
                self.fail()

        for frame in self.test_journey.frames:
            if frame.distance_from_point(destination_frame) < EXCLUDE_METRES_BEGIN_AND_END:
                self.fail()

        for frame in self.test_journey.frames:
            if frame.time - origin_frame.time < 60 * MINUTES_TO_CUT:
                self.fail()

        for frame in self.test_journey.frames:
            if destination_frame.time - frame.time < 60 * MINUTES_TO_CUT:
                self.fail()

    def test_duration(self):
        self.assertEqual(
            self.test_journey.duration,
            770
        )

    def test_save_unculled(self):
        with self.assertRaises(Exception):
            self.test_journey.save()

