"""What is proved before anything is saved: the file keeps everything it had, and the changes are only the ones asked for."""
from __future__ import annotations

import io
from collections import Counter

from .comments import Comments
from .edits import Session
from .ooxml import attr, local
from .package import Package
from .paragraphs import current_text, paragraphs

_REVISIONS = frozenset({"ins", "del", "moveFrom", "moveTo", "rPrChange", "pPrChange", "sectPrChange", "tblPrChange", "tblGridChange", "tcPrChange",
                        "trPrChange", "numberingChange", "cellIns", "cellDel", "cellMerge"})
_ANCHORS = frozenset({"commentRangeStart", "commentRangeEnd", "commentReference"})


def _revisions(root, skip: frozenset[str] = frozenset()) -> tuple[set, Counter]:
    """Every tracked change not in ``skip``: the ``(kind, id)`` of each, and per ``(kind, author, date)`` how many characters of words they hold (a
    change cut in two keeps its author, date and words, and a deletion nested inside it is words it still holds)."""
    found = [element for element in root.iter() if local(element) in _REVISIONS and attr(element, "id") not in skip]
    words: Counter = Counter()
    for element in found:
        words[(local(element), attr(element, "author"), attr(element, "date"))] += len("".join(element.itertext()))
    return {(local(element), attr(element, "id")) for element in found}, words


def _anchors(root) -> Counter:
    return Counter((local(element), attr(element, "id")) for element in root.iter() if local(element) in _ANCHORS)


class Before:
    """The file as it came in: its tracked changes, comments and the words of every paragraph."""

    def __init__(self, package: Package, comments: Comments) -> None:
        root = package.root(package.main)
        self.revisions = _revisions(root)
        self.revision_ids = {number for _, number in self.revisions[0]}
        self.anchors = _anchors(root)
        self.comments = comments.existing()
        self.paragraphs = [(paragraph, current_text(paragraph)) for paragraph in paragraphs(root)]
        self.comment_count = len(self.comments)


def verify(package: Package, before: Before, session: Session, saved: bytes) -> list[str]:
    """The problems found, empty when the saved file keeps everything it had: other parts byte for byte, every earlier tracked change and comment as
    it was, every paragraph that was not edited with the same words, and the new ids unique and unfamiliar. It must also open in python-docx."""
    problems: list[str] = []
    root = package.root(package.main)
    allowed = {package.main, package.main_rels, "[Content_Types].xml", session.comments.name} - {None}
    if (stray := package.changed_parts() - allowed):
        problems.append(f"parts changed that no edit owns: {sorted(stray)}")
    if (drifted := package.unchanged_bytes_kept(saved)):
        problems.append(f"parts not kept byte for byte: {drifted}")
    made = frozenset(session.mine)
    after_ids, after_words = _revisions(root, skip=made)
    if (lost := before.revisions[0] - after_ids) or any(after_words[key] != size for key, size in before.revisions[1].items()):
        problems.append(f"earlier tracked changes were lost or altered: {sorted(lost)[:3]}")
    present = [attr(element, "id") for element in root.iter() if local(element) in _REVISIONS]
    if (foreign := set(present) - before.revision_ids - made - session.cloned):
        problems.append(f"tracked changes appeared that this run did not make: {sorted(foreign)[:3]}")
    if len(present) != len(set(present)):
        problems.append("two tracked changes share an id")
    comments = session.comments.existing()
    if any(comments.get(number) != value for number, value in before.comments.items()):
        problems.append("an earlier comment was lost or altered")
    if len(comments) - before.comment_count != session.made["comments"]:
        problems.append("the comments part does not hold exactly the comments this run added")
    anchors = _anchors(root)
    if before.anchors - anchors:
        problems.append("an earlier comment's anchor was lost")
    for number in (key[1] for key in anchors - before.anchors if key[0] == "commentRangeStart"):
        if any(anchors[(kind, number)] != 1 for kind in _ANCHORS) or number not in comments:
            problems.append(f"comment {number} is not tied once at both ends and held in the comments part")
    for paragraph, text in before.paragraphs:
        if paragraph not in session.touched and current_text(paragraph) != text:
            problems.append(f"a paragraph no edit named changed: {text[:60]!r}")
    for paragraph, text in session.touched.items():
        if current_text(paragraph) != text:
            problems.append(f"an edited paragraph does not read as expected: {text[:60]!r}")
    problems.extend(_opens(saved, before.comment_count + session.made["comments"]))
    return problems


def _opens(saved: bytes, comment_count: int) -> list[str]:
    import docx
    try:
        document = docx.Document(io.BytesIO(saved))
        found = len(list(document.comments))
    except Exception as failure:  # noqa: BLE001 - any failure to open IS the finding
        return [f"the result does not open in python-docx: {type(failure).__name__}: {failure}"]
    return [] if found == comment_count else [f"python-docx reads {found} comments where {comment_count} are expected"]
