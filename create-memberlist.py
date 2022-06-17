#!/usr/bin/env python3

# Copyright (c) 2022 Samuel Mehrbrodt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import datetime
import io
import os
import requests

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFilter
from py3o.template import Template
from pyactiveresource.activeresource import ActiveResource

load_dotenv()

# Random limits from Churchtools API
MAX_PERSONS_LIMIT = 500
MAX_GROUP_MEMBERS_LIMIT = 100

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--filter-group", help="Filter for group ID")
args = parser.parse_args()

requested_group_id = args.filter_group

# Create template
t = Template("template.odt", "output.odt")

# REST API definitions
class ApiBase(ActiveResource):
    _site = 'https://' + os.getenv('CHURCHTOOLS_DOMAIN') + '/api/'
    _headers = { 'Authorization': 'Login ' + os.getenv('CHURCHTOOLS_LOGIN_TOKEN') }

class Group(ApiBase):
    pass

class Person(ApiBase):
    pass

class Child:
    pass

def age(birthdate_str):
    birthdate = datetime.datetime.strptime(birthdate_str, "%Y-%m-%d").date()
    today = datetime.date.today()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

def format_birthdate(birthdate_str):
    birthdate = datetime.datetime.strptime(birthdate_str, "%Y-%m-%d").date()
    return birthdate.strftime("%d.%m.%Y")

# From https://note.nkmk.me/en/python-pillow-square-circle-thumbnail/
def mask_circle_transparent(pil_img, blur_radius, offset=0):
    offset = blur_radius * 2 + offset
    mask = Image.new("L", pil_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((offset, offset, pil_img.size[0] - offset, pil_img.size[1] - offset), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

    result = pil_img.copy()
    result.putalpha(mask)

    return result

def make_img_round(img_bytes):
    im = Image.open(io.BytesIO(img_bytes))
    im_round = mask_circle_transparent(im, 0, 2)
    img_byte_arr = io.BytesIO()
    im_round.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# Get all persons
persons_result = Person.find(from_=ApiBase._site + 'persons', limit=MAX_PERSONS_LIMIT)
persons = persons_result[0]['data']

persons_filtered = []
# Filter only those in current group
if requested_group_id:
    group_url = ApiBase._site + 'groups/{id}/members'.format(id=requested_group_id)
    persons_in_group_result = Group.find(from_=group_url, limit=MAX_GROUP_MEMBERS_LIMIT)
    persons_in_group = persons_in_group_result[0]['data']
    # Remove persons not in this group from persons
    for person in persons:
        found = False
        for group_person in persons_in_group:
            if group_person['personId'] == person['id']:
                found = True
                break
        if found:
            persons_filtered.append(person)

# Postprocessing
for person in persons_filtered:
    # Profile pic
    if person['imageUrl']:
        person['image'] = requests.get(person['imageUrl']).content
    else:
        default_img_path = os.path.realpath(os.path.dirname(__file__)) + '/images/placeholder.png'
        img = open(default_img_path,'rb')
        person['image'] = bytes(img.read())

    # Make image round
    person['image'] = make_img_round(person['image'])

    # Format birthdate
    person['birthday'] = format_birthdate(person['birthday'])

    # Relationships (Spouse, children)
    relationships_url = ApiBase._site + 'persons/{id}/relationships'.format(id=person['id'])
    relationships_result = Person.find(from_=relationships_url, limit=MAX_PERSONS_LIMIT)
    relationships = relationships_result[0]['data']
    person['children'] = []
    person['family_id'] = person['lastName']
    for relationship in relationships:
        if relationship['relationshipTypeId'] == 1: # Kind
            child = Child()
            child.name = relationship['relative']['domainAttributes']['firstName']
            child_result = Person.find(from_=relationship['relative']['apiUrl'], limit=MAX_PERSONS_LIMIT)
            if len(child_result) > 0:
                child.age = ' (' + str(age(child_result[0]['birthday'])) + ')'
            person['children'].append(child)
        elif relationship['relationshipTypeId'] == 2: # Ehepartner
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

# Sort persons by their family
persons_sorted = sorted(persons_filtered, key = lambda p: (p['family_id'], p['sexId']))

data = dict(persons=persons_sorted)
t.render(data)
