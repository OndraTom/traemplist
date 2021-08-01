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


class TracksRepositoryException(Exception):
    pass
