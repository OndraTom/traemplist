from traemplist.client import SpotifyClient, TracksCollection
from traemplist.repository import TracksRepository, TrackRecord
from traemplist.logger import Logger


class TracksHistoryLoader:

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
        for playlist_id in self.client.get_user_playlist_ids():
            self.repository.save_tracks(
                self._tracks_to_track_records(
                    self.client.get_playlist(playlist_id)
                )
            )

    @staticmethod
    def _tracks_to_track_records(tracks: TracksCollection) -> [TrackRecord]:
        return [TrackRecord(id=track.id) for track in tracks.get_tracks()]

    def _tracks_total_count(self) -> int:
        return self.repository.tracks_total_count()
