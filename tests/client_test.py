from unittest import TestCase, mock
from typing import Optional
from uuid import uuid4
from spotipy.oauth2 import SpotifyOauthError
from spotipy.client import SpotifyException
from traemplist.config import AccountCredentialsConfig
from traemplist.client import Artist, Track, TracksCollection, EmptyTracksCollectionError, SpotifyAccessTokenProvider, \
    SpotifyAccessTokenRequestError, SpotifyAccessTokenResponseDataError, SpotifyClient, SpotifyClientRequestError, \
    SpotifyClientResponseDataError, Playlist


class TracksCollectionTest(TestCase):

    def test_tracks_adding(self):
        collection = TracksCollection()
        self.assertEqual(collection.get_tracks(), set())
        track_a = self._create_test_track()
        track_b = self._create_test_track()
        collection.add_track(track_a)
        collection.add_track(track_b)
        self.assertEqual(collection.get_tracks(), {track_a, track_b})
        track_c = self._create_test_track()
        track_d = self._create_test_track()
        collection.add_tracks(
            TracksCollection().add_track(track_c).add_track(track_d)
        )
        self.assertEqual(
            collection.get_tracks(),
            {track_a, track_b, track_c, track_d}
        )

    def test_get_random_track(self):
        with self.subTest("From non-empty collection"):
            track = self._create_test_track()
            collection = TracksCollection().add_track(track)
            self.assertEqual(collection.get_random_track(), track)
        with self.subTest("From empty collection"):
            with self.assertRaises(EmptyTracksCollectionError):
                TracksCollection().get_random_track()

    def test_contains_artist_track(self):
        track = self._create_test_track()
        collection = TracksCollection().add_track(track)
        self.assertTrue(
            collection.contains_artist_track(track.artist)
        )
        self.assertFalse(
            collection.contains_artist_track(Artist(id="new", name="new"))
        )

    def test_remove_artist_tracks(self):
        track_a = self._create_test_track()
        track_b = self._create_test_track(artist=Artist(id="new", name="new"))
        collection = TracksCollection().add_track(track_a).add_track(track_b)
        collection.remove_artist_tracks(track_a.artist)
        self.assertFalse(collection.contains_artist_track(track_a.artist))
        self.assertTrue(collection.contains_artist_track(track_b.artist))

    def test_contains(self):
        track_a = self._create_test_track()
        track_b = self._create_test_track()
        collection = TracksCollection().add_track(track_a)
        self.assertTrue(track_a in collection)
        self.assertFalse(track_b in collection)

    def test_length(self):
        collection = TracksCollection()
        self.assertEqual(len(collection), 0)
        collection.add_track(self._create_test_track())
        self.assertEqual(len(collection), 1)

    @staticmethod
    def _create_test_track(artist: Optional[Artist] = None) -> Track:
        track_id = str(uuid4())
        if not artist:
            artist = Artist(id="artist", name="Artist")
        return Track(id=track_id, name=track_id, artist=artist)


class SpotifyAccessTokenProviderTest(TestCase):

    CLIENT_ID = "test_client_id"
    CLIENT_SECRET = "test_client_secret"
    REFRESH_TOKEN = "test_refresh_token"

    def setUp(self) -> None:
        self.provider = SpotifyAccessTokenProvider(
            credentials_config=AccountCredentialsConfig(
                client_id=self.CLIENT_ID,
                client_secret=self.CLIENT_SECRET,
                refresh_token=self.REFRESH_TOKEN
            )
        )

    def test_get_access_token_success(self):
        with mock.patch("traemplist.client.SpotifyOAuth") as oauth_mock:
            oauth_instance_mock = mock.Mock()
            oauth_mock.side_effect = lambda *args, **kwargs: oauth_instance_mock
            oauth_instance_mock.refresh_access_token.return_value = {
                "access_token": "returned_access_token"
            }
            self.assertEqual(
                self.provider.get_access_token(),
                "returned_access_token"
            )
            self.provider.get_access_token()
            oauth_mock.assert_called_once_with(
                client_id=self.CLIENT_ID,
                client_secret=self.CLIENT_SECRET,
                redirect_uri="localhost"
            )
            oauth_instance_mock.refresh_access_token.assert_called_once_with(
                refresh_token=self.REFRESH_TOKEN
            )

    def test_access_token_request_error(self):
        with mock.patch("traemplist.client.SpotifyOAuth") as oauth_mock:
            oauth_instance_mock = mock.Mock()
            oauth_mock.side_effect = lambda *args, **kwargs: oauth_instance_mock
            oauth_instance_mock.refresh_access_token.side_effect = SpotifyOauthError("error")
            with self.assertRaises(SpotifyAccessTokenRequestError):
                self.provider.get_access_token()

    def test_access_token_response_data_error(self):
        with mock.patch("traemplist.client.SpotifyOAuth") as oauth_mock:
            oauth_instance_mock = mock.Mock()
            oauth_mock.side_effect = lambda *args, **kwargs: oauth_instance_mock
            oauth_instance_mock.refresh_access_token.return_value = {
                "invalid": "data"
            }
            with self.assertRaises(SpotifyAccessTokenResponseDataError):
                self.provider.get_access_token()


class SpotifyClientTest(TestCase):

    ACCESS_TOKEN = "test_access_token"
    ARTIST_RESPONSE_DATA = {
        "id": "artist_id",
        "name": "artist_name"
    }
    ARTIST_RESPONSE_OBJECT = Artist(
        id="artist_id",
        name="artist_name"
    )
    TRACK_RESPONSE_DATA = {
        "id": "track_id",
        "name": "track_name",
        "artists": [
            ARTIST_RESPONSE_DATA
        ]
    }
    TRACK_RESPONSE_OBJECT = Track(
        id="track_id",
        name="track_name",
        artist=ARTIST_RESPONSE_OBJECT
    )

    def setUp(self) -> None:
        self.token_provider = mock.Mock()
        self.token_provider.get_access_token.return_value = self.ACCESS_TOKEN
        self.client = SpotifyClient(
            access_token_provider=self.token_provider
        )

    def test_get_user_playlist_ids_success(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.current_user_playlists.side_effect = [
                {
                    "items": [{"id": str(i)} for i in range(50)]
                },
                {
                    "items": [{"id": str(i)} for i in range(50, 60)]
                }
            ]
            self.assertEqual(
                list(self.client.get_user_playlist_ids()),
                [str(i) for i in range(60)]
            )
            client_instance_mock.current_user_playlists.assert_has_calls([
                mock.call(
                    limit=SpotifyClient.GET_USER_PLAYLIST_LIMIT,
                    offset=0
                ),
                mock.call(
                    limit=SpotifyClient.GET_USER_PLAYLIST_LIMIT,
                    offset=SpotifyClient.GET_USER_PLAYLIST_LIMIT
                )
            ])

    def test_get_user_playlist_ids_request_error(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.current_user_playlists.side_effect = SpotifyException("error", "error", "error")
            with self.assertRaises(SpotifyClientRequestError):
                list(self.client.get_user_playlist_ids())

    def test_get_user_playlist_ids_response_data_error(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.current_user_playlists.return_value = {"invalid_data"}
            with self.assertRaises(SpotifyClientResponseDataError):
                list(self.client.get_user_playlist_ids())

    def test_get_playlist_success(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.playlist.return_value = {
                "id": "playlist_id",
                "name": "playlist_name",
                "tracks": {
                    "items": [
                        {
                            "track": self.TRACK_RESPONSE_DATA
                        }
                    ]
                }
            }
            self.assertEqual(
                self.client.get_playlist(playlist_id="playlist_id"),
                Playlist(
                    playlist_id="playlist_id",
                    name="playlist_name"
                ).add_track(
                    self.TRACK_RESPONSE_OBJECT
                )
            )
            client_instance_mock.playlist.assert_called_once_with(
                playlist_id="playlist_id",
                fields=["id, name, tracks.items(track(name, id, artists))"]
            )

    def test_get_playlist_request_error(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.playlist.side_effect = SpotifyException("error", "error", "error")
            with self.assertRaises(SpotifyClientRequestError):
                self.client.get_playlist(playlist_id="playlist_id")

    def test_get_playlist_response_data_error(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.playlist.return_value = {"invalid_data"}
            with self.assertRaises(SpotifyClientResponseDataError):
                self.client.get_playlist(playlist_id="playlist_id")

    def test_get_recently_played_tracks_success(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.current_user_recently_played.return_value = {
                "items": [
                    {
                        "track": self.TRACK_RESPONSE_DATA
                    }
                ]
            }
            self.assertEqual(
                self.client.get_recently_played_tracks(),
                TracksCollection().add_track(
                    self.TRACK_RESPONSE_OBJECT
                )
            )
            client_instance_mock.current_user_recently_played.assert_called_once()

    def test_get_recently_played_tracks_request_error(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.current_user_recently_played.side_effect = SpotifyException("error", "error", "error")
            with self.assertRaises(SpotifyClientRequestError):
                self.client.get_recently_played_tracks()

    def test_get_recently_played_tracks_response_data_error(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.current_user_recently_played.return_value = {"invalid_data"}
            with self.assertRaises(SpotifyClientResponseDataError):
                self.client.get_recently_played_tracks()

    def test_get_related_artists_success(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.artist_related_artists.return_value = {
                "artists": [
                    self.ARTIST_RESPONSE_DATA
                ]
            }
            self.assertEqual(
                self.client.get_related_artists(artist_id="artist_id"),
                [self.ARTIST_RESPONSE_OBJECT]
            )
            client_instance_mock.artist_related_artists.assert_called_once_with(
                artist_id="artist_id"
            )

    def test_get_related_artists_request_error(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.artist_related_artists.side_effect = SpotifyException("error", "error", "error")
            with self.assertRaises(SpotifyClientRequestError):
                self.client.get_related_artists(artist_id="artist_id")

    def test_get_related_artists_response_data_error(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.artist_related_artists.return_value = {"invalid_data"}
            with self.assertRaises(SpotifyClientResponseDataError):
                self.client.get_related_artists(artist_id="artist_id")

    def test_get_artist_top_tracks_success(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.artist_top_tracks.return_value = {
                "tracks": [
                    self.TRACK_RESPONSE_DATA
                ]
            }
            self.assertEqual(
                self.client.get_artist_top_tracks(artist_id="artist_id"),
                TracksCollection().add_track(
                    self.TRACK_RESPONSE_OBJECT
                )
            )
            client_instance_mock.artist_top_tracks.assert_called_once_with(
                artist_id="artist_id"
            )

    def test_get_artist_top_tracks_request_error(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.artist_top_tracks.side_effect = SpotifyException("error", "error", "error")
            with self.assertRaises(SpotifyClientRequestError):
                self.client.get_artist_top_tracks(artist_id="artist_id")

    def test_get_artist_top_tracks_response_data_error(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.artist_top_tracks.return_value = {"invalid_data"}
            with self.assertRaises(SpotifyClientResponseDataError):
                self.client.get_artist_top_tracks(artist_id="artist_id")

    def test_replace_playlist_tracks_success(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            self.client.replace_playlist_tracks(
                playlist_id="playlist_id",
                new_track_ids=["track_a", "track_b"]
            )
            client_instance_mock.playlist_replace_items.assert_called_once_with(
                playlist_id="playlist_id",
                items=["track_a", "track_b"]
            )

    def test_replace_playlist_tracks_request_error(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.playlist_replace_items.side_effect = SpotifyException("error", "error", "error")
            with self.assertRaises(SpotifyClientRequestError):
                self.client.replace_playlist_tracks(
                    playlist_id="playlist_id",
                    new_track_ids=["track_a", "track_b"]
                )

    def test_get_user_liked_tracks_success(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            tracks_data = []
            tracks_objects = []
            for i in range(self.client.GET_USER_LIKED_SONGS_LIMIT):
                track_data = dict(self.TRACK_RESPONSE_DATA)
                track_id = f"track_{i}_id"
                track_name = f"track_{i}_name"
                track_data["id"] = track_id
                track_data["name"] = track_name
                tracks_data.append(
                    {"track": track_data}
                )
                tracks_objects.append(
                    Track(
                        id=track_id,
                        name=track_name,
                        artist=self.ARTIST_RESPONSE_OBJECT
                    )
                )
            client_instance_mock.current_user_saved_tracks.side_effect = [
                {
                    "items": tracks_data
                },
                {
                    "items": []
                }
            ]
            expected_tracks_collection = TracksCollection()
            for tracks_object in tracks_objects:
                expected_tracks_collection.add_track(tracks_object)
            self.assertEqual(
                self.client.get_user_liked_tracks(),
                expected_tracks_collection
            )
            client_instance_mock.current_user_saved_tracks.assert_has_calls([
                mock.call(
                    limit=SpotifyClient.GET_USER_LIKED_SONGS_LIMIT,
                    offset=0
                ),
                mock.call(
                    limit=SpotifyClient.GET_USER_LIKED_SONGS_LIMIT,
                    offset=SpotifyClient.GET_USER_LIKED_SONGS_LIMIT
                )
            ])

    def test_get_user_liked_tracks_request_error(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.current_user_saved_tracks.side_effect = SpotifyException("error", "error", "error")
            with self.assertRaises(SpotifyClientRequestError):
                self.client.get_user_liked_tracks()

    def test_get_user_liked_tracks_response_data_error(self):
        with mock.patch("traemplist.client.Spotify") as client_mock:
            client_instance_mock = mock.Mock()
            client_mock.side_effect = lambda *args, **kwargs: client_instance_mock
            client_instance_mock.current_user_saved_tracks.return_value = {"invalid_data"}
            with self.assertRaises(SpotifyClientResponseDataError):
                self.client.get_user_liked_tracks()
