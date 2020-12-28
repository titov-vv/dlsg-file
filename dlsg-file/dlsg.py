import re
import logging

# standard header is "DLSG            DeclYYYY0102FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", where YYYY is year of declaration
HEADER_LENGTH = 60
SIZE_LENGTH = 4
FOOTER = '\0\0'

class DLSG:
    header_pattern = "DLSG            Decl(\d{4})0102FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
    def __init__(self):
        self._year = 0
        self._records = []
        self._has_footer = False

    def dump(self):
        print(self._records)

    # Method reads declaration form a file with given filename
    # Header of file is being validated
    def read_file(self, filename):
        logging.info(f"Loading file: {filename}")

        with open(filename, "r", encoding='cp1251') as taxes:
            raw_data = taxes.read()

        self.header = raw_data[:HEADER_LENGTH]

        parts = re.match(self.header_pattern, self.header)
        if not parts:
            logging.error(f"Unexpected file header: {self.header}")
            return
        self._year = int(parts.group(1))
        logging.info(f"Declaration found for year: {self._year}")

        self.split_records(raw_data[HEADER_LENGTH:])

    # this method gets declaration data without header and splits it into a set of separate list of self._records
    def split_records(self, data):
        pos = 0

        while (pos < len(data)):
            length_field= data[pos : pos + SIZE_LENGTH]
            if length_field == FOOTER:
                self._has_footer = True
                break

            try:
                length = int(length_field)
            except Exception as e:
                logging.fatal(f"Invalid record size at position {pos+HEADER_LENGTH}: '{length_field}'")
                raise e
            pos += SIZE_LENGTH
            self._records.append(data[pos: pos + length])
            pos = pos + length

