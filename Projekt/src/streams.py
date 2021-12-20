import threading
import time
from queue import Queue


class Stream:
    def __init__(self, packet_size=400):
        self._message_size = packet_size
        self.messages = Queue()

    def get_next_message(self, timeout):
        if self.messages.empty():
            return None
        else:
            return self.messages.get(timeout=timeout)

    def fill_queue(self, data: bytes):
        for i in range(0, len(data), self._message_size):
            self.messages.put(data[i:i + self._message_size])

    def prepare(self):
        pass

    def close(self):
        pass


class File(Stream):
    def __init__(self, filename, encoding="utf-8", packet_size=400):
        super().__init__(packet_size)
        with open(filename, 'r', encoding=encoding) as file:
            self._data = file.read()
            self._binary_data = bytes(self._data, encoding=encoding)

    def prepare(self):
        self.fill_queue(self._binary_data)

    def get_data(self):
        return self._data

    def get_binary_data(self):
        return self._binary_data


class Ping(Stream):
    def __init__(self, delay: int):
        """
        Simple infinite stream, which sends small message b'PING' every x seconds.

        :param delay: delay between pings
        """
        super().__init__()
        self.delay = delay
        self.stop = False

    def prepare(self):
        self.stop = False
        threading.Thread(target=lambda: self.add_message()).start()

    def get_next_message(self, timeout):
        return self.messages.get(timeout=timeout)

    def close(self):
        self.stop = True

    def add_message(self):
        while not self.stop:
            self.fill_queue(b"PING")
            time.sleep(self.delay)
