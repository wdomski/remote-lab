#!/usr/bin/python3

import csv
from collections import namedtuple
import json

def read_csv(filename, hostname=''):
    items = []
    try:
        with open(filename, 'r') as file:
            f_csv = csv.reader(file)
            headings = next(f_csv)
            item = namedtuple('Row', headings)
            for r in f_csv:
                if len(r) > 0:
                    commented_line = False
                    if len(r[0]) > 0:
                        if r[0][0] == '#':
                            commented_line = True
                    if not commented_line:
                        row = item(*r)
                        row = dict(row._asdict())
                        if hostname == "" or hostname == row['server']:
                            items.append(row)

    except FileNotFoundError:
        pass

    return items

def read_json(filename, hostname=''):
    items = []
    data = []
    try:
        with open(filename, 'r') as file:
            data = json.loads(file.read())
    except FileNotFoundError:
        pass

    if len(data) > 0:
        for entry in data:
            if hostname == "" or hostname == entry['server'] or hostname == "all":
                items.append(entry)

    return items
