from unittest import TestCase, mock

from traemplist.config import TraemplistConfig, AccountConfig, AccountCredentialsConfig, PlaylistConfig, Config
from traemplist.client import TracksCollection, Track, Artist, Playlist
from traemplist.repository import TrackRecord
from traemplist.service import TracksHistoryService, TraemplistGeneratorService


class TracksHistoryServiceTest(TestCase):

    def setUp(self) -> None:
        self.spotify_client_mock = mock.Mock()
        self.tracks_repository_mock = mock.Mock()
        self.tracks_history_service = TracksHistoryService(
            client=self.spotify_client_mock,
            repository=self.tracks_repository_mock,
            logger=mock.Mock()
        )

    def test_save_recently_played_tracks_success(self):
        recently_played_tracks = TracksCollection()
        recently_played_tracks.add_track(self._create_test_track("test_track"))
        self.spotify_client_mock.get_recently_played_tracks.return_value = recently_played_tracks
        self.tracks_history_service.save_recently_played_tracks()
        self.tracks_repository_mock.save_tracks.assert_called_once_with(
            [TrackRecord(id=track.id) for track in recently_played_tracks.get_tracks()]
        )

    def test_save_all_user_playlists_tracks_success(self):
        self.spotify_client_mock.get_user_playlist_ids.return_value = ["10", "20"]
        playlist_a = Playlist(playlist_id="a", name="playlist A").add_track(self._create_test_track("test_track_a"))
        playlist_b = Playlist(playlist_id="b", name="playlist B").add_track(self._create_test_track("test_track_b"))
        self.spotify_client_mock.get_playlist.side_effect = [playlist_a, playlist_b]
        self.tracks_history_service.save_all_user_playlists_tracks()
        self.tracks_repository_mock.save_tracks.assert_has_calls([
            mock.call(
                [TrackRecord(id=track.id) for track in playlist_a.get_tracks()]
            ),
            mock.call(
                [TrackRecord(id=track.id) for track in playlist_b.get_tracks()]
            )
        ])
        self.spotify_client_mock.get_playlist.assert_has_calls([
            mock.call("10"),
            mock.call("20")
        ])

    @staticmethod
    def _create_test_track(track_id: str) -> Track:
        return Track(
            id=track_id,
            name=f"{track_id} name",
            artist=Artist(
                id=f"{track_id} artist_id",
                name=f"{track_id } artist_name"
            )
        )


class TraemplistGeneratorServiceTest(TestCase):

    def setUp(self) -> None:
        self.spotify_client_mock = mock.Mock()
        self.traemplist_generator_mock = mock.Mock()
        self.account_credentials = AccountCredentialsConfig(
            client_id="client_id",
            client_secret="client_secret",
            refresh_token="refresh_token"
        )

    def test_generate_and_save_traemplist_from_standard_playlist(self):
        playlist_track = self._create_test_track("playlist_track")
        self.spotify_client_mock.get_playlist.return_value = Playlist(
            playlist_id="playlist_id",
            name="playlist_name"
        ).add_track(playlist_track)
        generated_tracks_collection = TracksCollection().add_track(playlist_track)
        self.traemplist_generator_mock.generate.return_value = generated_tracks_collection
        TraemplistGeneratorService(
            config=TraemplistConfig(
                account=AccountConfig(
                    credentials=self.account_credentials,
                    playlists=[
                        PlaylistConfig(id="playlist_id")
                    ]
                ),
                traemplist_songs_count=2,
                traemplist_id="traemplist_id"
            ),
            client=self.spotify_client_mock,
            generator=self.traemplist_generator_mock,
            logger=mock.Mock()
        ).generate_and_save_traemplist()
        self.traemplist_generator_mock.generate.assert_called_once_with(
            input_tracks_collection=TracksCollection().add_track(playlist_track),
            size=2
        )
        self.spotify_client_mock.get_playlist.assert_called_once_with("playlist_id")
        self.spotify_client_mock.replace_playlist_tracks.assert_called_once_with(
            playlist_id="traemplist_id",
            new_track_ids=["playlist_track"]
        )

    def test_generate_and_save_traemplist_from_liked_songs(self):
        playlist_track = self._create_test_track("playlist_track")
        self.spotify_client_mock.get_user_liked_tracks.return_value = Playlist(
            playlist_id="playlist_id",
            name="playlist_name"
        ).add_track(playlist_track)
        generated_tracks_collection = TracksCollection().add_track(playlist_track)
        self.traemplist_generator_mock.generate.return_value = generated_tracks_collection
        TraemplistGeneratorService(
            config=TraemplistConfig(
                account=AccountConfig(
                    credentials=self.account_credentials,
                    playlists=[
                        PlaylistConfig(id=Config.LIKED_SONGS_PLAYLIST_ID)
                    ]
                ),
                traemplist_songs_count=2,
                traemplist_id="traemplist_id"
            ),
            client=self.spotify_client_mock,
            generator=self.traemplist_generator_mock,
            logger=mock.Mock()
        ).generate_and_save_traemplist()
        self.traemplist_generator_mock.generate.assert_called_once_with(
            input_tracks_collection=TracksCollection().add_track(playlist_track),
            size=2
        )
        self.spotify_client_mock.get_user_liked_tracks.assert_called_once()
        self.spotify_client_mock.replace_playlist_tracks.assert_called_once_with(
            playlist_id="traemplist_id",
            new_track_ids=["playlist_track"]
        )

    @staticmethod
    def _create_test_track(track_id: str) -> Track:
        return Track(
            id=track_id,
            name=f"{track_id} name",
            artist=Artist(
                id=f"{track_id} artist_id",
                name=f"{track_id} artist_name"
            )
        )
