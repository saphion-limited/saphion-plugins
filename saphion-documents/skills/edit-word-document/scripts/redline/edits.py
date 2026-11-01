"""The three edits, each made so that rejecting what was added gives back the original and everything else is left alone.

* ``replace``: words become other words. Only the words that actually differ are changed (a word-level difference of the quoted text and its
  replacement), so a redline shows the change and not the whole clause, and unchanged words keep their own formatting. Tracked, the old words
  are wrapped in ``w:del`` and the new ones in ``w:ins`` (copying the formatting of the words they replace); untracked, the runs are changed in place.
* ``comment``: a comment is tied to the words, in the comments part, with its range markers and reference.
* ``insert_after``: new paragraphs after a paragraph, with its paragraph properties (style, list numbering), tracked as an inserted paragraph.

Every edit proves itself before the next one starts: the paragraph's current text must be exactly the expected text, and with the change rejected
it must read as it did.
"""
from __future__ import annotations

import copy
import difflib
import re
from dataclasses import dataclass, field

from lxml import etree

from .comments import Comments, anchor
from .ooxml import Refusal, local, q, text_children
from .paragraphs import (
    current_text,
    cut_at,
    describe,
    fold,
    is_marker,
    original_text,
    paragraphs,
    scan,
)

_TOKEN = re.compile(r"\s+|\S+")
_WORD = re.compile(r"\w")
_PARAGRAPH_MARK_REVISIONS = ("ins", "del", "moveFrom", "moveTo", "rPrChange")
#: What an edit may cut into and rewrite: a tracked edit may delete inside someone's insertion (nested, as Word does); an untracked one never.
_REWRITABLE = {True: frozenset({"plain", "inserted"}), False: frozenset({"plain"})}


@dataclass
class Session:
    root: object
    comments: Comments
    author: str
    initials: str
    date: str
    next_id: int
    mine: set[str] = field(default_factory=set)  # the ids of the insertions and deletions this run made
    cloned: set[str] = field(default_factory=set)  # the ids of the halves made by cutting someone's insertion in two
    touched: dict = field(default_factory=dict)  # each paragraph this run edited, with the text it must now read
    made: dict[str, int] = field(default_factory=lambda: {"comments": 0, "deletions": 0, "insertions": 0, "paragraphs": 0})

    def new_id(self) -> int:
        self.next_id += 1
        return self.next_id

    def revision(self, kind: str, *, counted: bool = True):
        element = etree.Element(q(kind))
        number = self.new_id()
        for name, value in (("id", str(number)), ("author", self.author), ("date", self.date)):
            element.set(q(name), value)
        self.mine.add(str(number))
        if counted:
            self.made["deletions" if kind == "del" else "insertions"] += 1
        return element


# --- finding the words ---------------------------------------------------------------------------------------------------------------


def _context(text: str, start: int, end: int) -> str:
    return ("…" if start > 30 else "") + text[max(0, start - 30):end + 30] + ("…" if end + 30 < len(text) else "")


def locate(session: Session, find: str, occurrence: int | None):
    """The one place ``find`` reads in the document's current text (a paragraph, start, end). More than one place needs ``occurrence``."""
    needle, hits, texts = fold(find), [], []
    for paragraph in paragraphs(session.root):
        text = current_text(paragraph)
        texts.append(text)
        folded, position = fold(text), 0
        while (position := folded.find(needle, position)) != -1:
            hits.append((paragraph, position, position + len(needle)))
            position += len(needle)
    if not hits:
        words = set(re.findall(r"\w+", needle.lower()))
        close = sorted(((len(words & set(re.findall(r"\w+", text.lower()))) / max(len(words), 1), text) for text in texts), reverse=True)[:2]
        near = "".join(f"\n  - {text[:200]!r}" for score, text in close if score >= 0.4)
        raise Refusal(f"No place in the document reads {find!r}. It is matched against what the document reads now (deleted words are gone, inserted "
                      "words are there), within one paragraph." + (f" The nearest paragraphs read:{near}" if near else ""))
    if occurrence is None and len(hits) > 1:
        shown = "".join(f"\n  {number}. {_context(current_text(paragraph), start, end)!r}" for number, (paragraph, start, end) in enumerate(hits[:6], 1))
        raise Refusal(f"{len(hits)} places read {find!r}; quote more words so exactly one matches, or give occurrence (1 to {len(hits)}):{shown}")
    if occurrence is not None and not 1 <= occurrence <= len(hits):
        raise Refusal(f"occurrence {occurrence} was asked for but {find!r} reads in {len(hits)} place(s).")
    return hits[(occurrence or 1) - 1]


# --- changing words ------------------------------------------------------------------------------------------------------------------


def word_changes(old: str, new: str) -> list[tuple[int, int, str]]:
    """Where ``new`` differs from ``old`` as ``(start, end, replacement)`` in ``old``, by whole words as they read (a word keeps its punctuation); changes with no word between them are one."""
    old_tokens, new_tokens = _TOKEN.findall(fold(old)), _TOKEN.findall(fold(new))
    old_at, new_at = [0], [0]
    for token in old_tokens:
        old_at.append(old_at[-1] + len(token))
    for token in new_tokens:
        new_at.append(new_at[-1] + len(token))
    changes: list[tuple[int, int, str]] = []
    for tag, a1, a2, b1, b2 in difflib.SequenceMatcher(None, old_tokens, new_tokens, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        start, end, text = old_at[a1], old_at[a2], new[new_at[b1]:new_at[b2]]
        if changes and not _WORD.search(old[changes[-1][1]:start]):
            before_start, before_end, before_text = changes[-1]
            changes[-1] = (before_start, end, before_text + old[before_end:start] + text)
        else:
            changes.append((start, end, text))
    return changes


def _clean_rpr(run):
    """A copy of the run's formatting for words that replace its words (a revision of the formatting itself is not carried over)."""
    found = run.find(q("rPr")) if run is not None else None
    if found is None:
        return None
    clone = copy.deepcopy(found)
    for change in clone.findall(q("rPrChange")):
        clone.remove(change)
    return clone


def _new_run(formatting, text: str):
    run = etree.Element(q("r"))
    if formatting is not None:
        run.append(copy.deepcopy(formatting))
    for child in text_children(text):
        run.append(child)
    return run


def _wrapped(session: Session, tracked: bool, formatting, text: str):
    run = _new_run(formatting, text)
    if not tracked:
        return run
    insertion = session.revision("ins")
    insertion.append(run)
    return insertion


def place_after(session: Session, element, node) -> None:
    """Put ``node`` right after ``element``. If ``element`` sits inside someone's tracked insertion, that insertion is cut after it (as Word does: the
    two halves keep their author and date, the second takes a new id) and ``node`` goes between them, outside both."""
    parent = element.getparent()
    while local(parent) in ("ins", "moveTo"):
        following = list(element.itersiblings())
        if following:
            rest = etree.Element(parent.tag, dict(parent.attrib))
            rest.set(q("id"), str(session.new_id()))
            session.cloned.add(rest.get(q("id")))
            for sibling in following:
                rest.append(sibling)
            parent.addnext(rest)
        element, parent = parent, parent.getparent()
    element.addnext(node)


def _insert_words(session: Session, paragraph, at: int, text: str, tracked: bool) -> None:
    cut_at(paragraph, at, kinds=_REWRITABLE[tracked])
    pieces = [piece for piece in scan(paragraph) if piece.end > piece.start]
    left = next((piece for piece in reversed(pieces) if piece.end == at), None)
    right = next((piece for piece in pieces if piece.start == at), None)
    source = next((piece for piece in (left, right) if piece is not None and piece.kind == "plain"), left or right)
    node = _wrapped(session, tracked, _clean_rpr(source.element if source and source.simple else None), text)
    if left is not None and (left.kind in _REWRITABLE[tracked]):
        place_after(session, left.element, node)
    elif left is None and right is not None and right.kind == "plain":
        right.element.addprevious(node)
    else:
        raise Refusal("The change lands beside a field, a content control or someone's tracked insertion in a way that cannot be tracked: choose other words.")


def _change_words(session: Session, paragraph, start: int, end: int, text: str, tracked: bool) -> None:
    if start == end:
        _insert_words(session, paragraph, start, text, tracked)
        return
    kinds = _REWRITABLE[tracked]
    cut_at(paragraph, end, kinds=kinds)
    cut_at(paragraph, start, kinds=kinds)
    pieces = scan(paragraph)
    for piece in pieces:
        if piece.start == piece.end and start < piece.start < end:
            raise Refusal("The words contain an object (a formula, a picture in the line, a form control): change the words either side of it separately.")
    covered = [piece for piece in pieces if piece.end > piece.start and start <= piece.start and piece.end <= end]
    for piece in covered:
        if piece.kind not in kinds or not piece.simple:
            raise Refusal(f"These words include {describe(piece)}: it cannot be rewritten without losing it. Choose words outside it.")
    runs = [piece.element for piece in covered]
    formatting = _clean_rpr(runs[0])
    if not tracked:
        if len({id(piece.parent) for piece in covered}) != 1:
            raise Refusal("These words run across a link or other structure: change the part before it and the part after it separately.")
        for sibling in runs[0].itersiblings() if len(runs) > 1 else ():
            if sibling is runs[-1]:
                break
            if sibling not in runs and not is_marker(sibling):
                raise Refusal("Someone's tracked change sits inside these words, so they cannot be replaced untracked; track this edit, or choose other words.")
        for run in runs[1:]:
            run.getparent().remove(run)
        first = runs[0]
        for child in list(first):
            if local(child) != "rPr":
                first.remove(child)
        if text:
            for child in text_children(text):
                first.append(child)
        else:
            first.getparent().remove(first)
        return
    wrapper = None
    for run in runs:
        if wrapper is not None and run.getprevious() is wrapper:
            wrapper.append(run)
        else:
            wrapper = session.revision("del")
            run.addprevious(wrapper)
            wrapper.append(run)
        for child in run:
            if local(child) == "t":
                child.tag = q("delText")
    if text:
        place_after(session, wrapper, _wrapped(session, True, formatting, text))


def replace(session: Session, find: str, text: str, tracked: bool, note: str | None, occurrence: int | None) -> str:
    paragraph, start, end = locate(session, find, occurrence)
    before = current_text(paragraph)
    was, old = original_text(paragraph, session.mine), before[start:end]
    if fold(old) == fold(text):
        raise Refusal(f"The document already reads {old!r} there: nothing to change.")
    if note is not None and not text:
        raise Refusal("A comment cannot sit on words that are deleted. Comment on the words beside them, in a comment edit.")
    changes = word_changes(old, text)
    for a, b, new in reversed(changes):
        _change_words(session, paragraph, start + a, start + b, new, tracked)
    expected = before[:start] + text + before[end:]
    if (now := current_text(paragraph)) != expected:
        raise Refusal(f"Internal check failed: the paragraph reads {now!r} where {expected!r} was expected. Nothing was saved.")
    if tracked and original_text(paragraph, session.mine) != was:
        raise Refusal("Internal check failed: rejecting the change would not restore the paragraph. Nothing was saved.")
    session.touched[paragraph] = expected
    if note is not None:  # on the words that changed (first change to last, as the paragraph now reads), not the whole quoted passage
        first, last = start + changes[0][0], start + len(text) - (len(old) - changes[-1][1])
        if last <= first:
            first, last = start, start + len(text)
        add_comment(session, paragraph, first, last, note)
    return f"{'tracked ' if tracked else ''}{old[:60]!r} -> {text[:60]!r}"


# --- comments ------------------------------------------------------------------------------------------------------------------------


def add_comment(session: Session, paragraph, start: int, end: int, text: str) -> None:
    number = session.new_id()
    anchor(session.comments, paragraph, start, end, number)
    session.comments.add(number, session.author, session.initials, session.date, text)
    session.made["comments"] += 1


def comment(session: Session, find: str, text: str, occurrence: int | None) -> str:
    paragraph, start, end = locate(session, find, occurrence)
    before = current_text(paragraph)
    add_comment(session, paragraph, start, end, text)
    if current_text(paragraph) != before:
        raise Refusal("Internal check failed: anchoring the comment changed the text. Nothing was saved.")
    session.touched[paragraph] = before
    return f"comment on {before[start:end][:60]!r}"


# --- new paragraphs ------------------------------------------------------------------------------------------------------------------


def _paragraph_after(session: Session, source, line: str, tracked: bool, formatting):
    """A new paragraph with the source paragraph's properties (style, list numbering), its mark tracked as inserted when the edit is tracked."""
    new = etree.Element(q("p"))
    properties = source.find(q("pPr"))
    properties = copy.deepcopy(properties) if properties is not None else etree.Element(q("pPr"))
    for kept_out in ("sectPr", "pPrChange"):  # a section break or a formatting revision belongs to the source paragraph alone
        for found in properties.findall(q(kept_out)):
            properties.remove(found)
    mark = properties.find(q("rPr"))
    if mark is not None:
        for kind in _PARAGRAPH_MARK_REVISIONS:
            for found in mark.findall(q(kind)):
                mark.remove(found)
    if tracked:
        if mark is None:
            mark = etree.SubElement(properties, q("rPr"))
        mark.insert(0, session.revision("ins", counted=False))
    if len(properties) or tracked:
        new.append(properties)
    new.append(_wrapped(session, tracked, formatting, line))
    return new


def insert_after(session: Session, find: str, text: str, tracked: bool, note: str | None, occurrence: int | None) -> str:
    source, _, _ = locate(session, find, occurrence)
    lines = text.split("\n")
    if any(not line.strip() for line in lines):
        raise Refusal("Each new paragraph needs words: remove the empty line.")
    plain = [piece for piece in scan(source) if piece.kind == "plain" and piece.simple and piece.end > piece.start]
    formatting = _clean_rpr(max(plain, key=lambda piece: piece.end - piece.start).element) if plain else None
    created, after = [], source
    for line in lines:
        new = _paragraph_after(session, source, line, tracked, formatting)
        after.addnext(new)
        after = new
        created.append((new, line))
        session.made["paragraphs"] += 1
    for new, line in created:
        if current_text(new) != line or original_text(new, session.mine) != ("" if tracked else line):
            raise Refusal("Internal check failed: a new paragraph does not read as written. Nothing was saved.")
    session.touched.update(created)
    if note is not None:
        add_comment(session, created[0][0], 0, len(lines[0]), note)
    return f"{'tracked ' if tracked else ''}{len(lines)} new paragraph(s) after {current_text(source)[:50]!r}"
