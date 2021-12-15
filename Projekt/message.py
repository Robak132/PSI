import struct
import hashlib


class Message:
    def __init__(self, message_type: str, identifier: int, data: bytes, data_hash=None):
        self.hash_algorith = hashlib.sha3_256()
        self.message_type = message_type  # 3 bytes: REQ, ERR, MSG, FIN, ACK
        self.identifier = identifier      # 4 bytes: int
        if data_hash is None:             # 8 bytes: SHA-3 hash
            self.hash_algorith.update(data)
            self.data_hash = self.hash_algorith.digest()
        else:
            self.data_hash = data_hash
        self.data = data                  # 400 bytes

    def pack(self) -> bytes:
        return struct.pack(f"3si8s400s",
                           self.message_type.encode("utf-8"),
                           self.identifier,
                           self.data_hash,
                           self.data)

    @staticmethod
    def unpack(binary_data: bytes):
        message_type, identifier, data, data_hash = struct.unpack(f"3si8s400s", binary_data)
        return Message(message_type.decode("utf-8"), identifier, data_hash, data)

    def check_hash(self) -> bool:
        self.hash_algorith.update(self.data)
        return self.hash_algorith.digest() == self.data_hash


class RequestMessage(Message):
    def __init__(self, identifier: int):
        super().__init__("REQ", identifier, b"")


class DataMessage(Message):
    def __init__(self, identifier: int, data: bytes):
        super().__init__("MSG", identifier, data)


class ACKMessage(Message):
    def __init__(self, identifier: int):
        super().__init__("ACK", identifier, b"")


class QuitMessage(Message):
    def __init__(self, identifier: int):
        super().__init__("FIN", identifier, b"")
