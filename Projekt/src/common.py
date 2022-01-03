import logging
import threading


class StoppableThread(threading.Thread):
    """
    Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition.

    Based on: https://stackoverflow.com/questions/47912701/python-how-can-i-implement-a-stoppable-thread
    """

    def __init__(self, task):
        super().__init__()
        self._stop_event = threading.Event()
        self.task = task

        self.start()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while not self.stopped():
            self.task()


def setup_loggers(logging_level: int):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging_level)
    log_format = '%(threadName)12s:%(levelname)8s %(message)s'
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(stderr_handler)
    return logger
