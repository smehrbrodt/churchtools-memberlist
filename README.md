# Reporting via Churchtools API

Python script to create documents via Churchtools API.

* Member list
* Prayer list
* Checkin form
* Attendance report

## Initial Setup

* Copy `.env.sample` to `.env`, and adjust to your setup.
  * See [Getting a login token](#getting-a-login-token)
* Copy template.sample.odt to template.odt and adjust to your preferences (Use [LibreOffice](https://www.libreoffice.org/) to modify the template).
  * Check the [template language documentation](https://py3otemplate.readthedocs.io/)
* Install [Python 3](https://www.python.org/)
* Create a virtual env for this project, and activate the venv. [More information](https://docs.python.org/3/library/venv.html)
* Install Python dependencies:
  * `<path_to_venv>/bin/pip install -r requirements.txt`

## Usage

Any of the below commands will create `odt` output files.
Use [LibreOffice](https://www.libreoffice.org/) to preview or postprocess them, or generate a PDF of it.

You can also use the command line to generate a PDF: `libreoffice --convert-to pdf --outdir . input.odt`

### Member list

Creates a membership directory.

```bash
./create-memberlist.py \
    --filter-group <group_id> \
    [--template template_memberlist.odt] \
    [--output memberlist.odt]
```

The `--filter-group` param is used to filter by a certain group in Churchtools.

### Prayer list

Creates a prayer list (similiar to membership directory, but different layout). Can be filtered to include only part of the members using `--surname-from` and `surname-to` arguments.

```bash
./create-prayerlist.py \
    [--surname-from <letter>] \
    [--surname-to <letter>] \
    [--template template_prayerlist.odt] \
    [--output prayerlist.odt]
```

### Checkin form

Create a checkin form. This assumes you have two groups: Members and regular visitors.
The regular visitors group can be filtered to include only certain roles from that group.

```bash
./create-checkinform.py \
    --group-members <group_id> \
    --group-regularvisitors <group_id> \
    --role-id-regularvisitors <role_id> \
    [--template template_checkinform.odt] \
    [--output checkinform.odt]
```

### Attendance report

Generate an attendance report.

```bash
./create-attendancereport.py \
    --group-members <group_id> \
    --group-regular-visitors <group_id> \
    --role-id-regularvisitors <role_id> \
    --group-visitors <group_id> \
    --role-id-visitors <role_id> \
    --date YYYY-MM-DD \
    [--template template_attendancereport.odt] \
    [--output attendancereport.odt]
```

## Getting a login token

Find your ChurchTools API documentation / playground here: \<mychurch\>.church.tools/api

To retrieve a login token, first find your user ID using the `GET /persons` API.

Then use the `GET /persons/{id}/logintoken` API to get your login token.