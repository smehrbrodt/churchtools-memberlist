#!/usr/bin/env python3

# Copyright (c) 2022 Samuel Mehrbrodt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse

import churchtoolsapi

from py3o.template import Template

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--filter-group", help="Filter for group ID")
parser.add_argument("--surname-from", help="Only include surname larger than this letter(s)")
parser.add_argument("--surname-to", help="Only include surname up than this letter(s)")
args = parser.parse_args()

# Create template
t = Template("template_prayerlist.odt", "gebetsblatt.odt")

# Retrieve people
persons = churchtoolsapi.get_persons(args.filter_group)

if args.surname_from:
    persons = filter(lambda p : p['lastName'] >= args.surname_from, persons)

if args.surname_to:
    persons = filter(lambda p : p['lastName'] <= args.surname_to, persons)


data = dict(persons=persons)
t.render(data)
