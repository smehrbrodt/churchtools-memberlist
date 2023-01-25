#!/usr/bin/env python3

# Copyright (c) 2022 Samuel Mehrbrodt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import io
import pickle
import os
import requests

from dotenv import load_dotenv
from os.path import exists
from PIL import Image, ImageDraw, ImageFilter
from pyactiveresource.activeresource import ActiveResource

# DEBUG MODE (cache REST API result)
DEBUG = False
CACHED_FILENAME = "persons_{group_id}.dump"

# Random limits from Churchtools API
MAX_PERSONS_LIMIT = 500
MAX_GROUP_MEMBERS_LIMIT = 100

load_dotenv()

# REST API definitions
class ApiBase(ActiveResource):
    _site = 'https://' + os.getenv('CHURCHTOOLS_DOMAIN') + '/api/'
    _headers = { 'Authorization': 'Login ' + os.getenv('CHURCHTOOLS_LOGIN_TOKEN') }

class Group(ApiBase):
    pass

class Person(ApiBase):
    pass

class Child:
    def __lt__(self, other):
        return self.birthdate > other.birthdate

    def __str__(self):
        return self.name + self.age

def str_to_date(birthdate_str):
    if not birthdate_str:
        return datetime.datetime(1900, 1, 1)
    return datetime.datetime.strptime(birthdate_str, "%Y-%m-%d").date()

def __age(birthdate_str):
    if not birthdate_str:
        return ""
    birthdate = str_to_date(birthdate_str)
    today = datetime.date.today()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

def format_date(birthdate_str):
    if not birthdate_str:
        return ""
    birthdate = str_to_date(birthdate_str)
    return birthdate.strftime("%d.%m.%Y")

# From https://note.nkmk.me/en/python-pillow-square-circle-thumbnail/
def __mask_circle_transparent(pil_img, blur_radius, offset=0):
    offset = blur_radius * 2 + offset
    mask = Image.new("L", pil_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((offset, offset, pil_img.size[0] - offset, pil_img.size[1] - offset), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

    result = pil_img.copy()
    result.putalpha(mask)

    return result

def __make_img_round(img_bytes):
    im = Image.open(io.BytesIO(img_bytes))
    im_round = __mask_circle_transparent(im, 0, 2)
    img_byte_arr = io.BytesIO()
    im_round.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


def get_persons(filter_group_id=None, filter_role_id=None, include_images=False):
    filter_group_id = int(filter_group_id) if filter_group_id else None
    filter_role_id = int(filter_role_id) if filter_role_id else None
    filename = CACHED_FILENAME.format(group_id=filter_group_id)
    if DEBUG and exists(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)

    # Get all persons
    persons_result = Person.find(from_=ApiBase._site + 'persons', limit=MAX_PERSONS_LIMIT)
    persons = persons_result[0]['data']

    # Filter only those in current group
    if filter_group_id:
        persons_filtered = []
        group_url = ApiBase._site + 'groups/{id}/members'.format(id=filter_group_id)
        persons_in_group_result = Group.find(from_=group_url, limit=MAX_GROUP_MEMBERS_LIMIT)
        persons_in_group = persons_in_group_result[0]['data']
        # Remove persons not in this group from persons
        for person in persons:
            found = False
            for group_person in persons_in_group:
                if group_person['personId'] == person['id']:
                    found = True

                if filter_role_id:
                    found = found and group_person['groupTypeRoleId'] == filter_role_id

                if found:
                    break
            if found:
                persons_filtered.append(person)
        persons = persons_filtered

    # Postprocessing
    for person in persons:
        # Profile pic
        if include_images:
            if person['imageUrl']:
                person['image'] = requests.get(person['imageUrl']).content
            else:
                default_img_path = os.path.realpath(os.path.dirname(__file__)) + '/images/placeholder.png'
                img = open(default_img_path,'rb')
                person['image'] = bytes(img.read())

            # Make image round
            person['image'] = __make_img_round(person['image'])

        # Format birthdate
        if person['birthday']:
            person['birthday_date'] = str_to_date(person['birthday'])
            person['birthday'] = format_date(person['birthday'])
        else:
            person['birthday_date'] = None

        # Relationships (Spouse, children)
        relationships_url = ApiBase._site + 'persons/{id}/relationships'.format(id=person['id'])
        relationships_result = Person.find(from_=relationships_url, limit=MAX_PERSONS_LIMIT)
        relationships = relationships_result[0]['data']
        person['children'] = []
        person['family_id'] = person['lastName']
        person['familyEnd'] = False
        personHasSpouse = False
        if not relationships:
            person['familyEnd'] = True
        for relationship in relationships:
            if relationship['relationshipTypeId'] == 1: # Kind
                child = Child()
                child.name = relationship['relative']['domainAttributes']['firstName']
                child_result = Person.find(from_=relationship['relative']['apiUrl'], limit=MAX_PERSONS_LIMIT)
                if len(child_result) > 0:
                    child.birthdate = str_to_date(child_result[0]['birthday'])
                    child.age = ' (' + str(__age(child_result[0]['birthday'])) + ')'
                person['children'].append(child)
            elif relationship['relationshipTypeId'] == 2: # Ehepartner
                personHasSpouse = True
                person['spouse'] = relationship['relative']['domainIdentifier']
                # Create family_id for sorting (last name, ID of husband & wife)
                if person['sexId'] == 1: # Male
                    person['family_id'] = '{lastname}-{husband_id}-{wife_id}'.format(
                                            lastname=person['lastName'],
                                            husband_id=str(person['id']),
                                            wife_id=str(relationship['relative']['domainIdentifier']))
                else: # Female
                    person['family_id'] = '{lastname}-{husband_id}-{wife_id}'.format(
                                            lastname=person['lastName'],
                                            husband_id=str(relationship['relative']['domainIdentifier']),
                                            wife_id=str(person['id']))
                    person['familyEnd'] = True

        if not personHasSpouse:
            person['familyEnd'] = True

        # Sort children by age
        person['children'].sort()

        # All children in one line
        person['allChildren'] = ', '.join(str(child) for child in person['children'])

    # Sort persons by their family
    persons_sorted = sorted(persons, key = lambda p: (p['family_id'], p['sexId']))

    # Cache result if in debug mode
    if DEBUG:
        with open(filename, 'wb') as f:
            pickle.dump(persons_sorted, f)

    return persons_sorted

class Member:
    personId = None
    firstName = ''
    lastName = ''
    present = False # Whether the person was present in the meeting

    def __hash__(self):
        return hash(self.personId)

    def __eq__(self, other):
        return self.personId == other.personId

    def __lt__(self, other):
        return self.lastName + self.firstName < other.lastName + other.firstName

    def __str__(self):
        return "{lastName} {firstName}".format(firstName = self.firstName, lastName = self.lastName)

def get_group_meeting(group_id, meeting_date):
    start_date_str = meeting_date.strftime("%Y-%m-%d")
    # End date must be one day more than start date
    end_date = meeting_date + datetime.timedelta(days=1)
    end_date_str = end_date.strftime("%Y-%m-%d")
    group_url = ApiBase._site + 'groups/{id}/meetings'.format(id=group_id)
    meetings_in_group_result = Group.find(from_=group_url,
        limit=1,
        start_date=start_date_str, end_date=end_date_str)
    meetings_in_group = meetings_in_group_result[0]['data']
    return meetings_in_group[0]

def get_meeting_members(group_id, meeting_id, filter_role_id=None):
    url = ApiBase._site + 'groups/{groupId}/meetings/{meetingId}/members'.format(groupId=group_id, meetingId=meeting_id)
    members_result = Group.find(from_=url)
    members = members_result[0]['data']
    new_members = []
    for member in members:
        if filter_role_id and int(member['member']['groupTypeRoleId']) != int(filter_role_id):
            continue
        new_member = Member()
        new_member.personId = member['member']['personId']
        new_member.firstName = member['member']['person']['domainAttributes']['firstName']
        new_member.lastName = member['member']['person']['domainAttributes']['lastName']
        new_member.present = member['status'] == 'present'
        new_members.append(new_member)
    return new_members