"""Take pages out of a PDF: one file of the pages asked for, several files of page groups, or one file per page.

    split_pdf.py SOURCE.pdf GROUPS

``SOURCE.pdf`` is the PDF's issued file reference. ``GROUPS`` is page groups separated by semicolons, each a list of pages and ranges (pages are
numbered from 1 as a viewer counts them): ``"1-3"`` is one file of pages 1 to 3; ``"1-3;4-6;7-"`` is three files; ``"2,5,9"`` is one file of
those three pages in that order; ``"each"`` is one file per page. Each file is named ``<name>-pages-<pages>.pdf``. The source is not changed.
Every file is written only if reading it back gives exactly the pages asked for, each the same page as in the source.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))

from pdf_pages import MAX_FILES, describe, fingerprint, open_pdf, parse_pages, refuse, reopen, save, stem, to_bytes
from pypdf import PdfWriter


def main(arguments: list[str]) -> None:
    if len(arguments) != 2:
        raise SystemExit("Usage: split_pdf.py SOURCE.pdf GROUPS")
    source, text = arguments
    name, reader = os.path.basename(source), open_pdf(source)
    total = len(reader.pages)
    if text.strip().lower() == "each":
        groups = [[index] for index in range(total)]
    else:
        groups = [parse_pages(group, total, name) for group in text.split(";")]
    if len(groups) > MAX_FILES:
        raise refuse(f"That makes {len(groups)} files and one run delivers at most {MAX_FILES}: ask for fewer, larger page groups.")
    names = [f"{stem(source)}-pages-{describe(group).replace(',', '_')}.pdf" for group in groups]
    if len(set(names)) != len(names):
        raise refuse("Two groups are the same pages, so they would be the same file: name each set of pages once.")
    prints = [fingerprint(page) for page in reader.pages]
    made = []
    for group, file in zip(groups, names, strict=True):
        writer = PdfWriter()
        writer.append(reader, pages=group)
        data = to_bytes(writer)
        produced = reopen(data)
        if [fingerprint(page) for page in produced.pages] != [prints[index] for index in group]:
            raise refuse(f"Reading {file} back does not give pages {describe(group)} of {name}.")
        made.append((group, file, data, len(produced.pages)))
    for _, file, data, _ in made:
        save(file, data)
    results = [f"  {file}: pages {describe(group)} of {name} ({count} page{'s' if count != 1 else ''})" for group, file, _, count in made]
    print(f"Split {name} ({total} pages) into {len(groups)} file{'s' if len(groups) != 1 else ''}; each read back holds exactly the pages named:")
    print("\n".join(results))


main(sys.argv[1:])
