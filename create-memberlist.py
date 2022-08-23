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
parser.add_argument("--template", default="template_memberlist.odt", help="custom template file (odt)")
parser.add_argument("--output", default="memberlist.odt", help="output file (odt)")
args = parser.parse_args()

# Create template
t = Template(args.template, args.output)

# Sort persons by their family
persons_sorted = churchtoolsapi.get_persons(args.filter_group)

data = dict(persons=persons_sorted)
t.render(data)
