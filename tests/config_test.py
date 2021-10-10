import os
import shutil
from unittest import TestCase
from uuid import uuid4
from tempfile import mkdtemp
from traemplist.config import PlaylistConfig, AccountCredentialsConfig, AccountConfig, TraemplistConfig, JsonConfig, \
    ConfigFileNotFoundError, InvalidJsonError, InvalidConfigDataError


class JsonConfigTest(TestCase):

    FIXTURES_PATH = f"{os.path.dirname(os.path.abspath(__file__))}/fixtures/config"
    VALID_CONFIG_PATH = f"{FIXTURES_PATH}/valid.json"
    INVALID_JSON_CONFIG_PATH = f"{FIXTURES_PATH}/invalid_json.json"
    INVALID_DATA_CONFIG_PATH = f"{FIXTURES_PATH}/invalid_data.json"

    def setUp(self) -> None:
        self.tmp_dir = mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_success_create(self):
        config = JsonConfig(self.VALID_CONFIG_PATH)
        traemplists = config.get_traemplist_configs()
        self.assertEqual(
            traemplists,
            [
                TraemplistConfig(
                    account=AccountConfig(
                        credentials=AccountCredentialsConfig(
                            client_id="valid_id",
                            client_secret="valid_secret",
                            refresh_token="valid_refresh_token"
                        ),
                        playlists=[
                            PlaylistConfig(id="playlist_a"),
                            PlaylistConfig(id="playlist_b")
                        ]
                    ),
                    traemplist_songs_count=20,
                    traemplist_id="t_id"
                )
            ]
        )

    def test_save_and_reload(self):
        config_file_path = self.tmp_dir + "/config.json"
        shutil.copyfile(self.VALID_CONFIG_PATH, config_file_path)
        config = JsonConfig(config_file_path)
        traemplists = config.get_traemplist_configs()
        new_refresh_token = str(uuid4())
        traemplists[0].account.credentials.refresh_token = new_refresh_token
        config.save()
        config = JsonConfig(config_file_path)
        self.assertEqual(
            config.get_traemplist_configs()[0].account.credentials.refresh_token,
            new_refresh_token
        )

    def test_non_existent_file_error(self):
        config_file_path = self.tmp_dir + "/non_existent.json"
        with self.assertRaises(ConfigFileNotFoundError):
            JsonConfig(config_file_path)

    def test_invalid_json_error(self):
        with self.assertRaises(InvalidJsonError):
            JsonConfig(self.INVALID_JSON_CONFIG_PATH)

    def test_invalid_config_data_error(self):
        with self.assertRaises(InvalidConfigDataError):
            JsonConfig(self.INVALID_DATA_CONFIG_PATH)
