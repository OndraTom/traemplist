from traemplist.client import SpotifyClient, TracksCollection, Artist, Track
from traemplist.repository import TracksRepository


class TraemplistGenerator:

    def __init__(self, client: SpotifyClient, history: TracksRepository):
        self.client = client
        self.history = history

    def generate(self, input_tracks_collection: TracksCollection, size: int) -> TracksCollection:
        """
        :raises TraemplistGeneratorException
        """
        if size < 0:
            raise InvalidTraemplistSizeError
        traemplist = TracksCollection()
        while True:
            if not input_tracks_collection:
                return traemplist
            start_track = input_tracks_collection.get_random_track()
            related_artists_tracks = self._get_related_artists_tracks(start_track.artist)
            for track in related_artists_tracks.get_tracks():
                if self._is_traemplist_candidate(track, traemplist):
                    traemplist.add_track(track)
                    if len(traemplist) >= size:
                        return traemplist
                    break
            input_tracks_collection.remove_artist_tracks(start_track.artist)

    def _get_related_artists_tracks(self, artist: Artist) -> TracksCollection:
        related_artists_tracks = TracksCollection()
        for related_artist in self.client.get_related_artists(artist.id):
            related_artists_tracks.add_tracks(
                self.client.get_artist_top_tracks(related_artist.id)
            )
        return related_artists_tracks

    def _is_traemplist_candidate(self, track: Track, traemplist: TracksCollection) -> bool:
        if self.history.contains_track(track.id):
            return False
        if traemplist.contains_artist_track(track.artist):
            return False
        return True


class TraemplistGeneratorException(Exception):
    pass


class InvalidTraemplistSizeError(TraemplistGeneratorException):

    def __str__(self) -> str:
        return "Traemplist size must be a positive integer"
