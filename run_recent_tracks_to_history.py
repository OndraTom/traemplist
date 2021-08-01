from traemplist.logger import StandardOutputLogger
from traemplist.config import JsonConfig
from traemplist.client import SpotifyClient
from traemplist.repository import SqLiteTracksRepository
from traemplist.history import TracksHistoryLoader


logger = StandardOutputLogger()
config = JsonConfig("/app/config.json")
client = SpotifyClient(credentials_config=config.get_accounts()[0].credentials)
client.register_credentials_config_change_callback(
    config.save
)
history_loader = TracksHistoryLoader(
    client=client,
    repository=SqLiteTracksRepository("/app/storage/tracks.db"),
    logger=logger
)
history_loader.save_recently_played_tracks()
