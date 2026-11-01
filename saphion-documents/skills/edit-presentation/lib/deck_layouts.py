"""A deck's layouts, slides and placeholders as the edit-presentation scripts address them, and the edits made to them.

A layout is named by its own name, or by its number in ``numbered_layouts`` when two masters share a name. A shape of a slide is named by its
placeholder number (``idx``), ``title``, or its exact shape name. Every request that names something the deck does not have is a ``SpecError``
saying what the deck does have; nothing is guessed. The layouts, the masters and the theme are never edited: a slide takes them as they are.
"""
from __future__ import annotations

import copy

from lxml import etree
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.oxml.ns import qn

FURNITURE = {PP_PLACEHOLDER.SLIDE_NUMBER: "slide number", PP_PLACEHOLDER.FOOTER: "footer", PP_PLACEHOLDER.DATE: "date"}
#: Placeholders that hold a picture, a chart, a table or media, which these scripts do not fill.
NOT_TEXT = {PP_PLACEHOLDER.PICTURE, PP_PLACEHOLDER.CHART, PP_PLACEHOLDER.TABLE, PP_PLACEHOLDER.MEDIA_CLIP, PP_PLACEHOLDER.BITMAP,
            PP_PLACEHOLDER.ORG_CHART}


class SpecError(ValueError):
    """The request names something this deck does not have or cannot do; ``str(error)`` says what the deck has, for the model to correct."""


def kind_of(shape) -> str:
    return str(shape.placeholder_format.type).split(".")[-1].split(" ")[0].lower()


def describe(shape) -> str:
    where = f"{shape.width / 914_400:.1f} x {shape.height / 914_400:.1f} in" if shape.width is not None else "no size"
    if shape.is_placeholder:
        return f"{shape.name!r} (placeholder {shape.placeholder_format.idx}, {kind_of(shape)}, {where})"
    return f"{shape.name!r} ({where})"


def numbered_layouts(prs) -> list[tuple[int, int, object]]:
    """``(number, master number, layout)`` for every layout of every master, numbered from 1 in the order the deck lists them."""
    found = []
    for master_number, master in enumerate(prs.slide_masters, 1):
        found += [(number, master_number, layout) for number, layout in enumerate(master.slide_layouts, len(found) + 1)]
    return found


def find_layout(prs, wanted):
    layouts = numbered_layouts(prs)
    listed = "; ".join(f"{number} {layout.name!r}" for number, _, layout in layouts)
    if isinstance(wanted, int) and not isinstance(wanted, bool):
        match = [layout for number, _, layout in layouts if number == wanted]
    elif isinstance(wanted, str):
        match = [layout for _, _, layout in layouts if layout.name.casefold() == wanted.strip().casefold()]
    else:
        raise SpecError(f"A layout is named by its name or its number, not {wanted!r}. This deck's layouts: {listed}.")
    if not match:
        raise SpecError(f"This deck has no layout {wanted!r}. Its layouts: {listed}.")
    if len(match) > 1:
        raise SpecError(f"{len(match)} layouts are named {wanted!r}: name one by its number. Layouts: {listed}.")
    return match[0]


def find_shape(slide, where: str, key):
    """The shape of ``slide`` that ``key`` names: ``title``, a placeholder number, or an exact shape name."""
    shapes = list(slide.shapes)
    listed = ", ".join(describe(shape) for shape in shapes if shape.has_text_frame or shape.is_placeholder) or "no text shapes"
    key = str(key).strip()
    if key.casefold() == "title":
        if slide.shapes.title is None:
            raise SpecError(f"In {where}: there is no title placeholder. Its shapes: {listed}.")
        return slide.shapes.title
    match = ([shape for shape in shapes if shape.is_placeholder and str(shape.placeholder_format.idx) == key] if key.isdigit() else [])
    match = match or [shape for shape in shapes if shape.name.casefold() == key.casefold()]
    if len(match) != 1:
        raise SpecError(f"In {where}: there is {'no' if not match else 'more than one'} shape {key!r}. Its shapes: {listed}.")
    return match[0]


def paragraphs_of(value) -> list[tuple[str, int | None]]:
    """The paragraphs a ``set`` value stands for: one text (a line break starts a paragraph) or a list of texts or ``{"text", "level"}``."""
    items = value.split("\n") if isinstance(value, str) else value
    if not isinstance(items, list) or not items:
        raise SpecError(f"A text is a string or a non-empty list of paragraphs, not {value!r}.")
    found = []
    for item in items:
        if isinstance(item, str):
            found.append((item, None))
        elif isinstance(item, dict) and set(item) <= {"text", "level"} and isinstance(item.get("text"), str) and isinstance(item.get("level", 0), int):
            found.append((item["text"], item.get("level")))
        else:
            raise SpecError(f"A paragraph is a string or {{\"text\": ..., \"level\": 0-8}}, not {item!r}.")
    return found


def write_text(shape, value, where: str) -> None:
    """Replace a shape's text with ``value``, each new paragraph made as the shape's own are: the first run's properties and the paragraph's
    properties of the same level are copied, and bullets and sizes stay what the layout says."""
    if shape.is_placeholder and shape.placeholder_format.type in NOT_TEXT:
        raise SpecError(f"In {where}: {describe(shape)} holds a picture, chart or table, which this skill does not fill. Leave it out of `set`.")
    if not shape.has_text_frame:
        raise SpecError(f"In {where}: {describe(shape)} has no text to change.")
    items = paragraphs_of(value)
    body = shape.text_frame._txBody
    existing = body.findall(qn("a:p"))

    def level_of(paragraph) -> int:
        properties = paragraph.find(qn("a:pPr"))
        return int(properties.get("lvl", 0)) if properties is not None else 0
    models = {}
    for paragraph in existing:
        if paragraph.find(qn("a:r")) is not None:
            models.setdefault(level_of(paragraph), paragraph)
    fallback = next(iter(models.values()), None)
    made = []
    for text, level in items:
        model = models.get(level, fallback) if level is not None else fallback
        if model is None:
            paragraph = etree.SubElement(body, qn("a:p"))
            run = etree.SubElement(paragraph, qn("a:r"))
            etree.SubElement(run, qn("a:t"))
        else:
            paragraph = copy.deepcopy(model)
            runs = paragraph.findall(qn("a:r"))
            run = runs[0]
            for stale in [*runs[1:], *paragraph.findall(qn("a:br")), *paragraph.findall(qn("a:fld"))]:
                paragraph.remove(stale)
        run.find(qn("a:t")).text = text
        if level is not None and level_of(paragraph) != level:
            properties = paragraph.find(qn("a:pPr"))
            if properties is None:
                properties = etree.Element(qn("a:pPr"))
                paragraph.insert(0, properties)
            properties.set("lvl", str(level))
        made.append(paragraph)
    for paragraph in existing:
        if paragraph.getparent() is not None:
            body.remove(paragraph)
    for paragraph in made:
        body.append(paragraph)


def remove_unfilled_placeholders(slide) -> list[str]:
    """Drop the placeholders a new slide's layout gave it that were left empty (an empty one reads "Click to add" when edited and means
    nothing shown); returns what was dropped, by name."""
    dropped = []
    for shape in list(slide.shapes):
        if shape.is_placeholder and shape.placeholder_format.type not in FURNITURE and not (shape.has_text_frame and shape.text_frame.text.strip()):
            dropped.append(shape.name)
            shape._element.getparent().remove(shape._element)
    return dropped


def carry_furniture(slide, layout, existing_slides) -> None:
    """Give a new slide the slide number, footer and date that the deck's own slides show (python-pptx leaves them off): each is the deck's
    own element, set on the new layout's placeholder of that kind so it takes that layout's place and look."""
    tree = slide.shapes._spTree
    for kind in FURNITURE:
        target = next((item for item in layout.placeholders if item.placeholder_format.type == kind), None)
        donor = next((shape for old in existing_slides for shape in old.placeholders if shape.placeholder_format.type == kind), None)
        if target is None or donor is None:
            continue
        element = copy.deepcopy(donor._element)
        shape_properties = element.find(qn("p:spPr"))
        for child in list(shape_properties):
            shape_properties.remove(child)
        reference = element.find(f".//{qn('p:ph')}")
        reference.set("idx", str(target.placeholder_format.idx))
        element.find(f".//{qn('p:cNvPr')}").set("id", str(max(int(item.get("id")) for item in tree.iter(qn("p:cNvPr"))) + 1))
        tree.append(element)


def move_slide(prs, slide, position: int) -> None:
    """Place ``slide`` at ``position`` (0 is first) in the deck's order."""
    order = prs.slides._sldIdLst
    element = next(item for item in order if prs.slides.get(int(item.get("id"))) is slide)
    order.remove(element)
    order.insert(position, element)


def delete_slide(prs, slide) -> None:
    """Remove a slide from the order and drop its relationship, so its part is not saved with the deck."""
    order = prs.slides._sldIdLst
    element = next(item for item in order if prs.slides.get(int(item.get("id"))) is slide)
    prs.part.drop_rel(element.rId)
    order.remove(element)


def title_of(slide) -> str:
    """What a slide says first: its title, else the first text it holds, on one line."""
    title = slide.shapes.title
    texts = [title.text_frame.text] if title is not None else []
    texts += [shape.text_frame.text for shape in slide.shapes if shape.has_text_frame]
    return " ".join(next((text for text in texts if text.strip()), "").split())
