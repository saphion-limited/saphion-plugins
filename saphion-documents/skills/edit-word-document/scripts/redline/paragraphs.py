"""A paragraph as the person reads it, and the runs behind each word.

Word splits one sentence across many runs, wraps text in insertions, hyperlinks and fields, and leaves deleted words in the file. ``scan`` reads a
paragraph as its **current text**: what Word shows with every tracked change accepted (deleted words are gone, inserted words are there). Each
stretch of that text is a ``Piece`` that knows its run, so an edit can cut a run at a character and change exactly those words. A piece is

* ``plain``: ordinary text, safe to rewrite;
* ``inserted``: inside someone's tracked insertion. It can be commented on; rewriting it would hide their change, so it is refused;
* ``locked``: part of a field, a content control, or a run that holds a picture, note reference or other object. It can be commented on, never rewritten.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

from lxml import etree

from .ooxml import XML_SPACE, Refusal, attr, local, q, run_text, run_units

#: Typographic quotes and no-break spaces match their plain forms, one character for one, so positions never shift.
_FOLD = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', " ": " "})
#: Zero-width markup between the runs: it is never text and never stands in the way of an edit.
MARKERS = frozenset({
    "bookmarkStart", "bookmarkEnd", "proofErr", "commentRangeStart", "commentRangeEnd", "permStart", "permEnd", "moveFromRangeStart",
    "moveFromRangeEnd", "moveToRangeStart", "moveToRangeEnd", "customXmlInsRangeStart", "customXmlInsRangeEnd", "customXmlDelRangeStart",
    "customXmlDelRangeEnd", "customXmlMoveFromRangeStart", "customXmlMoveFromRangeEnd", "customXmlMoveToRangeStart", "customXmlMoveToRangeEnd",
})
_TRANSPARENT = frozenset({"hyperlink", "smartTag", "customXml", "dir", "bdo"})
_EXCLUDED_ANCESTORS = frozenset({q("txbxContent"), q("del"), q("moveFrom"), "{http://schemas.openxmlformats.org/markup-compatibility/2006}AlternateContent"})


def fold(text: str) -> str:
    return text.translate(_FOLD)


@dataclass
class Piece:
    element: object
    parent: object
    start: int
    end: int
    kind: str
    simple: bool
    text: str
    author: str = ""


def is_marker(element) -> bool:
    """Zero-width markup, including the run that holds only a comment's reference mark."""
    name = local(element)
    if name in MARKERS or not isinstance(element.tag, str):
        return True
    return name == "r" and not run_text(element) and all(local(child) in ("rPr", "commentReference", "lastRenderedPageBreak") for child in element)


def paragraphs(root) -> list:
    """Every paragraph of the body that is its own text: not a text box (Word keeps two copies of one) and not a deleted paragraph."""
    body = root.find(q("body"))
    if body is None:
        raise Refusal("The document has no body to edit.")
    return [p for p in body.iter(q("p")) if not any(ancestor.tag in _EXCLUDED_ANCESTORS for ancestor in p.iterancestors())]


def scan(paragraph) -> list[Piece]:
    pieces: list[Piece] = []
    at = 0
    fields: list[str] = []

    def visit(container, kind: str, author: str) -> None:
        nonlocal at
        for child in container:
            name = local(child)
            if name == "r":
                units = run_units(child)
                marks = [(attr(unit, "fldCharType"), unit) for unit, _, _ in units if local(unit) == "fldChar"]
                text = "".join(part for _, part, _ in units)
                objects = [unit for unit, _, is_object in units if is_object and local(unit) != "commentReference"]
                if text or objects:
                    locked = bool(objects) or bool(fields)
                    pieces.append(Piece(child, container, at, at + len(text), "locked" if locked else kind, not objects and not fields, text, author))
                    at += len(text)
                for mark, _ in marks:
                    if mark == "begin":
                        fields.append("instruction")
                    elif mark == "separate" and fields:
                        fields[-1] = "result"
                    elif mark == "end" and fields:
                        fields.pop()
            elif name in _TRANSPARENT:
                visit(child, kind, author)
            elif name in ("ins", "moveTo"):
                visit(child, "inserted", attr(child, "author") or "")
            elif name == "fldSimple":
                visit(child, "locked", author)
            elif name == "sdt":
                content = child.find(q("sdtContent"))
                if content is not None:
                    visit(content, "locked", author)
            elif name in ("del", "moveFrom", "pPr") or is_marker(child):
                continue
            else:  # an object between runs (a formula, an alternate-content picture): not text, never inside an edit
                pieces.append(Piece(child, container, at, at, "locked", False, ""))

    visit(paragraph, "plain", "")
    return pieces


def current_text(paragraph) -> str:
    return "".join(piece.text for piece in scan(paragraph))


def original_text(paragraph, mine: set[str]) -> str:
    """The paragraph as it reads with the changes in ``mine`` (revision ids) rejected and everyone else's changes as they stand."""
    out: list[str] = []

    def visit(container) -> None:
        for child in container:
            name = local(child)
            if name == "r":
                out.append(run_text(child))
            elif name in _TRANSPARENT or name == "fldSimple":
                visit(child)
            elif name == "sdt" and child.find(q("sdtContent")) is not None:
                visit(child.find(q("sdtContent")))
            # my insertion is rejected away and my deletion is restored; everyone else's insertion stands and everyone else's deletion stays deleted
            elif name in ("ins", "moveTo", "del", "moveFrom") and (attr(child, "id") in mine) == (name in ("del", "moveFrom")):
                visit(child)

    visit(paragraph)
    return "".join(out)


def top_level(paragraph, element):
    """The child of ``paragraph`` that holds ``element``."""
    while element.getparent() is not paragraph:
        element = element.getparent()
    return element


def split_run(run, offset: int):
    """Cut a plain run in two at character ``offset`` (inside it). Both halves keep the run's formatting; the right half is returned."""
    right = copy.deepcopy(run)
    for child in list(right):
        if local(child) != "rPr":
            right.remove(child)
    seen, moving = 0, False
    for child, text, _ in run_units(run):
        if local(child) == "rPr":
            continue
        if moving:
            right.append(child)
            continue
        if seen + len(text) > offset:  # inside this child: only a w:t is longer than one character
            keep = offset - seen
            tail = etree.SubElement(right, child.tag)
            tail.text = text[keep:]
            tail.set(XML_SPACE, "preserve")
            child.text = text[:keep]
            child.set(XML_SPACE, "preserve")
            moving = True
        else:
            seen += len(text)
            moving = seen == offset
    run.addnext(right)
    return right


def cut_at(paragraph, offset: int, *, kinds: frozenset[str]) -> None:
    """Make ``offset`` a boundary between two runs. A run is cut only if it holds no object or field mark and its kind is one of ``kinds`` (an edit
    that rewrites words never cuts into a field; an untracked one never cuts into someone's insertion). Such a position is refused, naming what is in the way."""
    for piece in scan(paragraph):
        if piece.start < offset < piece.end:
            if not piece.simple or piece.kind not in kinds:
                raise Refusal(f"The words end inside {describe(piece)}: choose words that begin and end outside it.")
            split_run(piece.element, offset - piece.start)
            return


def describe(piece: Piece) -> str:
    if piece.kind == "inserted":
        return f"a tracked insertion by {piece.author or 'someone'} (an untracked edit would hide their change)"
    return "a field, a content control or a run holding a picture or note"
