from traemplist.logger import StandardOutputLogger
from traemplist.config import JsonConfig
from traemplist.client import SpotifyClient
from traemplist.generator import TraemplistGenerator
from traemplist.repository import SqLiteTracksRepository
from traemplist.service import TraemplistGeneratorService

logger = StandardOutputLogger()
config = JsonConfig("./config.json")
client = SpotifyClient(credentials_config=config.get_accounts()[0].credentials)
tracks_repository = SqLiteTracksRepository("./storage/tracks.db")
generator = TraemplistGenerator(
    client=client,
    history=tracks_repository
)
service = TraemplistGeneratorService(
    config=config,
    client=client,
    history=tracks_repository,
    generator=generator,
    logger=logger
)
service.generate_and_save_traemplist()
