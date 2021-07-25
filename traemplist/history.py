from traemplist.client import SpotifyClient, TracksCollection
from traemplist.repository import TracksRepository, TrackRecord


class TracksHistoryLoader:

    def __init__(self, client: SpotifyClient, repository: TracksRepository):
        self.client = client
        self.repository = repository

    def save_recently_played_tracks(self):
        self.repository.save_tracks(
            self._tracks_to_track_records(
                self.client.get_recently_played_tracks()
            )
        )

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
