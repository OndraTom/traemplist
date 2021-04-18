import parsedatetime
from datetime import datetime


class DatetimeUtil:

    @staticmethod
    def get_guessed_time_from_string(time_in_string: str) -> datetime:
        time_struct, result = parsedatetime.Calendar(version=parsedatetime.VERSION_CONTEXT_STYLE).parse(time_in_string)
        if not result.dateTimeFlag:
            raise DatetimeUtilException("Cannot parse date: " + time_in_string)
        return datetime(*time_struct[:6])

    @staticmethod
    def get_now() -> datetime:
        return datetime.now()


class DatetimeUtilException(Exception):
    pass
