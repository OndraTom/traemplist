import json
import jsonschema
from dataclasses import dataclass
from datetime import datetime
from traemplist.utils import DatetimeUtil, DatetimeUtilException


@dataclass(frozen=True)
class PlaylistConfig:
    id: str


@dataclass(frozen=True)
class AccountConfig:
    access_token: str
    playlists: [PlaylistConfig]


@dataclass(frozen=True)
class HistoryConfig:
    since: datetime


@dataclass(frozen=True)
class Config:
    accounts: [AccountConfig]
    history: HistoryConfig
    traemplist_songs_count: int


class ConfigFactory:

    SCHEMA = {
        "type": "object",
        "properties": {
            "traemplist_songs_count": {
                "type": "integer",
                "minimum": 10,
                "maximum": 200
            },
            "history": {
                "type": "object",
                "properties": {
                    "since": {
                        "type": "string"
                    }
                },
                "required": [
                    "since"
                ]
            },
            "accounts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "access_token": {
                            "type": "string"
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
                        "access_token",
                        "playlists"
                    ]
                },
                "minItems": 1
            }
        },
        "required": [
            "traemplist_songs_count",
            "history"
        ]
    }

    def create_from_file(self, config_file_path: str) -> Config:
        """
        :raises ConfigFactoryException
        """
        config_data = self._get_config_data(config_file_path)
        self._validate_config_data(config_data)
        return self._get_config_from_data(config_data)

    @staticmethod
    def _get_config_data(config_file_path: str) -> dict:
        try:
            with open(config_file_path) as config_file:
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

    def _get_config_from_data(self, config_data: dict) -> Config:
        return Config(
            accounts=self._get_accounts_from_data(config_data),
            history=self._get_history_from_data(config_data),
            traemplist_songs_count=config_data["traemplist_songs_count"]
        )

    @staticmethod
    def _get_accounts_from_data(config_data: dict) -> [AccountConfig]:
        accounts = []
        for account_data in config_data["accounts"]:
            playlists = []
            for playlist_data in account_data["playlists"]:
                playlists.append(
                    PlaylistConfig(playlist_data["id"])
                )
            accounts.append(
                AccountConfig(
                    access_token=account_data["access_token"],
                    playlists=playlists
                )
            )
        return accounts

    @staticmethod
    def _get_history_from_data(config_data: dict) -> HistoryConfig:
        try:
            since = DatetimeUtil.get_guessed_time_from_string(config_data["history"]["since"])
            if since > DatetimeUtil.get_now():
                raise InvalidConfigDataError
            return HistoryConfig(
                since=since
            )
        except DatetimeUtilException:
            raise InvalidConfigDataError


class ConfigFactoryException(Exception):
    pass


class ConfigFileNotFoundError(ConfigFactoryException):
    pass


class InvalidJsonError(ConfigFactoryException):
    pass


class InvalidConfigDataError(ConfigFactoryException):
    pass
