from queue import Queue


class Stream:
    def __init__(self, packet_size=400):
        self._message_size = packet_size
        self._messages = Queue()

    def get_next_message(self):
        if self._messages.empty():
            return None
        else:
            return self._messages.get()

    def fill_queue(self, data: bytes, segment_size: int):
        for i in range(0, len(data), segment_size):
            self._messages.put(data[i:i + segment_size])

    def prepare(self):
        pass


class File(Stream):
    def __init__(self, filename, packet_size=400):
        super().__init__(packet_size)
        with open(filename, 'r', encoding="utf-8") as file:
            self._data = file.read()
            self._binary_data = bytes(self._data, encoding="utf-8")

    def prepare(self):
        self.fill_queue(self._binary_data, self._message_size)

    def get_data(self):
        return self._data

    def get_binary_data(self):
        return bytes(self._data, encoding="utf-8")


class InfiniteStream(Stream):
    def __init__(self):
        super().__init__()