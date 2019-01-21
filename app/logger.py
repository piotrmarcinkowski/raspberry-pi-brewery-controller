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
            entry = [datetime.now(), level, msg]
            Logger.__logs.append(entry)
            print("{0} {1} {2}".format(entry[0], entry[1], entry[2]))
        finally:
            Logger.__lock.release()


if __name__ == "__main__":
    Logger.info('test')
