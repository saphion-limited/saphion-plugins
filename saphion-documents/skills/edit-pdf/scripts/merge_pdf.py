"""Join PDFs into one, whole and in the order given.

    merge_pdf.py OUTPUT.pdf FIRST.pdf SECOND.pdf [MORE.pdf ...]

``OUTPUT.pdf`` is the new file's name; each other argument is a PDF's issued file reference. To join only some pages of a file, split them out
first (``split_pdf.py``). Form fields, bookmarks and links of each file come with its pages. The result is written only if reading it back gives
every input's pages in the order given, each the same page as before.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))

from pdf_forms import form_fields
from pdf_pages import fingerprint, open_pdf, output_name, refuse, reopen, save, to_bytes
from pypdf import PdfWriter


def main(arguments: list[str]) -> None:
    if len(arguments) < 3:
        raise SystemExit("Usage: merge_pdf.py OUTPUT.pdf FIRST.pdf SECOND.pdf [MORE.pdf ...]")
    name, sources = output_name(arguments[0]), arguments[1:]
    readers = [open_pdf(path) for path in sources]
    writer, expected, seen, shared = PdfWriter(), [], {}, set()
    for path, reader in zip(sources, readers, strict=True):
        writer.append(reader)
        expected += [fingerprint(page) for page in reader.pages]
        for field in form_fields(reader):
            if field in seen:
                shared.add(field)
            seen[field] = os.path.basename(path)
    data = to_bytes(writer)
    produced = reopen(data)
    if [fingerprint(page) for page in produced.pages] != expected:
        raise refuse(f"Reading {name} back does not give the {len(expected)} pages of the inputs in the order given.")
    save(name, data)
    start = 1
    print(f"Merged {len(sources)} files into {name}, {len(produced.pages)} pages; reading it back gives each input's pages in this order:")
    for path, reader in zip(sources, readers, strict=True):
        count = len(reader.pages)
        print(f"  pages {start}-{start + count - 1}: {os.path.basename(path)} ({count} page{'s' if count != 1 else ''})")
        start += count
    if shared:
        print(f"Form fields named in more than one file ({', '.join(sorted(shared))}) are one field in the merged form: they show the same value everywhere.")


main(sys.argv[1:])
