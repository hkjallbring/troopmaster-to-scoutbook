import ConfigParser
import argparse
import csv
import re
from pprint import pprint

# Column names for advancement.csv
HEADER_COLUMNS = "BSA Member ID	First Name	Middle Name	Last Name	Advancement Type	Advancement	Version	Date Completed	Approved	Awarded".split("\t")

# Partial Merit Badges
# Example: Camping__Partial_MB_Progress_Matrix_(2015_reqts).txt
# Lastname, Firstname Requirement (X or blank)

# The following scouts are working on this badge using a different set of requirements. The list be

# Report > Awards/Advancement > Individual History
# [X] Include Partial MB remarks
# [Select All]
# [OK]
# [Save] as Text file
# [Save as Single File]
# [OK]
date = r'(\d+/\d+/\d+)'
newreport = re.compile(r'^Name:')
#position = re.compile(r"^Pos\\'n of Respons")
position = re.compile(r"^Pos'n of Respons")
rank_row = re.compile(r"^\s{4}\w|^\s{47}\w|^\s{47}-")
# rank_row = re.compile(r"s{4}Scout|Tenderfoot|2nd Class|1st Class|Star|Life|Eagle"
#                       r"\w+\s+\w+\s{4}\w+\s+../../..")
advancement_rank = re.compile(r"^(Scout|Tenderfoot|2nd Class|1st Class|Star|Life|Eagle)")
advancement_rank_item = re.compile(r"^(\d{1,2}[a-f]?|-)\s+([a-zA-Z /\*]+)(\d+/\d+/\d+|N/A)")

earned_mb = re.compile(r'\s+Earned Merit Badges:')
earned_mb_item = re.compile(r"([a-zA-Z \*]+)\s+(\d+/\d+/\d+)\s+")
partial_mb = re.compile(r"\s+Partial MB's")
partial_mb_item = re.compile(r"^\s+([a-zA-Z \*]+)\s+Start Date: (\d+/\d+/\d+){0,1}\s+Last Progress: (\d+/\d+/\d+){0,1}")
oa = re.compile(r'\s+Activity Summary/Order of Arrow')
oa_item = re.compile(r'(\w+)\s+')
special_awards = re.compile(r'\s+Special Awards')
special_awards_item = re.compile(r"\s+([a-zA-Z ']+)\s+(\d+/\d+/\d+)")

leadership_history = re.compile(r'^\s+Leadership History')
leadership_history_item = re.compile(r"^\s+([a-zA-Z \*]+)\s+(\d+/\d+/\d+)\s+-\s+(\d+/\d+/\d+)")
formfeed = re.compile(r"")


def parse_rank_columns(rank_columns):
    all_ranks = {}
    rank_requirements = []
    current_rank = None
    for rank_column in rank_columns:
        # print(rank_column)
        rank_match = advancement_rank.findall(rank_column)
        if rank_match:
            # finish the previous rank
            if rank_requirements:
                all_ranks[current_rank] = rank_requirements
            # start new rank
            rank_requirements = []
            current_rank = rank_match[0]
        else:
            matches = advancement_rank_item.findall(rank_column)
            if matches:
                for match in matches:
                    match = (match[0], match[1].strip(), match[2])
                    rank_requirements.append(match)
    all_ranks[current_rank] = rank_requirements
    return all_ranks


def parse_earned_mb(buf, stop_re):
    earned_mb_items = []
    for i, line in enumerate(buf):
        if stop_re.search(line):
            return i, earned_mb_items
        matches = earned_mb_item.findall(line)
        if matches:
            for match in matches:
                match = (match[0].strip(), match[1])
                earned_mb_items.append(match)
            # print(matches)


def parse_items(buf, item_re, stop_re):
    items = []
    for i, line in enumerate(buf):
        # print(line)
        if stop_re.search(line):
            # print(items)
            return i, items
        matches = item_re.findall(line)
        if matches:
            items.extend(matches)


def parse_leadership(bug, stop_re):
    pass


def parse_partial_mb(buf, stop_re):
    partial_mb_items = []
    for i, line in enumerate(buf):
        if stop_re.search(line):
            return i, partial_mb_items
        matches = partial_mb_item.findall(line)
        if matches:
            for match in matches:
                match = (match[0].strip(), match[1])
                partial_mb_items.append(match)
            # print(matches)


def parse_advancement(buf, stop_expression):
    parsing_rank = False
    rank_columns = []
    rank_column_1 = []
    rank_column_2 = []
    for i, line in enumerate(buf):
        if position.search(line):
            parsing_rank = True
        if parsing_rank:
            if stop_expression.search(line):
                rank_columns.extend(rank_column_1)
                rank_columns.extend(rank_column_2)
                advancements = parse_rank_columns(rank_columns)
                return i, advancements
            if formfeed.search(line):
                continue
            if rank_row.search(line):
                # skip empty lines
                rank_column_1.append(line[4:47])
                rank_column_2.append(line[47:].strip('\r\n'))
            else:
                rank_columns.extend(rank_column_1)
                rank_columns.extend(rank_column_2)
                # reset columns
                rank_column_1 = []
                rank_column_2 = []


def parse_record(buf):
    index, advancements = parse_advancement(buf, earned_mb)
    pprint(advancements)
    buf = buf[index:]
    index, earned_mbs = parse_earned_mb(buf, partial_mb)
    pprint(earned_mbs)
    buf = buf[index:]
    index, partial_mbs = parse_partial_mb(buf, oa)
    pprint(partial_mbs)
    buf = buf[index:]
    index, order_arrow = parse_items(buf, oa_item, special_awards)
    buf = buf[index:]
    index, special_awards_list = parse_items(buf, special_awards_item, leadership_history)


def main():

    parser = argparse.ArgumentParser(description="Process Troopmaster Advancement Reports")

    parser.add_argument('infile', type=argparse.FileType('rb'))

    args = parser.parse_args()

    buf = []
    record_no = 0
    for line in args.infile:
        if newreport.findall(line):
            if record_no > 0:
                parse_record(buf)
            buf = []
            buf.append(line)
            record_no += 1
        else:
            buf.append(line)
    # We will be left with one file buffer to parse, so go parse that
    # TODO: Needed?
    # parse_advancement(buf)
    parse_record(buf)


if __name__ == '__main__':
    main()
