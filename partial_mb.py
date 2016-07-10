import ConfigParser
import argparse
import csv
import re
from pprint import pprint
import scoutbook.util


#                         Camping* Partial MB Progress Matrix (2015 reqts)
newreport = re.compile(r"^\s+([a-zA-Z *]+) Partial MB Progress Matrix \((\d+) reqts\)")
req_header = re.compile(r"^\s+([0-9a-f])")
req_row = re.compile(r"^[a-zA-z]+,.*$")
blank_line = re.compile(r"^\s+$")
different_requirements = re.compile(r"^The following scouts are working on this badge using a different set of requirements")

different_reqs_first_line = re.compile(r"^\s+([a-zA-z, ]+):(\s+[0-9a-f, ]+)(:?\((\d+) reqts\))?")
different_reqs_second_line = re.compile(r"^\s+([0-9a-f, ]+)(:?\((\d+) reqts\))?")

HEADER_START_INDEX = 32


def get_name_key(lastname_comma_firstname):
    lastname, firstname = lastname_comma_firstname.split(",")
    return firstname.strip() + " " + lastname.strip()


def process_requirements(headers, year, reqs):
    requirements = []
    requirement_index_to_name = {}
    for i in range(0, len(headers[0]), 2):
        # create the requirement key
        requirement_key = ""
        for header in headers:
            requirement_key += header[i]
        requirement_key = requirement_key.strip()

        # build the map
        requirement_index_to_name[i] = requirement_key
    print(requirement_index_to_name)

    for req in reqs:
        req_string = ""
        for i in range(0, len(headers[0]), 2):
            if req[1][i] == "X":
                req_string += requirement_index_to_name[i] + ", "
                #print("{0}, {1}".format(req[0], requirement_index_to_name[i]))
        requirements.append((req[0], year, req_string))
    return requirements


def parse_record(buf, mb_name, year):
    headers = []
    reqs = []
    different_reqs = None
    for index, line in enumerate(buf):
        header = req_header.findall(line)
        if header and not reqs:
            headers.append(line[HEADER_START_INDEX:].replace("\r","").replace("\n", ""))

        row = req_row.findall(line)
        if row:
            name = line[0:30].strip()
            reqstr = line[HEADER_START_INDEX:].replace("\r","").replace("\n", "")
            reqs.append((get_name_key(name), reqstr))
        if different_requirements.findall(line):
            different_reqs = parse_different(buf[index+1:])
            break

    # pprint(headers)
    # pprint(reqs)
    requirements = process_requirements(headers, year, reqs)
    pprint(requirements)
    pprint(different_reqs)

    for r in requirements:
        format_row(r, mb_name)


onlydigits = re.compile("^(\d+)$")
digitsandletters = re.compile("^(\d+)([a-f]+)$")
digitsletterdigit = re.compile("^(\d+)([a-f]+)(\d)$")


def format_requirement(item):
    # generator
    # Valid inputs: 1, 4ab, 6abcde, 8a2
    match = onlydigits.findall(item)
    if match:
        yield "#" + item
    match = digitsandletters.findall(item)
    if match:
        digit = match[0][0]
        for letter in match[0][1]:
            yield "#" + digit + letter
    match = digitsletterdigit.findall(item)
    if match:
        digit = match[0][0]
        letter = match[0][1]
        subitem = match[0][2]
        yield "#" + digit + letter + "[{0}]".format(subitem)
    # raise Exception("Could not match: '{0}'".format(item))


def format_row(requirement, mb_name):
    name = scoutbook.util.lookup_scout_by_name(requirement[0])
    version = requirement[1]
    items = [r.strip() for r in requirement[2].split(",")]
    for item in items:
        print(item)
        for req in format_requirement(item):
            row = [
                name,
                "Merit Badge Requirement",
                mb_name + " " + req,
                version,
                "DateCompleted",
                "1",
                "0"
            ]
            print(row)


def parse_different(buf):
    name = None
    year = None
    requirements = ""
    results = []
    for i, line in enumerate(buf):
        if blank_line.findall(line):
            continue
        df1 = different_reqs_first_line.findall(line)
        df2 = different_reqs_second_line.findall(line)
        if df1:
            # TODO: Deal with first/last record
            if name and year:
                # Finish out the current record
                results.append((get_name_key(name), year, requirements.strip()))
                # Start a new record
                year = None
                requirements = ""
            item = df1[0]
            name = item[0]
            requirements += item[1]
            if len(item[3]):
                year =item[3]
        elif df2:
            item = df2[0]
            requirements += item[0]
            if len(item[2]):
                year = item[2]
    return results


def main():

    parser = argparse.ArgumentParser(description="Process Troopmaster Partial MB Progress Matrix Report")

    parser.add_argument('infile', type=argparse.FileType('rb'))
    parser.add_argument('--adult-infile', required=False, type=argparse.FileType('rb'),
                        metavar='Adult.txt', default='Adult.txt',
                        help='Troopmaster Adult export file.')
    parser.add_argument('--scout-infile', required=False, type=argparse.FileType('rb'),
                        metavar='Scout.txt', default='Scout.txt',
                        help='Troopmaster Scout export file.')
    args = parser.parse_args()

    scoutbook.util.read_scout_file(args.scout_infile)
    scoutbook.util.read_adult_file(args.adult_infile)

    buf = []
    record_no = 0
    report_row_index = 0
    year = None
    for i, line in enumerate(args.infile):
        report = newreport.findall(line)
        if report:
            mb_name = report[0][0]
            year = report[0][1]
            report_row_index = i
            print(report)
            if record_no > 0:
                parse_record(buf, mb_name, year)
            buf = []
            buf.append(line)
            record_no += 1
        else:
            buf.append(line)
    # We will be left with one file buffer to parse, so go parse that
    # TODO: Needed?
    # parse_advancement(buf)
    parse_record(buf[report_row_index:], mb_name, year)


if __name__ == '__main__':
    main()
