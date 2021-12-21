import struct
import hashlib
from enum import Enum


class MessageType(Enum):
    REQ = 0b0000001
    ERR = 0b0000010
    MSG = 0b0000100
    ACK = 0b0001000
    FIN = 0b0010000
    INF = 0b0100000


class Message:
    def __init__(self, message_type: MessageType, identifier: int, size=0, data=b"", data_hash=None):
        """
        +-----+------+---+---+---+---+---+---+---+
        |     |   0  | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
        +-----+------+---+---+---+---+---+---+---+
        |  0  | TYPE |  IDENTIFIER   |  SIZE |   |
        +-----+------+---------------+-------+---+
        |  8  |               SHA-3              |
        +-----+----------------------------------+
        |                   ...                  |
        +-----+----------------------------------+
        |  32 |               SHA-3              |
        +-----+----------------------------------+
        |  40 |               DATA               |
        +-----+----------------------------------+
        | ...                                    |
        +-----+----------------------------------+
        | 440 |               DATA               |
        +-----+----------------------------------+
        """
        self.hash_algorith = hashlib.sha3_256()
        self.message_type = message_type
        self.identifier = identifier
        self.size = size
        if data_hash is None:
            self.hash_algorith.update(data)
            self.data_hash = self.hash_algorith.digest()
        else:
            self.data_hash = data_hash
        self.data = data

    def pack(self) -> bytes:
        if self.size != 0:
            return struct.pack(f"!Bihx32s{self.size}s",
                               self.message_type.value,
                               self.identifier,
                               self.size,
                               self.data_hash,
                               self.data)
        else:
            return struct.pack(f"!Bihx",
                               self.message_type.value,
                               self.identifier,
                               self.size)

    @staticmethod
    def unpack(binary_data: bytes):
        type_value, identifier, size = struct.unpack(f"!BIHx", binary_data[:8])
        message_type = MessageType(type_value)

        data_hash = b""
        data = b""
        if size != 0:
            data_hash, data = struct.unpack(f"!8x32s{size}s", binary_data)

        return Message(message_type, identifier, size, data, data_hash)

    def check_hash(self) -> bool:
        self.hash_algorith.update(self.data)
        return self.hash_algorith.digest() == self.data_hash

    def __repr__(self):
        return f"{self.message_type.name}[{self.identifier}, {self.size}]->{self.data_hash}"


class RequestMessage(Message):
    def __init__(self, identifier: int, port: int):
        super().__init__(MessageType.REQ, identifier, 4, struct.pack("i", port))


class DataMessage(Message):
    def __init__(self, identifier: int, data=b""):
        super().__init__(MessageType.MSG, identifier, len(data), data)


class InfoMessage(Message):
    def __init__(self, identifier: int, port: int):
        super().__init__(MessageType.INF, identifier, 4, struct.pack("i", port))


class ACKMessage(Message):
    def __init__(self, identifier: int):
        super().__init__(MessageType.ACK, identifier)


class QuitMessage(Message):
    def __init__(self, identifier: int):
        super().__init__(MessageType.FIN, identifier)
