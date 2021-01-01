#!/usr/bin/python

import logging
import os
import argparse
import datetime
from dlsg import DLSG


def get_cmd_line_agurments():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] [FILE]...",
        description="DLSG file parser"
    )
    parser.add_argument('--file', required=True, metavar="FILE .dcX", help="Name of file to parse")
    parser.add_argument('--output', required=True, metavar="FILE .dcX", help="Name of file to write")
    return parser.parse_args()

def main():
    LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
    logging.basicConfig(level=LOGLEVEL)

    args = get_cmd_line_agurments()
    statement = DLSG()
    statement.read_file(args.file)
    
    statement.add_dividend(description="TEST", timestamp=datetime.date(2020, 12, 1), currency='USD', amount=123,
           amount_rub=654, tax=11, tax_rub=65, tax_rate=75)

    statement.write_file(args.output)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

