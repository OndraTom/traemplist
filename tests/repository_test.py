import shutil
from unittest import TestCase, SkipTest
from tempfile import mkdtemp
from traemplist.repository import TrackRecord, TracksRepository, SqLiteTracksRepository, InMemoryTracksRepository


class TracksRepositoryAbstractTest(TestCase):

    def setUp(self) -> None:
        if isinstance(self, TracksRepositoryAbstractTest):
            raise SkipTest
        self.repository = self._get_repository()

    def _get_repository(self) -> TracksRepository:
        raise NotImplementedError

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


class SqLiteTracksRepositoryTest(TracksRepositoryAbstractTest):

    def setUp(self) -> None:
        self.tmp_dir = mkdtemp()
        super().setUp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def _get_repository(self) -> SqLiteTracksRepository:
        return SqLiteTracksRepository(self.tmp_dir + "/test.db")


class InMemoryTracksRepositoryTest(TracksRepositoryAbstractTest):

    def _get_repository(self) -> InMemoryTracksRepository:
        return InMemoryTracksRepository()
