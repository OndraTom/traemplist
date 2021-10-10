import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class TrackRecord:
    id: str


class TracksRepository(ABC):

    @abstractmethod
    def save_tracks(self, tracks: [TrackRecord]) -> None:
        pass

    @abstractmethod
    def contains_track(self, track_id: str) -> bool:
        pass

    @abstractmethod
    def tracks_total_count(self) -> int:
        pass


class SqLiteTracksRepository(TracksRepository):

    def __init__(self, db_file_path: str):
        self.db_file_path = db_file_path
        self.lock = Lock()
        self._init_tracks_table()

    def save_tracks(self, tracks: [TrackRecord]) -> None:
        if not tracks:
            return
        self.lock.acquire()
        try:
            with self._get_connection() as connection:
                cursor = connection.cursor()
                values = ",".join([f"('{track.id}')" for track in tracks])
                cursor.execute(
                    f"""
                    INSERT INTO tracks(id) VALUES {values}
                    ON CONFLICT(id) DO NOTHING
                    """
                )
        finally:
            self.lock.release()

    def contains_track(self, track_id: str) -> bool:
        self.lock.acquire()
        try:
            with self._get_connection() as connection:
                cursor = connection.cursor()
                return cursor.execute(
                    f"SELECT COUNT(*) FROM tracks WHERE id = '{track_id}'"
                ).fetchone()[0] > 0
        finally:
            self.lock.release()

    def tracks_total_count(self) -> int:
        self.lock.acquire()
        try:
            with self._get_connection() as connection:
                cursor = connection.cursor()
                return cursor.execute(
                    f"SELECT COUNT(*) FROM tracks"
                ).fetchone()[0]
        finally:
            self.lock.release()

    def _init_tracks_table(self):
        self.lock.acquire()
        try:
            with self._get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tracks (
                        id TEXT PRIMARY KEY
                    )
                    """
                )
        finally:
            self.lock.release()

    def _get_connection(self):
        return sqlite3.connect(self.db_file_path)


class InMemoryTracksRepository(TracksRepository):

    def __init__(self):
        self.tracks = []
        self.lock = Lock()

    def save_tracks(self, tracks: [TrackRecord]) -> None:
        if not tracks:
            return
        self.lock.acquire()
        try:
            for track in tracks:
                if not self._contains_track(track.id, use_lock=False):
                    self.tracks.append(track)
        finally:
            self.lock.release()

    def contains_track(self, track_id: str) -> bool:
        return self._contains_track(track_id, use_lock=True)

    def _contains_track(self, track_id: str, use_lock: bool) -> bool:
        if use_lock:
            self.lock.acquire()
        try:
            for track in self.tracks:
                if track.id == track_id:
                    return True
            return False
        finally:
            if use_lock:
                self.lock.release()

    def tracks_total_count(self) -> int:
        self.lock.acquire()
        try:
            return len(self.tracks)
        finally:
            self.lock.release()


class TracksRepositoryException(Exception):
    pass
