# Generate Members list from Churchtools

Python script to generate a member directory from Churchtools API.

## Initial Setup

* Copy `.env.sample` to `.env`, and adjust to your setup.
* Copy template.sample.odt to template.odt and adjust to your preferences (Use LibreOffice to modify the template).
  * Find the template language documentation here: https://py3otemplate.readthedocs.io/

## Usage

* Run `./create-memberlist.py [--filter-group=<group_id>]`
  * The `--filter-group` param can be used to filter by a certain group in Churchtools.
  * This will create a file `output.odt`. Use LibreOffice to preview or postprocess it, or generate a PDF of it.
  * You can also use the command line to generate a PDF: `libreoffice --convert-to pdf --outdir . output.odt`

## Requirements

Python 3 is required.

Additionally, you need to install pyactiveresource py3o.template:

* `pip install pyactiveresource py3o.template`
