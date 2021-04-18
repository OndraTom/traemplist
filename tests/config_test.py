import os
from unittest import TestCase
from traemplist.utils import DatetimeUtil
from traemplist.config import PlaylistConfig, AccountConfig, HistoryConfig, Config, ConfigFactory


class ConfigFactoryTest(TestCase):

    FIXTURES_PATH = f"{os.path.dirname(os.path.abspath(__file__))}/fixtures/config"
    VALID_CONFIG_PATH = f"{FIXTURES_PATH}/valid.json"

    @classmethod
    def setUpClass(cls) -> None:
        cls.config_factory = ConfigFactory()

    def test_success_create(self):
        self.assertEqual(
            self.config_factory.create_from_file(self.VALID_CONFIG_PATH),
            Config(
                accounts=[
                    AccountConfig(
                        access_token="valid_access_token",
                        playlists=[
                            PlaylistConfig(id="playlist_a"),
                            PlaylistConfig(id="playlist_b")
                        ]
                    )
                ],
                history=HistoryConfig(
                    since=DatetimeUtil.get_guessed_time_from_string("-10 days")
                ),
                traemplist_songs_count=10
            )
        )
