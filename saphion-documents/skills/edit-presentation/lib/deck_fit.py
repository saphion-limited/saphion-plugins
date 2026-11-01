"""What is wrong on a slide before anyone looks at it: text that overflows its box, a shape off the slide, sample wording left behind.

``slide_findings`` is the one reading of a slide the scripts share: ``inspect_deck.py`` reports it for the whole template, ``edit_deck.py`` refuses to
deliver a deck whose added or updated slides have any. It measures (``deck_text``); it never looks at a render. Shapes it cannot measure (a table, a
chart, a picture, a group) are named as not measured, never passed as fine.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from deck_text import EMU_PER_INCH, available_height, grows_with_text, needed_height
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn

#: Measurement is an estimate: a box is overflowing only when the text is this much taller than it, or a word is wider than it.
HEIGHT_TOLERANCE = 1.03
EDGE_TOLERANCE_IN = 0.02
LEFTOVER = re.compile(r"lorem ipsum|\bclick to (?:edit|add)\b|\bx{3,}\b|\[insert|\bTODO\b|\bsample (?:text|title)\b|\byour (?:text|title) here\b", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    slide: int
    shape: str
    kind: str  # overflow | word_too_wide | off_slide | leftover | not_measured
    detail: str

    @property
    def blocks(self) -> bool:
        """Whether the finding is a defect (``not_measured`` only says what a person must look at in the render)."""
        return self.kind != "not_measured"

    def __str__(self) -> str:
        return f"slide {self.slide}, {self.shape!r}: {self.detail}"


def _text_shapes(slide):
    """The shapes that hold text. A shape with no text body is left alone: asking python-pptx for its text frame would add one to the deck."""
    return [shape for shape in slide.shapes
            if shape.shape_type != MSO_SHAPE_TYPE.GROUP and shape.has_text_frame and shape._element.find(qn("p:txBody")) is not None]


def slide_findings(slide, number: int, slide_width: int, slide_height: int) -> list[Finding]:
    found: list[Finding] = []
    for shape in slide.shapes:
        name = shape.name
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            found.append(Finding(number, name, "not_measured", "a group: its contents are not measured, check it in the render"))
        elif shape.has_chart or shape.has_table:
            found.append(Finding(number, name, "not_measured", "a chart or table: its fit is not measured, check it in the render"))
        if None in (shape.left, shape.top, shape.width, shape.height):
            continue
        right, bottom = (shape.left + shape.width) / EMU_PER_INCH, (shape.top + shape.height) / EMU_PER_INCH
        if (shape.left < -EDGE_TOLERANCE_IN * EMU_PER_INCH or shape.top < -EDGE_TOLERANCE_IN * EMU_PER_INCH
                or right > slide_width / EMU_PER_INCH + EDGE_TOLERANCE_IN or bottom > slide_height / EMU_PER_INCH + EDGE_TOLERANCE_IN):
            found.append(Finding(number, name, "off_slide", f"the shape reaches {right:.2f} x {bottom:.2f} in on a "
                                 f"{slide_width / EMU_PER_INCH:.2f} x {slide_height / EMU_PER_INCH:.2f} in slide"))
    for shape in _text_shapes(slide):
        text = shape.text_frame.text
        if not text.strip():
            continue
        if LEFTOVER.search(text):
            found.append(Finding(number, shape.name, "leftover", f"sample or placeholder wording is left: {LEFTOVER.search(text).group(0)!r}"))
        need, room, widest = needed_height(shape, slide)
        if widest > room:
            found.append(Finding(number, shape.name, "word_too_wide", f"a word is {widest:.2f} in wide in a box with {room:.2f} in of room"))
        if grows_with_text(shape):
            bottom = shape.top / EMU_PER_INCH + need
            if bottom > slide_height / EMU_PER_INCH + EDGE_TOLERANCE_IN:
                found.append(Finding(number, shape.name, "off_slide", f"the box grows with its text to {bottom:.2f} in, past the slide's bottom"))
        elif need > available_height(shape) * HEIGHT_TOLERANCE:
            shrinks = shape._element.find(f".//{qn('a:normAutofit')}") is not None
            found.append(Finding(number, shape.name, "overflow", f"the text needs {need:.2f} in and the box has {available_height(shape):.2f} in"
                                 + (" (its shrink-on-overflow only applies when PowerPoint recalculates, so it would overflow as saved)" if shrinks else "")))
    return found
