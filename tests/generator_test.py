from unittest import TestCase, mock

from traemplist.client import TracksCollection, Track, Artist
from traemplist.repository import InMemoryTracksRepository, TrackRecord
from traemplist.generator import TraemplistGenerator, InvalidTraemplistSizeError


class TraemplistGeneratorTest(TestCase):

    def test_generate_success(self):
        client_mock = mock.Mock()
        history = InMemoryTracksRepository()
        history.save_tracks(
            [
                TrackRecord(id="history_track_a"),
                TrackRecord(id="history_track_b"),
                TrackRecord(id="history_track_c")
            ]
        )
        input_tracks_collection = TracksCollection()
        input_tracks_collection.add_track(self._create_track(track_id="input_track_a"))
        input_tracks_collection.add_track(self._create_track(track_id="input_track_b"))
        input_tracks_collection.add_track(self._create_track(track_id="input_track_c"))
        client_mock.get_related_artists.side_effect = [
            [Artist(id="related_artist_a", name="related_artist_a")],
            [Artist(id="related_artist_b", name="related_artist_b")],
            [Artist(id="related_artist_b", name="related_artist_c")]
        ]
        client_mock.get_artist_top_tracks.side_effect = [
            TracksCollection()
            .add_track(self._create_track(track_id="top_track_a"))
            .add_track(self._create_track(track_id="history_track_b")),
            TracksCollection()
            .add_track(self._create_track(track_id="top_track_b"))
            .add_track(self._create_track(track_id="top_track_a")),
            TracksCollection()
            .add_track(self._create_track(track_id="top_track_c"))
        ]
        traemplist = TraemplistGenerator(
            client=client_mock,
            history=history,
            logger=mock.Mock()
        ).generate(
            input_tracks_collection=input_tracks_collection,
            size=100
        )
        self.assertEqual(
            traemplist,
            TracksCollection()
            .add_track(self._create_track(track_id="top_track_a"))
            .add_track(self._create_track(track_id="top_track_b"))
            .add_track(self._create_track(track_id="top_track_c"))
        )
        client_mock.get_related_artists.assert_has_calls([
            mock.call(
                artist_id="track_input_track_a_artist_id"
            ),
            mock.call(
                artist_id="track_input_track_b_artist_id"
            ),
            mock.call(
                artist_id="track_input_track_c_artist_id"
            )
        ], any_order=True)
        client_mock.get_artist_top_tracks.assert_has_calls([
            mock.call(
                artist_id="related_artist_a"
            ),
            mock.call(
                artist_id="related_artist_b"
            ),
            mock.call(
                artist_id="related_artist_b"
            )
        ])

    def test_invalid_size_error(self):
        with self.assertRaises(InvalidTraemplistSizeError):
            TraemplistGenerator(
                client=mock.Mock(),
                history=mock.Mock(),
                logger=mock.Mock()
            ).generate(
                input_tracks_collection=mock.Mock(),
                size=-1
            )

    @staticmethod
    def _create_track(track_id: str) -> Track:
        return Track(
            id=track_id,
            name=f"track_{track_id}_name",
            artist=Artist(
                id=f"track_{track_id}_artist_id",
                name=f"track_{track_id}_artist_name",
            )
        )
