# Nazwa projektu: System niezawodnego strumieniowania danych po UDP
# Autorzy:        Michał Matak, Paweł Müller, Jakub Robaczewski, Grzegorz Rusinek
# Data:           14.01.2022

from message import DataMessage


class TestHash:
    def test_hash_type(self):
        message = DataMessage(0, "Wlazł kotek na płotek i mruga".encode("utf-8"))
        assert type(message.data_hash) == bytes

    def test_hash_size(self):
        message = DataMessage(0, "Wlazł kotek na płotek i mruga".encode("utf-8"))
        assert len(message.data_hash) == 32

    def test_hash_working(self):
        message = DataMessage(0, "Wlazł kotek na płotek i mruga".encode("utf-8"))
        message2 = DataMessage(1, "Wlazł kotek na płotek i mruga".encode("utf-8"))
        assert message.data_hash == message2.data_hash
