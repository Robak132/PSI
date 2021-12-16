class DataProvider:
    def __init__(self):
        self._data = None

    def from_file(self, filename: str):
        with open(filename, 'r', encoding='utf-8') as file:
            self._data = file.read()

    def get_data(self):
        return self._data
