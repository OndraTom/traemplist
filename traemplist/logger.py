import sys
from abc import ABC, abstractmethod


class Logger(ABC):

    @abstractmethod
    def log_info(self, message: str):
        pass

    @abstractmethod
    def log_error(self, message: str):
        pass


class StandardOutputLogger(Logger):

    def log_info(self, message: str):
        print(message, file=sys.stdout, flush=True)

    def log_error(self, message: str):
        print(message, file=sys.stderr, flush=True)
