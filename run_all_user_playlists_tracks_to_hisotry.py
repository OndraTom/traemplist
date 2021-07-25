from traemplist.config import JsonConfig
from traemplist.client import SpotifyClient
from traemplist.repository import SqLiteTracksRepository
from traemplist.history import TracksHistoryLoader


config = JsonConfig("./config.json")
client = SpotifyClient(credentials_config=config.get_accounts()[0].credentials)
client.register_credentials_config_change_callback(
    config.save
)
history_loader = TracksHistoryLoader(
    client=client,
    repository=SqLiteTracksRepository("./tracks.db")
)
history_loader.save_all_user_playlists_tracks()
