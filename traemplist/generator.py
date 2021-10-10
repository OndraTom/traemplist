from traemplist.client import SpotifyClient, TracksCollection, Artist, Track
from traemplist.repository import TracksRepository
from traemplist.logger import Logger


class TraemplistGenerator:

    def __init__(self, client: SpotifyClient, history: TracksRepository, logger: Logger):
        self.client = client
        self.history = history
        self.logger = logger

    def generate(self, input_tracks_collection: TracksCollection, size: int) -> TracksCollection:
        """
        :raises TraemplistGeneratorException
        """
        if size < 0:
            raise InvalidTraemplistSizeError
        traemplist = TracksCollection()
        while True:
            if not input_tracks_collection:
                self.logger.log_info("Input tracks collection is empty - generating done")
                return traemplist
            start_track = input_tracks_collection.get_random_track()
            self.logger.log_info(f"Randomly picked track: '{start_track.artist.name} - {start_track.name}'")
            self.logger.log_info("Loading top related artists' tracks")
            related_artists_tracks = self._get_related_artists_tracks(start_track.artist)
            for track in related_artists_tracks.get_tracks():
                if self._is_traemplist_candidate(track, traemplist):
                    self.logger.log_info(f"'{track.artist.name} - {track.name}' seems like a good choice, adding")
                    traemplist.add_track(track)
                    if len(traemplist) >= size:
                        return traemplist
                    break
            input_tracks_collection.remove_artist_tracks(start_track.artist)

    def _get_related_artists_tracks(self, artist: Artist) -> TracksCollection:
        related_artists_tracks = TracksCollection()
        for related_artist in self.client.get_related_artists(artist_id=artist.id):
            related_artists_tracks.add_tracks(
                self.client.get_artist_top_tracks(artist_id=related_artist.id)
            )
        return related_artists_tracks

    def _is_traemplist_candidate(self, track: Track, traemplist: TracksCollection) -> bool:
        if self.history.contains_track(track.id):
            self.logger.log_info(f"You've already heard '{track.artist.name} - {track.name}', skipping")
            return False
        if traemplist.contains_artist_track(track.artist):
            self.logger.log_info(f"Artist '{track.artist.name}' is already in traemplist, skipping")
            return False
        return True


class TraemplistGeneratorException(Exception):
    pass


class InvalidTraemplistSizeError(TraemplistGeneratorException):

    def __str__(self) -> str:
        return "Traemplist size must be a positive integer"
