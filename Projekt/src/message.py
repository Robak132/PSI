import struct
import hashlib


class Message:
    def __init__(self, message_type: str, identifier: int, size=0, data=b"", data_hash=None):
        """
        +-----+---+---+---+---+---+---+---+---+---+---+----+----+----+----+----+----+
        |     | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
        +-----+---+---+---+---+---+---+---+---+---+---+----+----+----+----+----+----+
        |  0  |    TYPE   |   IDENTIFIER  |      SIZE      |          SHA-3         |
        +-----+-----------+---------------+----------------+------------------------+
        |  16 |                                SHA-3                                |
        +-----+--------------------------------------------+------------------------+
        |  32 |                    SHA-3                   |          DATA          |
        +-----+--------------------------------------------+------------------------+
        |                                    ...                                    |
        +-----+--------------------------------------------+----+----+----+----+----+
        | 384 |                    DATA                    |    |    |    |    |    |
        +-----+--------------------------------------------+----+----+----+----+----+
        """
        self.hash_algorith = hashlib.sha3_256()
        self.message_type = message_type    # 3 bytes: REQ, ERR, MSG, FIN, ACK, INF
        self.identifier = identifier        # 4 bytes: int
        self.size = size                    # 4 bytes: int
        if data_hash is None:               # 32 bytes: SHA-3 hash
            self.hash_algorith.update(data)
            self.data_hash = self.hash_algorith.digest()
        else:
            self.data_hash = data_hash
        self.data = data                    # 400 bytes

    def pack(self) -> bytes:
        return struct.pack(f"3sii32s{self.size}s",
                           self.message_type.encode("utf-8"),
                           self.identifier,
                           self.size,
                           self.data_hash,
                           self.data)

    @staticmethod
    def unpack(binary_data: bytes):
        message_type, identifier, size = struct.unpack(f"3sii{len(binary_data)-12}x", binary_data)

        data_hash = None
        data = b""
        if size != 0:
            data_hash, data = struct.unpack(f"!32s{size}s", binary_data[8:])

        return Message(message_type.decode("utf-8"), identifier, size, data, data_hash)

    def check_hash(self) -> bool:
        self.hash_algorith.update(self.data)
        return self.hash_algorith.digest() == self.data_hash


class RequestMessage(Message):
    def __init__(self, identifier: int, port: int):
        super().__init__("REQ", identifier, 4, struct.pack("i", port))


class DataMessage(Message):
    def __init__(self, identifier: int, data=b""):
        super().__init__("MSG", identifier, len(data), data)


class InfoMessage(Message):
    def __init__(self, identifier: int, port: int):
        super().__init__("INF", identifier, 4, struct.pack("i", port))


class ACKMessage(Message):
    def __init__(self, identifier: int):
        super().__init__("ACK", identifier)


class QuitMessage(Message):
    def __init__(self, identifier: int):
        super().__init__("FIN", identifier)
