"""WordprocessingML vocabulary shared by the modules: names, and what a run's content means as text."""
from __future__ import annotations

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


class Refusal(Exception):
    """An edit that cannot be made faithfully. ``str(error)`` is for the model: what stands in the way and what to do instead."""


def q(name: str) -> str:
    return f"{{{W}}}{name}"


def local(element) -> str:
    """The local tag name; comments and processing instructions have none."""
    return etree.QName(element).localname if isinstance(element.tag, str) else ""


def attr(element, name: str) -> str | None:
    return element.get(q(name))


#: What each child of a run is as text. Anything not here and not zero-width is an object (a picture, a note reference, a field mark) the
#: run is then locked around: its words can be commented on but never rewritten.
_TEXT_OF = {"tab": "\t", "cr": "\n", "noBreakHyphen": "-"}
_ZERO_WIDTH = {"rPr", "lastRenderedPageBreak"}
_TEXT_CHILDREN = {"t", "delText"}


def run_units(run) -> list[tuple[object, str, bool]]:
    """The content of a run as ``(child, text, is_object)`` in order. A ``br`` is a line break (``\\n``) unless it is a page or column break."""
    units = []
    for child in run:
        name = local(child)
        if name in _ZERO_WIDTH:
            units.append((child, "", False))
        elif name in _TEXT_CHILDREN:
            units.append((child, child.text or "", False))
        elif name in _TEXT_OF:
            units.append((child, _TEXT_OF[name], False))
        elif name == "br" and attr(child, "type") in (None, "textWrapping"):
            units.append((child, "\n", False))
        else:
            units.append((child, "", True))
    return units


def run_text(run) -> str:
    return "".join(text for _, text, _ in run_units(run))


def text_children(text: str) -> list:
    """The run content that reads as ``text``: ``w:t`` pieces, with ``w:tab`` and ``w:br`` where the text has a tab or a line break."""
    children, buffer = [], []

    def flush() -> None:
        if buffer:
            node = etree.Element(q("t"))
            node.text = "".join(buffer)
            node.set(XML_SPACE, "preserve")
            children.append(node)
            buffer.clear()

    for character in text:
        if character in "\t\n":
            flush()
            children.append(etree.Element(q("tab" if character == "\t" else "br")))
        else:
            buffer.append(character)
    flush()
    return children
