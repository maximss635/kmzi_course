import logging
import os.path
import threading


class WithLogger:
    def __init__(self, filename="", to_console=False):
        self._logger = logging.getLogger(self.__class__.__name__)

        formatter = logging.Formatter("%(levelname)s [%(name)s] %(message)s")

        if filename:
            if filename[-4:] != ".log":
                filename += ".log"
            if not os.path.exists("logs"):
                os.makedirs("logs")
            handler = logging.FileHandler("logs/" + filename)
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

        if to_console:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

        self._logger.setLevel(logging.DEBUG)


def call_with_lock(func):
    lock = threading.Lock()

    def wrap(*args, **kwargs):
        lock.acquire()
        try:
            ret = func(*args, **kwargs)
        except BaseException as err:
            raise err
        finally:
            lock.release()

        return ret

    return wrap
