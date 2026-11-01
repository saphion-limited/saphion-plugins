"""Look at one or more PDFs before changing them: pages, sizes, rotation and the form's fields.

    inspect_pdf.py FILE.pdf [FILE.pdf ...] [--from N]

Each argument is a PDF's issued file reference (it arrives as its path). For each file the summary is printed: its page count and size, any page
that is already rotated, and each form field with its type, page and what it accepts. A form with more fields than the run shows (the last 2,000
characters) says where it stopped: run it again with ``--from N`` to list the fields from the Nth on. Nothing is written and nothing in the PDF is
changed.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))

from pdf_forms import form_fields, has_xfa
from pdf_pages import open_pdf

#: The run's stdout is shown to the model from its end, 2,000 characters at most: the summary stays inside that and ``--from`` reaches the rest.
BUDGET = 1_400


def accepts(entry) -> str:
    if entry.kind in ("checkbox", "radio") and not entry.settable:
        return "not fillable (the PDF stores no checked state for it)"
    if entry.kind == "checkbox":
        return f"true/false (checked is '{entry.states[0]}')"
    if entry.kind == "radio":
        return "one of " + ", ".join(repr(state) for state in entry.states)
    if entry.kind == "choice":
        return "one of " + ", ".join(repr(shown) for _, shown in entry.options)
    return {"text": "text", "button": "not fillable (push button)", "signature": "not fillable (signature)"}[entry.kind]


def main(arguments: list[str]) -> None:
    first = 1
    if len(arguments) >= 2 and arguments[-2] == "--from":
        if not arguments[-1].isdigit() or int(arguments[-1]) < 1:
            raise SystemExit("--from takes a field number, 1 or more.")
        first, arguments = int(arguments[-1]), arguments[:-2]
    if not arguments:
        raise SystemExit("Usage: inspect_pdf.py FILE.pdf [FILE.pdf ...] [--from N]")
    for path in arguments:
        reader = open_pdf(path)
        pages = reader.pages
        width, height = (float(value) for value in (pages[0].mediabox.width, pages[0].mediabox.height))
        turned = [f"{number} ({page.rotation} deg)" for number, page in enumerate(pages, 1) if page.rotation]
        fields = form_fields(reader)
        line = f"{os.path.basename(path)}: {len(pages)} page{'s' if len(pages) != 1 else ''}, first page {width / 72:.1f} x {height / 72:.1f} in"
        print(line + (f"; rotated pages {', '.join(turned)}" if turned else "") + (f"; {len(fields)} form fields" if fields else "; no form fields"))
        if fields and has_xfa(reader):
            print("  It also carries an XFA form: a viewer that supports XFA shows that, not these fields, so this skill will not fill it.")
        shown = 0
        for number, entry in enumerate(fields.values(), 1):
            if number < first:
                continue
            text = f"  {entry.name} [{entry.kind}, page {', '.join(str(page) for page in entry.pages)}{', read only' if entry.read_only else ''}]"
            if entry.kind != "text":
                text += f": {accepts(entry)}"
            held = "; ".join(entry.value) if isinstance(entry.value, list) else str(entry.value or "")
            if held:
                text += f" (now {held!r})"
            if shown and shown + len(text) > BUDGET // len(arguments):
                print(f"  ... {len(fields) - number + 1} more fields: run again with --from {number}")
                break
            print(text)
            shown += len(text)


main(sys.argv[1:])
