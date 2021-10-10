import os
from traemplist.logger import StandardOutputLogger
from traemplist.config import JsonConfig, AccountCredentialsConfig
from traemplist.client import SpotifyClient, SpotifyAccessTokenProvider
from traemplist.repository import SqLiteTracksRepository
from traemplist.service import TracksHistoryService


this_dir_path = os.path.dirname(os.path.abspath(__file__))
logger = StandardOutputLogger()
config = JsonConfig(f"{this_dir_path}/config.json")

for traemplist_config in config.get_traemplist_configs():
    account_credentials = traemplist_config.account.credentials
    spotify_client = SpotifyClient(
        access_token_provider=SpotifyAccessTokenProvider(
            AccountCredentialsConfig(
                client_id=account_credentials.client_id,
                client_secret=account_credentials.client_secret,
                refresh_token=account_credentials.refresh_token
            )
        )
    )
    TracksHistoryService(
        client=spotify_client,
        repository=SqLiteTracksRepository(
            f"{this_dir_path}/storage/{account_credentials.client_id}_tracks.db"
        ),
        logger=logger
    ).save_all_user_playlists_tracks()
