# Generate Members list from Churchtools

Python script to generate a member directory from Churchtools API.

## Initial Setup

* Copy `.env.sample` to `.env`, and adjust to your setup.
  * See [Getting a login token](#getting-a-login-token)
* Copy template.sample.odt to template.odt and adjust to your preferences (Use [LibreOffice](https://www.libreoffice.org/) to modify the template).
  * Check the [template language documentation](https://py3otemplate.readthedocs.io/)
* Install [Python 3](https://www.python.org/)
* Install Python dependencies:
  * `pip install pyactiveresource py3o.template`

## Usage

Run `./create-memberlist.py [--filter-group=<group_id>]`

The `--filter-group` param can be used to filter by a certain group in Churchtools.

This will create a file `output.odt`. Use [LibreOffice](https://www.libreoffice.org/) to preview or postprocess it, or generate a PDF of it.

You can also use the command line to generate a PDF: `libreoffice --convert-to pdf --outdir . output.odt`

## Getting a login token

Find your ChurchTools API documentation / playground here: \<mychurch\>.church.tools/api

To retrieve a login token, first find your user ID using the `GET /persons` API.

Then use the `GET /persons/{id}/logintoken` API to get your login token.