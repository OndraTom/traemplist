import os
import shutil
from unittest import TestCase
from uuid import uuid4
from tempfile import mkdtemp
from traemplist.config import PlaylistConfig, AccountCredentialsConfig, AccountConfig, JsonConfig


class JsonConfigTest(TestCase):

    FIXTURES_PATH = f"{os.path.dirname(os.path.abspath(__file__))}/fixtures/config"
    VALID_CONFIG_PATH = f"{FIXTURES_PATH}/valid.json"

    def setUp(self) -> None:
        self.tmp_dir = mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_success_create(self):
        config = JsonConfig(self.VALID_CONFIG_PATH)
        self.assertEqual(config.get_traemplist_songs_count(), 10)
        self.assertEqual(
            config.get_accounts(),
            [
                AccountConfig(
                    AccountCredentialsConfig(
                        client_id="valid_id",
                        client_secret="valid_secret",
                        refresh_token="valid_refresh_token",
                    ),
                    playlists=[
                        PlaylistConfig(id="playlist_a"),
                        PlaylistConfig(id="playlist_b")
                    ]
                )
            ]
        )

    def test_save_and_reload(self):
        config_file_path = self.tmp_dir + "/config.json"
        shutil.copyfile(self.VALID_CONFIG_PATH, config_file_path)
        config = JsonConfig(config_file_path)
        accounts = config.get_accounts()
        new_refresh_token = str(uuid4())
        accounts[0].credentials.refresh_token = new_refresh_token
        config.save()
        config = JsonConfig(config_file_path)
        self.assertEqual(
            config.get_accounts()[0].credentials.refresh_token,
            new_refresh_token
        )
