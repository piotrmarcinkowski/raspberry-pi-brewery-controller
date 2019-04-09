from datetime import datetime
from threading import Lock

LEVEL_INFO = 'info'
LEVEL_ERROR = 'error'


class Logger(object):
    __logs = []
    __lock = Lock()

    @staticmethod
    def info(msg: str):
        Logger.__append_log(LEVEL_INFO, msg)

    @staticmethod
    def error(msg: str):
        Logger.__append_log(LEVEL_ERROR, msg)

    @staticmethod
    def clear():
        Logger.__lock.acquire()
        try:
            Logger.__logs.clear()
        finally:
            Logger.__lock.release()

    @staticmethod
    def get_logs():
        Logger.__lock.acquire()
        try:
            return Logger.__logs.copy()
        finally:
            Logger.__lock.release()

    @staticmethod
    def __append_log(level: str, msg: str):
        Logger.__lock.acquire()
        try:
            entry = LogEntry(datetime.now(), level, msg)
            Logger.__logs.append(entry)
            print(str(entry))
        finally:
            Logger.__lock.release()


class LogEntry(object):
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, date, level, message):
        self.date = date
        self.level = level
        self.message = message

    def to_json_data(self):
        return {"date": self.date.strftime(LogEntry.DATE_FORMAT),
                "level": self.level,
                "msg": self.message}

    def __str__(self) -> str:
        return "{0} {1} {2}".format(self.date, self.level, self.message)


if __name__ == "__main__":
    Logger.info('test')
