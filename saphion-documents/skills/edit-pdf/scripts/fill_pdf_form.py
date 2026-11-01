"""Fill a PDF form's fields by name, then read the written file back to prove each holds its value.

    fill_pdf_form.py SOURCE.pdf VALUES [OUTPUT.pdf]

``SOURCE.pdf`` is the form's issued file reference. ``VALUES`` is one JSON object of field name to value: text for a text field, true/false for a
check box, one of the group's states for radio buttons, one of the options for a choice. ``OUTPUT.pdf`` defaults to the source's name with
``-filled``. A field the form does not have, a value it does not accept, a read-only field or a form that is not fillable stops the run, naming
each; nothing is written unless the file read back holds every value asked for and every other field as it was. Run ``inspect_pdf.py`` first.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))

from pdf_forms import OFF, fill, form_fields, has_xfa, read_back, resolve_values
from pdf_pages import open_pdf, output_name, refuse, reopen, save, stem, to_bytes


def main(arguments: list[str]) -> None:
    if len(arguments) not in (2, 3):
        raise SystemExit("Usage: fill_pdf_form.py SOURCE.pdf VALUES [OUTPUT.pdf]")
    source, spec = arguments[0], arguments[1]
    name = os.path.basename(source)
    try:
        values = json.loads(spec)
    except json.JSONDecodeError as failure:
        raise refuse(f"The values are not valid JSON ({failure}): give one object of field name to value.") from failure
    if not isinstance(values, dict) or not values:
        raise refuse('The values must be one JSON object of field name to value, such as {"Full name": "Ada Lovelace", "Agree": true}.')
    reader = open_pdf(source)
    fields = form_fields(reader)
    if not fields:
        raise refuse(f"{name} has no form fields, so there is nothing to fill: it is a plain PDF, not a fillable form.")
    if has_xfa(reader):
        raise refuse(f"{name} carries an XFA form, which a viewer shows in place of the fields this skill fills.")
    resolved = resolve_values(fields, values)
    data = to_bytes(fill(reader, resolved))
    problems = read_back(reopen(data), fields, resolved)
    if problems:
        raise refuse("The filled file does not hold what was asked:\n" + "\n".join(problems[:10]))
    save(output_name(arguments[2]) if len(arguments) == 3 else f"{stem(source)}-filled.pdf", data)
    print(f"Filled {len(resolved)} of {len(fields)} fields of {name}; the file read back holds each value and the other {len(fields) - len(resolved)} as they were:")
    for field, stored in resolved.items():
        print(f"  {field} = {'unchecked' if stored == OFF else stored}")


main(sys.argv[1:])
