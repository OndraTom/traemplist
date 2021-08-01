from traemplist.logger import StandardOutputLogger
from traemplist.config import JsonConfig
from traemplist.client import SpotifyClient
from traemplist.repository import SqLiteTracksRepository
from traemplist.service import TracksHistoryService


config = JsonConfig("/app/config.json")
client = SpotifyClient(credentials_config=config.get_accounts()[0].credentials)
client.register_credentials_config_change_callback(
    config.save
)
history_loader = TracksHistoryService(
    client=client,
    repository=SqLiteTracksRepository("/app/storage/tracks.db"),
    logger=StandardOutputLogger()
)
history_loader.save_all_user_playlists_tracks()
