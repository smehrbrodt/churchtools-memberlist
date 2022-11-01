#!/usr/bin/env python3

# Copyright (c) 2022 Samuel Mehrbrodt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import datetime

import churchtoolsapi

from py3o.template import Template

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--group-members", help="Group ID where to find Church members")
parser.add_argument("--group-regular-visitors", help="Group ID where to find regular visitors")
parser.add_argument("--role-id-regularvisitors", help="Only visitors with this role ID")
parser.add_argument("--group-visitors", help="Group ID where to find sporadic visitors")
parser.add_argument("--role-id-visitors", help="Only visitors with this role ID")
parser.add_argument("--date", help="Service date. Format: YYYY-MM-DD; e.g. '2022-05-21'")
parser.add_argument("--template", default="template_attendancereport.odt", help="custom template file (odt)")
parser.add_argument("--output", default="attendancereport.odt", help="output file (odt)")
args = parser.parse_args()

def is_absent(member):
    return member.present == False

def get_two_weeks_absent(meeting_members):
    thisWeekAbsent = set(filter(is_absent, meeting_members[0]))
    lastWeekAbsent = set(filter(is_absent, meeting_members[1]))
    return sorted(thisWeekAbsent.intersection(lastWeekAbsent))

def get_last_eight_weeks_absent(meeting_members):
    meetings_only_absent_members = []
    for members in meeting_members:
        meetings_only_absent_members.append(filter(is_absent, members))

    members_with_absent_count = []
    for members in meetings_only_absent_members:
        for member in members:
            if member in members_with_absent_count:
                m = members_with_absent_count[members_with_absent_count.index(member)]
                m.absentCount += 1
                continue
            member.absentCount = 1
            members_with_absent_count.append(member)

    return list(filter(lambda member: member.absentCount >= 4, members_with_absent_count))

def get_present(meeting_members):
    return list(filter(lambda member: member.present == True, meeting_members))

# Create template
t = Template(args.template, args.output)

orig_meeting_date = churchtoolsapi.str_to_date(args.date)

## Fetch members data
# This week = meeting_members[0], 8 weeks ago = meeting_members[7]
meeting_members = []
meeting_members_stats = []
for nWeek in range(8):
    meeting_date = orig_meeting_date + datetime.timedelta(weeks=-(nWeek))
    meeting = churchtoolsapi.get_group_meeting(args.group_members, meeting_date)
    meeting_members_stats.append(meeting)
    meeting_members.append(churchtoolsapi.get_meeting_members(args.group_members, meeting['id']))

## Fetch regular visitors data
meeting_regular_visitors = []
meeting_regular_visitors_stats = []
for nWeek in range(2):
    meeting_date = orig_meeting_date + datetime.timedelta(weeks=-(nWeek))
    meeting = churchtoolsapi.get_group_meeting(args.group_regular_visitors, meeting_date)
    meeting_regular_visitors_stats.append(meeting)
    meeting_regular_visitors.append(
        churchtoolsapi.get_meeting_members(
            args.group_regular_visitors,
            meeting['id'],
            args.role_id_regularvisitors))

## Fetch other visitors data
#other_visitors = churchtoolsapi.get_persons(args.group_visitors, args.role_id_visitors)

# Member absences
twoWeeksAbsentMembers = get_two_weeks_absent(meeting_members)
fourTimesInEightWeeksAbsent = get_last_eight_weeks_absent(meeting_members)

# Regular visitors absences
presentRegularVisitors_ = get_present(meeting_regular_visitors[0])
twoWeeksAbsentRegularVisitors = get_two_weeks_absent(meeting_regular_visitors)

# Other visitors
other_visitors = (meeting_members_stats[0]['comment'] + meeting_regular_visitors_stats[0]['comment']).split("\n")

data = dict(
    meetingDate=churchtoolsapi.format_date(args.date),
    membersPresentCount = meeting_members_stats[0]['statistics']['present'],
    membersAbsentCount = meeting_members_stats[0]['statistics']['absent'],
    numGuests = meeting_members_stats[0]['numGuests'],
    absentLastTwoSundays = twoWeeksAbsentMembers,
    absentLastEightWeeks = fourTimesInEightWeeksAbsent,
    absentVisitorsLastTwoSundays = twoWeeksAbsentRegularVisitors,
    presentRegularVisitors = presentRegularVisitors_,
    regularVisitorsPresentCount = meeting_regular_visitors_stats[0]['statistics']['present'],
    regularVisitorsAbsentCount = meeting_regular_visitors_stats[0]['statistics']['absent'],
    presentVisitors = meeting_regular_visitors_stats[0]['comment'].split("\n")
)

t.render(data)
