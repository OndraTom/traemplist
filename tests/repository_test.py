import shutil
from unittest import TestCase
from tempfile import mkdtemp
from traemplist.repository import TrackRecord, SqLiteTracksRepository


class SqLiteTracksRepositoryTest(TestCase):

    def setUp(self) -> None:
        self.tmp_dir = mkdtemp()
        self.repository = SqLiteTracksRepository(self.tmp_dir + "/test.db")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_save_and_contains(self):
        track_a = TrackRecord(id="a")
        track_b = TrackRecord(id="b")
        self.repository.save_tracks([track_a])
        self.repository.save_tracks([track_b])
        self.assertTrue(self.repository.contains_track(track_id=track_a.id))
        self.assertTrue(self.repository.contains_track(track_id=track_b.id))
        self.assertFalse(self.repository.contains_track(track_id="c"))

    def test_double_insert(self):
        track_a = TrackRecord(id="a")
        self.repository.save_tracks([track_a])
        self.repository.save_tracks([track_a])
        self.assertTrue(self.repository.contains_track(track_id=track_a.id))
