#!/usr/bin/env python3

VERSION = "0.0.0"

from os import path
import re
from xml.sax.saxutils import escape
import argparse

UNIT_RE = r"((\/[\w]+)+\.o)"
UNIT_RE_CMP = re.compile(UNIT_RE)

TYPE_RE = r":(\d+):(\d+):\s(\w+):\s*(.*)"
TYPE_RE_CMP = re.compile(TYPE_RE)


def extract_file(error):
    file_prs = error[len(error) - 1].strip()
    groups = UNIT_RE_CMP.search(file_prs)
    return path.basename(path.splitext(groups.group(0))[0])


def err_factory():
    return {
        "trace": [],
        "info": {},
        "message": []
    }


def build_err_info(err_line):
    groups = TYPE_RE_CMP.search(err_line)
    return {
        "line": groups.group(1),
        "column": groups.group(2),
        "type": groups.group(3),
        "description": groups.group(4)
    }


def parse_errors(unit):
    errors = []
    n_err = err_factory()
    err_run = False
    err_desc = False
    for raw_line in unit:
        line = raw_line.strip()
        if line.startswith('cc1plus:') or line.startswith('make'):
            continue
        if line.startswith('/') or line.startswith('In file') or line.startswith('from'):
            if not err_desc:
                err_run = True
            if err_desc:
                errors.append(n_err)
                n_err = err_factory()
                err_desc = False
            n_err['trace'].append(raw_line[:-1])
        else:
            if not err_desc:
                n_err['info'] = build_err_info(n_err['trace'][-1])
            err_desc = True
            n_err['message'].append(raw_line[:-1])
    errors.append(n_err)
    return errors


def serialize(errors, target_file):
    with open(target_file, 'w') as xml_file:
        xml_file.write('<?xml version="1.0"?>\n<testsuites>\n')
        for unit in errors:
            xml_file.write('\t<testsuite name="{name}">\n'.format(name=unit['unit']))
            count = 0
            for error in unit['errors']:
                count += 1
                err_info = error['info']
                err_type = escape(err_info['type'])
                err_desc = escape(err_info['description'])
                fail_msg = "{line}: ({level}) {message}".format(
                    line=err_info['line'],
                    level=err_type,
                    message=err_desc
                )
                xml_file.write('\t\t<testcase name="{name}-{count}">\n'.format(name=unit['unit'], count=count))
                xml_file.write('\t\t\t<failure message="{message}" type="{level}">\n\t\t\t\t'.format(message=fail_msg,
                                                                                                    level=err_type))
                xml_file.write('\n\t\t\t\t'.join([escape(x) for x in error['trace']]))
                xml_file.write('\n\t\t\t\t')
                xml_file.write('\n\t\t\t\t'.join([escape(x) for x in error['message']]))
                xml_file.write('\n\t\t\t</failure>\n')
                xml_file.write('\t\t</testcase>\n')
            xml_file.write('\t</testsuite>\n')
        xml_file.write('</testsuites>\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str,
                        help="input file", nargs='?')
    parser.add_argument("-o", "--output", type=str,
                        help="output file", default="gpptoxunit.xml")
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args()

    if args.version:
        print(VERSION)
        exit(0)

    sep_unit = []
    n_err = []
    with open(args.input_file) as err_file:
        for raw_line in err_file.readlines():
            line = raw_line.strip()
            n_err.append(raw_line)
            if line.startswith('make: ***'):
                if n_err:
                    sep_unit.append(n_err)
                    n_err = []
    proper_errs = []
    for unit in sep_unit:
        err = {}
        unit_file = extract_file(unit)
        err['unit'] = unit_file
        proper_errs.append(err)
        errors = parse_errors(unit)
        err['errors'] = errors
    serialize(proper_errs, args.output)


if __name__ == "__main__":
    main()
