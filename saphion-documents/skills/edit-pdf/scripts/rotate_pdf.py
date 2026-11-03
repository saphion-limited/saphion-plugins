"""Turn pages of a PDF clockwise by 90, 180 or 270 degrees.

    rotate_pdf.py SOURCE.pdf DEGREES PAGES [OUTPUT.pdf]

``SOURCE.pdf`` is the PDF's issued file reference. ``DEGREES`` is 90, 180 or 270 clockwise (-90 is a quarter turn back). ``PAGES`` is the pages to
turn, numbered from 1 as a viewer counts them (``"2"``, ``"1-3,6"``) or ``"all"``. ``OUTPUT.pdf`` defaults to the source's own name, which is a new version of that file; another name is a new file.
The turn adds to a page's rotation as it is now. The file is written only if reading it back shows each asked page turned by exactly that much,
every other page not turned, and every page the same page as before.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))

from pdf_pages import describe, fingerprint, open_pdf, output_name, parse_pages, refuse, reopen, save, to_bytes
from pypdf import PdfWriter


def main(arguments: list[str]) -> None:
    if len(arguments) not in (3, 4):
        raise SystemExit("Usage: rotate_pdf.py SOURCE.pdf DEGREES PAGES [OUTPUT.pdf]")
    source, degrees, text = arguments[:3]
    name, reader = os.path.basename(source), open_pdf(source)
    try:
        turn = int(degrees)
    except ValueError:
        turn = None
    if turn is None or turn % 90 or turn % 360 == 0:
        raise refuse(f"A rotation is 90, 180 or 270 degrees clockwise (or -90); {degrees!r} is not.")
    turn %= 360
    chosen = sorted(set(parse_pages(text, len(reader.pages), name)))
    before = [(page.rotation % 360, fingerprint(page)) for page in reader.pages]
    writer = PdfWriter(clone_from=reader)
    for index in chosen:
        writer.pages[index].rotate(turn)
    data = to_bytes(writer)
    wanted = [((rotation + turn) % 360 if index in chosen else rotation, print_) for index, (rotation, print_) in enumerate(before)]
    if [(page.rotation % 360, fingerprint(page)) for page in reopen(data).pages] != wanted:
        raise refuse(f"Reading the rotated file back does not show pages {describe(chosen)} turned {turn} degrees and the rest unchanged.")
    save(output_name(arguments[3]) if len(arguments) == 4 else os.path.basename(source), data)
    print(f"Turned pages {describe(chosen)} of {name} {turn} degrees clockwise; read back, those pages now sit at "
          + ", ".join(f"{index + 1}: {wanted[index][0]} deg" for index in chosen[:12]) + (" ..." if len(chosen) > 12 else "")
          + f" and the other {len(before) - len(chosen)} pages are as they were.")


main(sys.argv[1:])
