import re
import logging
import datetime

# standard header is "DLSG            DeclYYYY0102FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", where YYYY is year of declaration
HEADER_LENGTH = 60
SIZE_LENGTH = 4
FOOTER = '\0'
SECTION_PREFIX = '@'


class DLSGrecord:
    def __init__(self):
        self.name = ''

class DLSGDeclInfo:
    tag = 'DeclInfo'

    def __init__(self, records):
        self.inspection = records.pop(0)
        self.records = []
        while records[0][:1] != SECTION_PREFIX:
            self.records.append(records.pop(0))

class DLSGPersonName:
    tag = 'PersonName'

    def __init__(self, records):
        self.surname = records.pop(0)
        self.name = records.pop(0)
        self.middle_name = records.pop(0)
        self.inn = records.pop(0)
        self.birth_place = records.pop(0)
        self.birth_date = records.pop(0)

class DLSGHomePhone:
    tag = 'HomePhone'

    def __init__(self, records):
        self.code = records.pop(0)
        self.number = records.pop(0)

class DLSGWorkPhone:
    tag = 'WorkPhone'

    def __init__(self, records):
        self.code = records.pop(0)
        self.number = records.pop(0)

class DLSGSourseIncome:
    tag = 'SourseIncome'

    def __init__(self, records):
        self.income_code = records.pop(0)
        self.income_description = records.pop(0)
        self.amount = records.pop(0)
        self.deduction_code = records.pop(0)
        self.deduction_amount = records.pop(0)
        self.unknown = records.pop(0)
        self.month = records.pop(0)
        self.records = records[:4]
        [records.pop(0) for _ in range(4)]

class DLSGThirteenPercent:
    tag = 'ThirteenPercent'

    def __init__(self, id, records):
        self.id = id
        self.standard = records.pop(0)
        self.inn = records.pop(0)
        self.kpp = records.pop(0)
        self.oktmo = records.pop(0)
        self.name = records.pop(0)
        self.records = records[:17]
        [records.pop(0) for _ in range(17)]
        self.count = int(records.pop(0))
        self.sections = {}

        for i in range(self.count):
            section_name = records.pop(0)

            if section_name != SECTION_PREFIX + DLSGSourseIncome.tag + f"{self.id:03d}" + f"{i:03d}":
                logging.fatal(f"Invalid ThirteenPercent subsection: {section_name}")
                raise ValueError
            self.sections[i] = DLSGSourseIncome(records)

class DLSGDeclInquiry:
    tag = 'DeclInquiry'

    def __init__(self, records):
        self.count = int(records.pop(0))
        self.sections = {}

        for i in range(self.count):
            section_name = records.pop(0)

            if section_name != SECTION_PREFIX + DLSGThirteenPercent.tag + f"{i:03d}":
                logging.fatal(f"Invalid DeclInquiry subsection: {section_name}")
                raise ValueError
            self.sections[i] = DLSGThirteenPercent(i, records)

        self.records = []
        while (len(records) > 0) and (records[0][:1] != SECTION_PREFIX):
            self.records.append(records.pop(0))

class DLSGCurrencyIncome:
    tag = 'CurrencyIncome'

    # Create empty dividend
    def __init__(self, id):
        self.id = id
        self.type = '14'
        self.income_code = '1010'
        self.income_description = 'Дивиденды'
        self.description = ''
        self.country_code = '840'
        self.income_date = 0
        self.tax_payment_date = 0
        self.auto_currency_rate = '0'   # '0' = no auto currency rates
        self.currency_code = ''
        self.income_rate = 0.0
        self.income_units = 0
        self.tax_rate = 0.0
        self.tax_units = 0
        self.currency_name = ''
        self.income_currency = 0.0
        self.income_rub = 0.0
        self.tax_currency = 0.0
        self.tax_rub = 0.0
        self.records = ['0', '0', '0', '0', '', '0']

    # Created dividend based of records from file
    def __init__(self, id, records):
        self.id = id
        self.type = records.pop(0)
        self.income_code = records.pop(0)
        self.income_description = records.pop(0)
        self.description = records.pop(0)
        self.country_code = records.pop(0)
        self.income_date = int(records.pop(0))
        self.tax_payment_date = int(records.pop(0))
        self.auto_currency_rate = records.pop(0)   # '0' = no auto currency rates
        self.currency_code = records.pop(0)
        self.income_rate = float(records.pop(0))
        self.income_units = int(records.pop(0))
        self.tax_rate = float(records.pop(0))
        self.tax_units = int(records.pop(0))
        self.currency_name = records.pop(0)
        self.income_currency = float(records.pop(0))
        self.income_rub = float(records.pop(0))
        self.tax_currency = float(records.pop(0))
        self.tax_rub = float(records.pop(0))
        self.records = records[:6]
        [records.pop(0) for _ in range(6)]


class DLSGDeclForeign:
    tag = 'DeclForeign'
    currencies = {
        "USD": ('840', 'Доллар сша', 100)
    }

    def __init__(self, records):
        self.count = int(records.pop(0))
        self.sections = {}

        for i in range(self.count):
            section_name = records.pop(0)

            if section_name != SECTION_PREFIX + DLSGCurrencyIncome.tag + f"{i:03d}":
                logging.fatal(f"Invalid DeclForeign subsection: {section_name}")
                raise ValueError
            self.sections[i] = DLSGCurrencyIncome(i, records)

    def add_dividend(self, description, timestamp, currency_code, amount, amount_rub, tax, tax_rub, rate):
        currency = self.currencies[currency_code]
        dividend = DLSGCurrencyIncome(self.count)
        dividend.description = description
        dividend.income_date = (timestamp.date() - datetime.date(1899, 12, 30)).days
        dividend.tax_payment_date = dividend.income_date
        dividend.currency_code = currency[0]
        dividend.currency_name = currency[1]
        dividend.income_units = dividend.tax_units = currency[2]
        dividend.income_rate = dividend.tax_rate = rate * currency[2]
        dividend.income_currency = amount
        dividend.income_rub = amount_rub
        dividend.tax_currency = tax
        dividend.tax_rub = tax_rub
        self.sections[self.count] = dividend
        self.count += 1


class DLSGUnknownSection:
    def __init__(self, tag, records):
        self.tag = tag
        self.records = []
        while (len(records) > 0) and (records[0][:1] != SECTION_PREFIX):
            self.records.append(records.pop(0))

class DLSG:
    header_pattern = "DLSG            Decl(\d{4})0102FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
    def __init__(self):
        self._year = 0              # year of declaration
        self._records = []
        self._sections = {}
        self._footer_len = 0        # if file ends with _footer_len 0x00 bytes

    def add_dividend(self, **kwargs):
        foreign_section = self.get_section('DeclForeign')
        if foreign_section is None:
            logging.fatal(f"Declaration has now 'DeclForeign' section")
            return
        foreign_section.add_dividend(kwargs['description'], kwargs['timestamp'], kwargs['currency'],
                                     kwargs['amount'], kwargs['amount_rub'],kwargs['tax'], kwargs['tax_rub'],
                                     kwargs['tax_rate'])

    def get_section(self, name):
        for section in self._sections:
            if section.tag == name:
                return section
        return None

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
        self.split_sections()

    # this method gets declaration data without header and splits it into a set of separate list of self._records
    def split_records(self, data):
        pos = 0

        while (pos < len(data)):
            length_field = data[pos : pos + SIZE_LENGTH]

            if length_field == (FOOTER * len(length_field)):
                self._footer_len = len(length_field)
                break

            try:
                length = int(length_field)
            except Exception as e:
                logging.fatal(f"Invalid record size at position {pos+HEADER_LENGTH}: '{length_field}'")
                raise e
            pos += SIZE_LENGTH
            self._records.append(data[pos: pos + length])
            pos = pos + length

        logging.debug(f"Declaration content: {self._records}")

    def split_sections(self):
        i = 0
        while len(self._records) > 0:
            section_name = self._records.pop(0)
            if section_name[0] != SECTION_PREFIX:
                logging.fatal(f"Invalid section prefix: {section_name}")
                raise ValueError
            section_name = section_name[1:]
            if section_name == DLSGDeclInfo.tag:
                section = DLSGDeclInfo(self._records)
            elif section_name == DLSGPersonName.tag:
                section = DLSGPersonName(self._records)
            elif section_name == DLSGHomePhone.tag:
                section = DLSGHomePhone(self._records)
            elif section_name == DLSGWorkPhone.tag:
                section = DLSGWorkPhone(self._records)
            elif section_name == DLSGDeclInquiry.tag:
                section = DLSGDeclInquiry(self._records)
            elif section_name == DLSGDeclForeign.tag:
                section = DLSGDeclForeign(self._records)
            else:
                section = DLSGUnknownSection(section_name, self._records)

            self._sections[i] = section
            i += 1

        logging.debug(f"Sections loaded: {i}")
        for j in range(i):
            logging.debug(f"Section: {self._sections[j].tag}")