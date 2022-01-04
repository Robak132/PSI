from streams import File


class TestDataProvider:
    def test_data_provider(self):
        data_prov = File("tests/resources/test_file.txt")
        expected_string = "1234567890\r\ntest\r\nzażółć gęsią jaźń"
        assert data_prov.get_data("utf-8") == expected_string
