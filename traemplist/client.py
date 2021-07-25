from dataclasses import dataclass
from typing import Set, Callable, Iterator

from spotipy.client import Spotify
from spotipy.oauth2 import SpotifyOAuth

from traemplist.config import AccountCredentialsConfig


@dataclass(frozen=True)
class Artist:
    id: str


@dataclass(frozen=True)
class Track:
    id: str
    name: str
    artist: Artist

    def __eq__(self, other: "Track") -> bool:
        return self.id == other.id


class TracksCollection:

    def __init__(self):
        self.tracks = set()

    def add_track(self, track: Track) -> "TracksCollection":
        self.tracks.add(track)
        return self

    def get_tracks(self) -> Set[Track]:
        return self.tracks

    def add_tracks(self, tracks: "TracksCollection") -> "TracksCollection":
        self.tracks = self.tracks.union(tracks.get_tracks())
        return self

    def __contains__(self, item: Track) -> bool:
        return item in self.tracks


class Playlist(TracksCollection):

    def __init__(self, playlist_id: str, name: str):
        super().__init__()
        self.id = playlist_id
        self.name = name

    def get_id(self) -> str:
        return self.id

    def get_name(self) -> str:
        return self.name


class SpotifyClient:

    GET_USER_PLAYLIST_LIMIT = 50

    def __init__(self, credentials_config: AccountCredentialsConfig):
        self.credentials_config = credentials_config
        self.credentials_config_change_callbacks = []
        self.access_token = None

    def register_credentials_config_change_callback(self, callback: Callable[[], None]) -> None:
        self.credentials_config_change_callbacks.append(callback)

    def get_user_playlist_ids(self) -> Iterator[str]:
        limit = self.GET_USER_PLAYLIST_LIMIT
        offset = 0
        while True:
            items = self._get_spotify_client().current_user_playlists(limit=limit, offset=offset)["items"]
            for item in items:
                yield item["id"]
            if len(items) < limit:
                break
            offset += limit

    def get_playlist(self, playlist_id: str) -> Playlist:
        return self._create_playlist_from_response(
            self._get_spotify_client().playlist(
                playlist_id=playlist_id,
                fields=["id, name, tracks.items(track(name, id, artists))"]
            )
        )

    def get_recently_played_tracks(self) -> TracksCollection:
        response = self._get_spotify_client().current_user_recently_played()
        return self._create_tracks_from_response(response["items"])

    def _get_spotify_client(self) -> Spotify:
        return Spotify(
            auth=self._get_access_token()
        )

    def _get_access_token(self) -> str:
        if not self.access_token:
            new_tokens = SpotifyOAuth(
                client_id=self.credentials_config.client_id,
                client_secret=self.credentials_config.client_secret,
                redirect_uri="localhost"
            ).refresh_access_token(
                refresh_token=self.credentials_config.refresh_token
            )
            self.credentials_config.refresh_token = new_tokens["refresh_token"]
            self.access_token = new_tokens["access_token"]
        return self.access_token

    def _call_credentials_change_callbacks(self):
        for callback in self.credentials_config_change_callbacks:
            callback()

    def _create_playlist_from_response(self, response: dict) -> Playlist:
        playlist = Playlist(
            playlist_id=response["id"],
            name=response["name"]
        )
        playlist.add_tracks(
            self._create_tracks_from_response(
                response["tracks"]["items"]
            )
        )
        return playlist

    def _create_tracks_from_response(self, response: [dict]) -> TracksCollection:
        tracks = TracksCollection()
        for item in response:
            tracks.add_track(
                self._create_track_from_response(item["track"])
            )
        return tracks

    @staticmethod
    def _create_track_from_response(response: dict) -> Track:
        return Track(
            id=response["id"],
            name=response["name"],
            artist=response["artists"][0]["id"]
        )
