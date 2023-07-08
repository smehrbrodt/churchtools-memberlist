#!/usr/bin/env python3

# Copyright (c) 2022 Samuel Mehrbrodt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import datetime

import dateutil.relativedelta as relativedelta

import churchtoolsapi

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--group-members", help="Group ID where to find Church members")
parser.add_argument("--group-regularvisitors", help="Group ID where to find regular visitors")
parser.add_argument("--role-id-regularvisitors", help="Only visitors with this role ID")
parser.add_argument("--group-visitors", help="Group ID where to find other visitors")
parser.add_argument("--role-id-visitors", help="Only visitors with this role ID")
args = parser.parse_args()

# Members
members_sorted = churchtoolsapi.get_persons(args.group_members)

# Regular visitors
regularvisitors_sorted = churchtoolsapi.get_persons(args.group_regularvisitors, args.role_id_regularvisitors)

next_sunday = datetime.date.today()
if next_sunday.weekday() != 6: # Sunday
    next_sunday += relativedelta.relativedelta(days=1, weekday=relativedelta.SU)
next_sunday_date = next_sunday.strftime("%d.%m.%Y")

# Highlight recent birthdays
for member in members_sorted + regularvisitors_sorted:
    birthday = member['birthday_date']
    if birthday and birthday != '1900-01-01 00:00:00':
        birthday = birthday.replace(year=next_sunday.year)
        delta = (next_sunday - birthday)
        if delta.days < 7 and delta.days >= 0:
            print("{} {} {}".format(member['firstName'], member['lastName'], birthday.strftime("%d.%m.")))

