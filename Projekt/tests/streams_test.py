# Nazwa projektu: System niezawodnego strumieniowania danych po UDP
# Autorzy:        Michał Matak, Paweł Müller, Jakub Robaczewski, Grzegorz Rusinek
# Data:           14.01.2022

from streams import File


class TestDataProvider:
    def test_data_provider(self):
        data_prov = File("tests/resources/test_file.txt")
        expected_string = "1234567890\ntest\nzażółć gęsią jaźń"
        assert data_prov.get_data() == expected_string
