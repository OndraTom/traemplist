from traemplist.config import Config, TraemplistConfig
from traemplist.client import SpotifyClient, TracksCollection
from traemplist.repository import TracksRepository, TrackRecord
from traemplist.generator import TraemplistGenerator
from traemplist.logger import Logger


class TracksHistoryService:

    def __init__(self, client: SpotifyClient, repository: TracksRepository, logger: Logger):
        self.client = client
        self.repository = repository
        self.logger = logger

    def save_recently_played_tracks(self):
        self.logger.log_info(f"Current tracks history size: {self._tracks_total_count()}")
        self.logger.log_info("Saving recently played tracks")
        self.repository.save_tracks(
            self._tracks_to_track_records(
                self.client.get_recently_played_tracks()
            )
        )
        self.logger.log_info("Recently played tracks saved")
        self.logger.log_info(f"Current tracks history size: {self._tracks_total_count()}")

    def save_all_user_playlists_tracks(self):
        self.logger.log_info(f"Current tracks history size: {self._tracks_total_count()}")
        self.logger.log_info("Going through user playlists")
        for playlist_id in self.client.get_user_playlist_ids():
            self.logger.log_info(f"- saving tracks from playlist {playlist_id}")
            self.repository.save_tracks(
                self._tracks_to_track_records(
                    self.client.get_playlist(playlist_id)
                )
            )
        self.logger.log_info("User playlist' tracks have been saved to history")
        self.logger.log_info(f"Current tracks history size: {self._tracks_total_count()}")

    @staticmethod
    def _tracks_to_track_records(tracks: TracksCollection) -> [TrackRecord]:
        return [TrackRecord(id=track.id) for track in tracks.get_tracks()]

    def _tracks_total_count(self) -> int:
        return self.repository.tracks_total_count()


class TraemplistGeneratorService:

    def __init__(self, config: TraemplistConfig,
                 client: SpotifyClient,
                 generator: TraemplistGenerator,
                 logger: Logger):
        self.config = config
        self.client = client
        self.generator = generator
        self.logger = logger

    def generate_and_save_traemplist(self):
        self.logger.log_info(f"Generating traemplist for account {self.config.account.credentials.client_id}")
        traemplist = self.generator.generate(
            input_tracks_collection=self._get_input_tracks(),
            size=self.config.traemplist_songs_count
        )
        self.logger.log_info("Traemplist successfully generated. Uploading ..")
        self.client.replace_playlist_tracks(
            playlist_id=self.config.traemplist_id,
            new_track_ids=[track.id for track in traemplist.get_tracks()]
        )
        self.logger.log_info("Traemplist uploaded")

    def _get_input_tracks(self) -> TracksCollection:
        input_tracks = TracksCollection()
        for playlist in self.config.account.playlists:
            if playlist.id == Config.LIKED_SONGS_PLAYLIST_ID:
                input_tracks.add_tracks(
                    self.client.get_user_liked_tracks()
                )
            else:
                input_tracks.add_tracks(
                    self.client.get_playlist(playlist.id)
                )
        return input_tracks
