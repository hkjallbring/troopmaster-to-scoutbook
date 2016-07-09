import ConfigParser
import argparse
import csv
import re
from pprint import pprint

#                         Camping* Partial MB Progress Matrix (2015 reqts)
newreport = re.compile(r"^\s+([a-zA-Z *]+) Partial MB Progress Matrix \((\d+) reqts\)")
req_header = re.compile(r"^\s+([0-9a-f])")
req_row = re.compile(r"^[a-zA-z]+,.*$")
blank_line = re.compile(r"^\s+$")
different_requirements = re.compile(r"^The following scouts are working on this badge using a different set of requirements")

different_reqs_first_line = re.compile(r"^\s+([a-zA-z, ]+):(\s+[0-9a-f, ]+)(:?\((\d+) reqts\))?")
different_reqs_second_line = re.compile(r"^\s+([0-9a-f, ]+)(:?\((\d+) reqts\))?")

HEADER_START_INDEX = 32


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
                req_string += requirement_index_to_name[i] + " "
                #print("{0}, {1}".format(req[0], requirement_index_to_name[i]))
        requirements.append((req[0], year, req_string))
    return requirements


def parse_record(buf, year):
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
            reqs.append((name, reqstr))
        if different_requirements.findall(line):
            different_reqs = parse_different(buf[index+1:])
            break

    requirements = process_requirements(headers, year, reqs)
    pprint(requirements)
    # pprint(headers)
    # pprint(reqs)
    pprint(different_reqs)


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
                results.append((name, year, requirements.strip()))
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

    args = parser.parse_args()

    buf = []
    record_no = 0
    report_row_index = 0
    for i, line in enumerate(args.infile):
        report = newreport.findall(line)
        if report:
            name = report[0][0]
            year = report[0][1]
            report_row_index = i
            print(report)
            if record_no > 0:
                parse_record(buf, year)
            buf = []
            buf.append(line)
            record_no += 1
        else:
            buf.append(line)
    # We will be left with one file buffer to parse, so go parse that
    # TODO: Needed?
    # parse_advancement(buf)
    parse_record(buf[report_row_index:], year)


if __name__ == '__main__':
    main()
