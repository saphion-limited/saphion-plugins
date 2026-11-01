"""What every PDF script shares: opening a PDF or refusing it by name, page ranges, the one place an output is written and the identity of a page.

A refusal is ``SystemExit`` with the words for the model: it names the file, the range or the field at fault, and nothing is written (a script
writes only after its own checks pass).
"""
import hashlib
import io
import os
import re

from pypdf import PdfReader
from pypdf.errors import PyPdfError

#: One run delivers at most this many files (the sandbox runner's own limit; a script that would write more refuses first).
MAX_FILES = 16


def refuse(message: str) -> "SystemExit":
    return SystemExit(message + " Nothing was written.")


def open_pdf(path: str) -> PdfReader:
    name = os.path.basename(path)
    try:
        reader = PdfReader(path)
        pages = len(reader.pages)
    except (PyPdfError, OSError, ValueError, KeyError, TypeError) as failure:
        raise refuse(f"{name} cannot be read as a PDF ({failure}).") from failure
    if reader.is_encrypted:
        raise refuse(f"{name} is password protected, and this skill does not open protected PDFs.")
    if pages == 0:
        raise refuse(f"{name} has no pages.")
    return reader


def parse_pages(text: str, total: int, name: str) -> list[int]:
    """The pages a range names, as indexes from 0, in the order written: ``"1-3,5"``, ``"7-"`` (to the last page) or ``"all"``.

    Pages are numbered from 1 as a viewer's page counter shows them, whatever labels the PDF prints on them."""
    text = text.strip()
    if text.lower() == "all":
        return list(range(total))
    if not text:
        raise refuse(f"The page range for {name} is empty: give pages such as '1-3,5', or 'all'.")
    indexes: list[int] = []
    for part in (item.strip() for item in text.split(",")):
        found = re.fullmatch(r"(\d+)(?:\s*(-)\s*(\d*))?", part)
        if not found:
            raise refuse(f"'{part}' in the page range '{text}' is not a page or a range: use numbers like '2', '1-3' or '7-'.")
        first = int(found.group(1))
        last = (int(found.group(3)) if found.group(3) else total) if found.group(2) else first
        if first < 1 or last < 1:
            raise refuse(f"'{part}' in the page range '{text}' starts at page 0, but pages are numbered from 1.")
        if last < first:
            raise refuse(f"'{part}' in the page range '{text}' runs backwards: write the lower page first, as '{last}-{first}'.")
        if last > total:
            raise refuse(f"'{part}' in the page range '{text}' goes past the last page: {name} has {total} page{'s' if total != 1 else ''}.")
        indexes.extend(range(first - 1, last))
    return indexes


def describe(indexes: list[int]) -> str:
    """Pages from 0 back to the words a person says: ``[0, 1, 2, 4]`` is ``1-3,5``."""
    runs: list[list[int]] = []
    for index in indexes:
        if runs and index == runs[-1][-1] + 1:
            runs[-1].append(index)
        else:
            runs.append([index])
    return ",".join(str(run[0] + 1) if len(run) == 1 else f"{run[0] + 1}-{run[-1] + 1}" for run in runs)


def fingerprint(page) -> str:
    """A page's identity: its drawing instructions and its size, never its rotation. Equal fingerprints are the same page, so the order of a
    merge or a split is checked by comparing what was written with what was read."""
    contents = page.get_contents()
    digest = hashlib.sha256(contents.get_data() if contents is not None else b"")
    digest.update(repr([round(float(value), 2) for value in page.mediabox]).encode())
    return digest.hexdigest()


def output_name(name: str) -> str:
    if name != os.path.basename(name) or not name.lower().endswith(".pdf") or name.lower() == ".pdf":
        raise refuse(f"The output name {name!r} must be a plain file name ending in .pdf.")
    return name


def stem(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def to_bytes(writer) -> bytes:
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def reopen(data: bytes) -> PdfReader:
    """The file as a reader will meet it: what a script checks is the bytes it is about to write, never the objects it built them from."""
    return PdfReader(io.BytesIO(data))


def save(name: str, data: bytes) -> None:
    """Write one checked file into the one folder a run delivers from."""
    with open(os.path.join(os.environ["SKILL_OUTPUT_DIR"], output_name(name)), "wb") as handle:
        handle.write(data)
