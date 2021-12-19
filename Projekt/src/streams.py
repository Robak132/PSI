class Stream:
    def __init__(self, packet_size=400):
        self._message_size = packet_size
        self._message_idx = -1
        self._messages = []

    def get_next_message(self):
        self._message_idx += 1
        if self._message_idx < len(self._messages):
            return self._messages[self._message_idx]
        else:
            return None

    def add_messages(self, data: bytes, segment_size: int):
        for i in range(0, len(data), segment_size):
            self._messages.append(data[i:i + segment_size])


class File(Stream):
    def __init__(self, filename, packet_size=400):
        super().__init__(packet_size)
        with open(filename, 'r', encoding="utf-8") as file:
            self._data = file.read()
            binary_data = bytes(self._data, encoding="utf-8")
            self.add_messages(binary_data, packet_size)

    def get_data(self):
        return self._data

    def get_binary_data(self):
        return bytes(self._data, encoding="utf-8")


class InfiniteStream(Stream):
    def __init__(self):
        super().__init__()