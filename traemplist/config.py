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


class Config(ABC):

    LIKED_SONGS_PLAYLIST_ID = "liked_songs"

    @abstractmethod
    def get_traemplist_songs_count(self) -> int:
        pass

    @abstractmethod
    def get_accounts(self) -> [AccountConfig]:
        pass

    @abstractmethod
    def get_traemplist_id(self) -> str:
        pass

    @abstractmethod
    def save(self) -> None:
        pass


class JsonConfig(Config):

    SCHEMA = {
        "type": "object",
        "properties": {
            "traemplist_songs_count": {
                "type": "integer",
                "minimum": 10,
                "maximum": 200
            },
            "accounts": {
                "type": "array",
                "items": {
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
                "minItems": 1
            },
            "traemplist_id": {
                "type": "string"
            }
        },
        "required": [
            "traemplist_songs_count",
            "accounts",
            "traemplist_id"
        ]
    }

    def __init__(self, config_file_path: str):
        self.config_file_path = config_file_path
        self.config_data = self._get_config_data()
        self._validate_config_data(self.config_data)
        self.accounts = self._get_accounts_from_data()

    def get_traemplist_songs_count(self) -> int:
        return self.config_data["traemplist_songs_count"]

    def get_accounts(self) -> [AccountConfig]:
        return self.accounts

    def get_traemplist_id(self) -> str:
        return self.config_data["traemplist_id"]

    def save(self) -> None:
        self.config_data["accounts"] = [asdict(account) for account in self.accounts]
        with open(self.config_file_path, "w") as config_file:
            config_file.write(
                json.dumps(self.config_data, indent=2)
            )

    def _get_config_data(self) -> dict:
        try:
            with open(self.config_file_path) as config_file:
                return json.load(config_file)
        except FileExistsError:
            raise ConfigFileNotFoundError
        except json.JSONDecodeError:
            raise InvalidJsonError

    def _validate_config_data(self, config_data: dict):
        try:
            jsonschema.validate(config_data, self.SCHEMA)
        except jsonschema.ValidationError:
            raise InvalidConfigDataError

    def _get_accounts_from_data(self) -> [AccountConfig]:
        accounts = []
        for account_data in self.config_data["accounts"]:
            playlists = []
            for playlist_data in account_data["playlists"]:
                playlists.append(
                    PlaylistConfig(playlist_data["id"])
                )
            accounts.append(
                AccountConfig(
                    credentials=AccountCredentialsConfig(
                        client_id=account_data["credentials"]["client_id"],
                        client_secret=account_data["credentials"]["client_secret"],
                        refresh_token=account_data["credentials"]["refresh_token"]
                    ),
                    playlists=playlists
                )
            )
        return accounts


class ConfigException(Exception):
    pass


class ConfigFileNotFoundError(ConfigException):
    pass


class InvalidJsonError(ConfigException):
    pass


class InvalidConfigDataError(ConfigException):
    pass
