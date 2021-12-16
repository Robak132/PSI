from data_provider import DataProvider


class TestDataProvider:
    def test_data_provider(self):
        data_prov = DataProvider()
        assert data_prov.get_data() is None
        data_prov.from_file("resources/test_file.txt")
        expected_string = "1234567890\ntest\nzażółć gęsią jaźń"
        assert data_prov.get_data() == expected_string

