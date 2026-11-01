"""Comments: the comments part, and the range markers that tie a comment to the words it is about."""
from __future__ import annotations

from lxml import etree

from .ooxml import XML_SPACE, Refusal, attr, q
from .package import Package
from .paragraphs import cut_at, scan

#: A comment only ties itself to words: it may sit on anything the paragraph reads, including a tracked insertion or a field's result.
ANYWHERE = frozenset({"plain", "inserted", "locked"})


class Comments:
    """The document's comments part, made only when the first comment is added. Existing comments are never rewritten; a new one is appended."""

    def __init__(self, package: Package) -> None:
        self.package = package
        found = [name for name in package.related("comments") if package.has(name)]
        self.name = found[0] if found else None
        styles = package.related("styles")
        self._styles = {attr(style, "styleId") for style in package.root(styles[0]).iter(q("style"))} if styles else set()

    def existing(self) -> dict[str, tuple[str | None, str | None, str]]:
        """Each comment by id: its author, its date and its words."""
        if self.name is None:
            return {}
        return {attr(comment, "id"): (attr(comment, "author"), attr(comment, "date"), "".join(comment.itertext()))
                for comment in self.package.root(self.name).iter(q("comment"))}

    def _open(self):
        if self.name is None:
            self.name = self.package.comments_part()
        self.package.touch(self.name)
        return self.package.root(self.name)

    def _styled(self, kind: str, style: str):
        """A ``w:pStyle`` or ``w:rStyle`` for ``style``, only when the document defines it (a style it lacks would be named for nothing)."""
        if style not in self._styles:
            return None
        element = etree.Element(q(kind))
        element.set(q("val"), style)
        return element

    def add(self, number: int, author: str, initials: str, date: str, text: str) -> None:
        comment = etree.SubElement(self._open(), q("comment"))
        for name, value in (("id", str(number)), ("author", author), ("date", date), ("initials", initials)):
            comment.set(q(name), value)
        for index, line in enumerate(text.split("\n")):
            paragraph = etree.SubElement(comment, q("p"))
            if (style := self._styled("pStyle", "CommentText")) is not None:
                etree.SubElement(paragraph, q("pPr")).append(style)
            if index == 0:
                mark = etree.SubElement(paragraph, q("r"))
                if (style := self._styled("rStyle", "CommentReference")) is not None:
                    etree.SubElement(mark, q("rPr")).append(style)
                etree.SubElement(mark, q("annotationRef"))
            words = etree.SubElement(etree.SubElement(paragraph, q("r")), q("t"))
            words.text = line
            words.set(XML_SPACE, "preserve")

    def reference_run(self, number: int):
        run = etree.Element(q("r"))
        if (style := self._styled("rStyle", "CommentReference")) is not None:
            etree.SubElement(run, q("rPr")).append(style)
        etree.SubElement(run, q("commentReference")).set(q("id"), str(number))
        return run


def anchor(comments: Comments, paragraph, start: int, end: int, number: int) -> None:
    """Tie comment ``number`` to characters ``start`` to ``end`` of the paragraph's current text: runs are cut at both ends, then the range markers
    and the reference run are placed exactly there."""
    if end <= start:
        raise Refusal("A comment needs words to sit on: these are empty. Comment on the words beside them.")
    cut_at(paragraph, end, kinds=ANYWHERE)
    cut_at(paragraph, start, kinds=ANYWHERE)
    covered = [piece for piece in scan(paragraph) if piece.end > piece.start and start <= piece.start and piece.end <= end]
    if not covered or covered[0].start != start or covered[-1].end != end:
        raise Refusal("These words could not be reached as runs of text, so the comment has nothing to be tied to.")
    begin, finish = etree.Element(q("commentRangeStart")), etree.Element(q("commentRangeEnd"))
    begin.set(q("id"), str(number))
    finish.set(q("id"), str(number))
    covered[0].element.addprevious(begin)
    covered[-1].element.addnext(finish)
    finish.addnext(comments.reference_run(number))
