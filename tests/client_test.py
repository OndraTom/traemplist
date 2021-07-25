from unittest import TestCase
from traemplist.client import Track, TracksCollection


class TracksCollectionTest(TestCase):

    def test_tracks_adding(self):
        collection = TracksCollection()
        self.assertEqual(collection.get_tracks(), set())
        track_a = Track(id="a", name="a")
        track_b = Track(id="b", name="b")
        track_c = Track(id="c", name="c")
        track_d = Track(id="d", name="d")
        collection.add_track(track_a)
        collection.add_track(track_b)
        self.assertEqual(collection.get_tracks(), {track_a, track_b})
        self.assertTrue(track_a in collection)
        self.assertFalse(track_c in collection)
        collection.add_tracks(
            TracksCollection().add_track(track_c).add_track(track_d)
        )
        self.assertEqual(
            collection.get_tracks(),
            {track_a, track_b, track_c, track_d}
        )
