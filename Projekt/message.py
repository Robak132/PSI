import struct


class Message:
    def __init__(self, message_type: bytes, data=b"", data_size=128):
        self.message_type = message_type
        self.data = data
        self.data_size = data_size

    def pack(self) -> bytes:
        return struct.pack(f"7s{self.data_size}s", self.message_type, self.data)

    @staticmethod
    def unpack(binary_data: bytes, data_size=128):
        message_type, content = struct.unpack(f"7s{data_size}s", binary_data)
        return Message(message_type, content)