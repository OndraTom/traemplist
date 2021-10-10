from dataclasses import dataclass
from typing import Set, Iterator
from random import randint

import jsonschema
from spotipy.client import Spotify, SpotifyException
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError

from traemplist.config import AccountCredentialsConfig


@dataclass(frozen=True)
class Artist:
    id: str
    name: str


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

    def get_random_track(self) -> Track:
        """
        :raises EmptyTracksCollectionError
        """
        if not self:
            raise EmptyTracksCollectionError
        tracks_list = list(self.tracks)
        return tracks_list[randint(0, len(tracks_list) - 1)]

    def contains_artist_track(self, artist: Artist) -> bool:
        for track in self.tracks:
            if track.artist == artist:
                return True
        return False

    def remove_artist_tracks(self, artist: Artist) -> None:
        for track in list(self.tracks):
            if track.artist == artist:
                self.tracks.remove(track)

    def __contains__(self, item: Track) -> bool:
        return item in self.tracks

    def __len__(self) -> int:
        return len(self.tracks)

    def __bool__(self) -> bool:
        return len(self.tracks) > 0

    def __str__(self) -> str:
        tracks_str = []
        for track in self.tracks:
            tracks_str.append(
                f"{track.artist.name} - {track.name}"
            )
        return "\n".join(tracks_str)

    def __eq__(self, other: "TracksCollection") -> bool:
        return self.tracks == other.tracks


class Playlist(TracksCollection):

    def __init__(self, playlist_id: str, name: str):
        super().__init__()
        self.id = playlist_id
        self.name = name

    def get_id(self) -> str:
        return self.id

    def get_name(self) -> str:
        return self.name

    def __eq__(self, other: "Playlist") -> bool:
        return self.id == other.id


class SpotifyAccessTokenProvider:

    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "access_token": {
                "type": "string"
            }
        },
        "required": [
            "access_token"
        ]
    }

    def __init__(self, credentials_config: AccountCredentialsConfig):
        self.credentials_config = credentials_config
        self.access_token = None

    def get_access_token(self) -> str:
        """
        :raises SpotifyAccessTokenProviderException
        """
        if not self.access_token:
            try:
                new_tokens = SpotifyOAuth(
                    client_id=self.credentials_config.client_id,
                    client_secret=self.credentials_config.client_secret,
                    redirect_uri="localhost"
                ).refresh_access_token(
                    refresh_token=self.credentials_config.refresh_token
                )
                self._validate_response_data(new_tokens)
                self.access_token = new_tokens["access_token"]
            except SpotifyOauthError as e:
                raise SpotifyAccessTokenRequestError(str(e))
        return self.access_token

    def _validate_response_data(self, response_data: dict):
        try:
            jsonschema.validate(response_data, self.RESPONSE_SCHEMA)
        except jsonschema.ValidationError:
            raise SpotifyAccessTokenResponseDataError(response_data)


class SpotifyClient:

    GET_USER_PLAYLIST_LIMIT = 50
    GET_USER_LIKED_SONGS_LIMIT = 50
    USER_PLAYLIST_IDS_SCHEMA = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"}
                    },
                    "required": ["id"]
                }
            }
        },
        "required": ["items"]
    }
    ARTIST_SCHEMA = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"}
        },
        "required": ["id", "name"]
    }
    TRACK_SCHEMA = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "artists": {
                "type": "array",
                "items": ARTIST_SCHEMA,
                "minItems": 1
            }
        },
        "required": ["id", "name", "artists"]
    }
    TRACKS_SCHEMA = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "track": TRACK_SCHEMA
                    },
                    "required": ["track"]
                }
            }
        },
        "required": ["items"]
    }
    PLAYLIST_SCHEMA = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "tracks": TRACKS_SCHEMA
        },
        "required": ["id", "name", "tracks"]
    }
    RELATED_ARTISTS_SCHEMA = {
        "type": "object",
        "properties": {
            "artists": {
                "type": "array",
                "items": ARTIST_SCHEMA
            }
        },
        "required": ["artists"]
    }
    ARTIST_TOP_TRACKS_SCHEMA = {
        "type": "object",
        "properties": {
            "tracks": {
                "type": "array",
                "items": TRACK_SCHEMA
            }
        },
        "required": ["tracks"]
    }
    USER_LIKED_TRACKS_SCHEMA = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "track": TRACK_SCHEMA
                    },
                    "required": ["track"]
                }
            }
        },
        "required": ["items"]
    }

    def __init__(self, access_token_provider: SpotifyAccessTokenProvider):
        self.access_token_provider = access_token_provider

    def get_user_playlist_ids(self) -> Iterator[str]:
        request_name = "current_user_playlists"
        limit = self.GET_USER_PLAYLIST_LIMIT
        offset = 0
        try:
            while True:
                response_data = self._get_spotify_client().current_user_playlists(limit=limit, offset=offset)
                self._validate_response_data(
                    request_name=request_name,
                    response_data=response_data,
                    schema=self.USER_PLAYLIST_IDS_SCHEMA
                )
                for item in response_data["items"]:
                    yield item["id"]
                if len(response_data["items"]) < limit:
                    break
                offset += limit
        except SpotifyException as e:
            raise SpotifyClientRequestError(request_name, str(e))

    def get_playlist(self, playlist_id: str) -> Playlist:
        request_name = "playlist"
        try:
            response_data = self._get_spotify_client().playlist(
                playlist_id=playlist_id,
                fields=["id, name, tracks.items(track(name, id, artists))"]
            )
            self._validate_response_data(
                request_name=request_name,
                response_data=response_data,
                schema=self.PLAYLIST_SCHEMA
            )
            return self._create_playlist_from_response(response_data)
        except SpotifyException as e:
            raise SpotifyClientRequestError(request_name, str(e))

    def get_recently_played_tracks(self) -> TracksCollection:
        request_name = "recently_played_tracks"
        try:
            response_data = self._get_spotify_client().current_user_recently_played()
            self._validate_response_data(
                request_name=request_name,
                response_data=response_data,
                schema=self.TRACKS_SCHEMA
            )
            return self._create_tracks_from_response(response_data["items"])
        except SpotifyException as e:
            raise SpotifyClientRequestError(request_name, str(e))

    def get_related_artists(self, artist_id: str) -> [Artist]:
        request_name = "artist_related_artists"
        try:
            related_artists = []
            response_data = self._get_spotify_client().artist_related_artists(artist_id=artist_id)
            self._validate_response_data(
                request_name=request_name,
                response_data=response_data,
                schema=self.RELATED_ARTISTS_SCHEMA
            )
            for artist_data in response_data["artists"]:
                related_artists.append(
                    self._create_artist_from_response(artist_data)
                )
            return related_artists
        except SpotifyException as e:
            raise SpotifyClientRequestError(request_name, str(e))

    def get_artist_top_tracks(self, artist_id: str) -> TracksCollection:
        request_name = "artist_top_tracks"
        try:
            response_data = self._get_spotify_client().artist_top_tracks(artist_id=artist_id)
            self._validate_response_data(
                request_name=request_name,
                response_data=response_data,
                schema=self.ARTIST_TOP_TRACKS_SCHEMA
            )
            top_tracks = TracksCollection()
            for track_data in response_data["tracks"]:
                top_tracks.add_track(
                    self._create_track_from_response(track_data)
                )
            return top_tracks
        except SpotifyException as e:
            raise SpotifyClientRequestError(request_name, str(e))

    def replace_playlist_tracks(self, playlist_id: str, new_track_ids: [str]):
        try:
            self._get_spotify_client().playlist_replace_items(
                playlist_id=playlist_id,
                items=new_track_ids
            )
        except SpotifyException as e:
            raise SpotifyClientRequestError("playlist_replace_items", str(e))

    def get_user_liked_tracks(self) -> TracksCollection:
        request_name = "current_user_saved_tracks"
        limit = self.GET_USER_LIKED_SONGS_LIMIT
        offset = 0
        liked_tracks = TracksCollection()
        spotify_client = self._get_spotify_client()
        try:
            while True:
                response_data = spotify_client.current_user_saved_tracks(limit=limit, offset=offset)
                self._validate_response_data(
                    request_name=request_name,
                    response_data=response_data,
                    schema=self.USER_LIKED_TRACKS_SCHEMA
                )
                items = response_data["items"]
                for item in items:
                    liked_tracks.add_track(
                        self._create_track_from_response(item["track"])
                    )
                if len(items) < limit:
                    return liked_tracks
                offset += limit
        except SpotifyException as e:
            raise SpotifyClientRequestError(request_name, str(e))

    def _get_spotify_client(self) -> Spotify:
        return Spotify(
            auth=self.access_token_provider.get_access_token()
        )

    @staticmethod
    def _validate_response_data(request_name: str, response_data: object, schema: dict):
        try:
            jsonschema.validate(response_data, schema)
        except jsonschema.ValidationError:
            raise SpotifyClientResponseDataError(request_name, response_data)

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

    def _create_track_from_response(self, response: dict) -> Track:
        return Track(
            id=response["id"],
            name=response["name"],
            artist=self._create_artist_from_response(response["artists"][0])
        )

    @staticmethod
    def _create_artist_from_response(response: dict) -> Artist:
        return Artist(
            id=response["id"],
            name=response["name"]
        )


class TracksCollectionException(Exception):
    pass


class EmptyTracksCollectionError(TracksCollectionException):

    def __str__(self) -> str:
        return "Empty tracks collection error"


class SpotifyAccessTokenProviderException(Exception):
    pass


class SpotifyAccessTokenRequestError(SpotifyAccessTokenProviderException):

    def __init__(self, error: str):
        self.error = error

    def __str__(self) -> str:
        return f"Access token request has failed: {self.error}"


class SpotifyAccessTokenResponseDataError(SpotifyAccessTokenProviderException):

    def __init__(self, response_data: dict):
        self.response_data = response_data

    def __str__(self) -> str:
        return f"Access token response doesn't contain valid data: {self.response_data}"


class SpotifyClientException(Exception):
    pass


class SpotifyClientRequestError(SpotifyClientException):

    def __init__(self, request_name: str, error: str):
        self.request_name = request_name
        self.error = error

    def __str__(self) -> str:
        return f"Spotify client request '{self.request_name}' has failed: {self.error}"


class SpotifyClientResponseDataError(SpotifyClientException):

    def __init__(self, request_name: str, response_data: object):
        self.request_name = request_name
        self.response_data = response_data

    def __str__(self) -> str:
        return f"Spotify client response of '{self.request_name}' doesn't contain valid data: {self.response_data}"
