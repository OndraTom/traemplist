import json
import jsonschema
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class PlaylistConfig:
    id: str


@dataclass(frozen=False)
class AccountCredentialsConfig:
    client_id: str
    client_secret: str
    refresh_token: str


@dataclass(frozen=True)
class AccountConfig:
    credentials: AccountCredentialsConfig
    playlists: [PlaylistConfig]


@dataclass(frozen=True)
class TraemplistConfig:
    account: AccountConfig
    traemplist_songs_count: int
    traemplist_id: str


class Config(ABC):

    LIKED_SONGS_PLAYLIST_ID = "liked_songs"

    @abstractmethod
    def get_traemplist_configs(self) -> [TraemplistConfig]:
        pass

    @abstractmethod
    def save(self) -> None:
        pass


class JsonConfig(Config):

    SCHEMA = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "account": {
                    "type": "object",
                    "properties": {
                        "credentials": {
                            "type": "object",
                            "properties": {
                                "client_id": {
                                    "type": "string"
                                },
                                "client_secret": {
                                    "type": "string"
                                },
                                "refresh_token": {
                                    "type": "string"
                                }
                            },
                            "required": [
                                "client_id",
                                "client_secret",
                                "refresh_token"
                            ]
                        },
                        "playlists": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "string"
                                    }
                                },
                                "required": [
                                    "id"
                                ]
                            },
                            "minItems": 1
                        }
                    },
                    "required": [
                        "credentials",
                        "playlists"
                    ]
                },
                "traemplist_songs_count": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 200
                },
                "traemplist_id": {
                    "type": "string"
                }
            },
            "required": [
                "account",
                "traemplist_songs_count",
                "traemplist_id"
            ]
        },
        "minItems": 1
    }

    def __init__(self, config_file_path: str):
        """
        :raises ConfigException
        """
        self.config_file_path = config_file_path
        self.config_data = self._get_config_data()
        self._validate_config_data(self.config_data)
        self.traemplists = self._get_traemplists_from_data()

    def get_traemplist_configs(self) -> [TraemplistConfig]:
        return self.traemplists

    def save(self) -> None:
        self.config_data = [asdict(traemplist) for traemplist in self.traemplists]
        with open(self.config_file_path, "w") as config_file:
            config_file.write(
                json.dumps(self.config_data, indent=2)
            )

    def _get_config_data(self) -> dict:
        try:
            with open(self.config_file_path) as config_file:
                return json.load(config_file)
        except FileNotFoundError:
            raise ConfigFileNotFoundError
        except json.JSONDecodeError:
            raise InvalidJsonError

    def _validate_config_data(self, config_data: dict):
        try:
            jsonschema.validate(config_data, self.SCHEMA)
        except jsonschema.ValidationError:
            raise InvalidConfigDataError

    def _get_traemplists_from_data(self) -> [TraemplistConfig]:
        traemplists = []
        for traemplist_data in self.config_data:
            traemplists.append(
                TraemplistConfig(
                    account=self._get_account_from_data(traemplist_data["account"]),
                    traemplist_songs_count=traemplist_data["traemplist_songs_count"],
                    traemplist_id=traemplist_data["traemplist_id"]
                )
            )
        return traemplists

    @staticmethod
    def _get_account_from_data(account_data: dict) -> AccountConfig:
        playlists = []
        for playlist_data in account_data["playlists"]:
            playlists.append(
                PlaylistConfig(playlist_data["id"])
            )
        return AccountConfig(
            credentials=AccountCredentialsConfig(
                client_id=account_data["credentials"]["client_id"],
                client_secret=account_data["credentials"]["client_secret"],
                refresh_token=account_data["credentials"]["refresh_token"]
            ),
            playlists=playlists
        )


class ConfigException(Exception):
    pass


class ConfigFileNotFoundError(ConfigException):
    pass


class InvalidJsonError(ConfigException):
    pass


class InvalidConfigDataError(ConfigException):
    pass
