import os
from traemplist.logger import StandardOutputLogger
from traemplist.config import JsonConfig
from traemplist.client import SpotifyClient, SpotifyAccessTokenProvider, AccountCredentialsConfig
from traemplist.generator import TraemplistGenerator
from traemplist.repository import SqLiteTracksRepository
from traemplist.service import TraemplistGeneratorService

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
    TraemplistGeneratorService(
        config=traemplist_config,
        client=spotify_client,
        generator=TraemplistGenerator(
            client=spotify_client,
            history=SqLiteTracksRepository(
                f"{this_dir_path}/storage/{account_credentials.client_id}_tracks.db"
            ),
            logger=logger
        ),
        logger=logger
    ).generate_and_save_traemplist()
