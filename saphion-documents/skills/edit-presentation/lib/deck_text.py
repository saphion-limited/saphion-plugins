"""How much room the text of one shape needs, and the room it has.

Written for the edit-presentation scripts, on python-pptx, lxml and Pillow only. A shape's text takes its size, font, indent and spacing from the
chain a PowerPoint deck defines: the paragraph itself, the shape's own list style, the layout's placeholder, the master's placeholder and the
master's text styles, and the theme's fonts last. ``needed_height`` walks that chain, wraps each paragraph with the matching font file and
returns the height the text takes in inches; ``available_height`` is the box minus its insets.
"""
from __future__ import annotations

import glob
import re
from functools import lru_cache

from PIL import ImageFont
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.oxml.ns import qn

EMU_PER_INCH = 914_400
POINTS_PER_INCH = 72
DEFAULT_SIZE_PT = 18.0
#: PowerPoint's own default insets of a text box, in EMU.
DEFAULT_INSETS = {"lIns": 91_440, "rIns": 91_440, "tIns": 45_720, "bIns": 45_720}
#: The font files the sandbox image holds, by the family a deck names: the metric-matched stand-ins first (Carlito for Calibri, Liberation for
#: Arial, Times New Roman and Courier New, Caladea for Cambria). A family with no stand-in is measured as DejaVu Sans, the face the render falls
#: back to, so what is measured is what the render shows.
STAND_INS = {
    "calibri": "Carlito", "arial": "LiberationSans", "helvetica": "LiberationSans", "times new roman": "LiberationSerif",
    "courier new": "LiberationMono", "cambria": "Caladea",
}
FALLBACK_FILES = {False: "DejaVuSans.ttf", True: "DejaVuSans-Bold.ttf"}
_TITLE_TYPES = {PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.VERTICAL_TITLE}
_FURNITURE_TYPES = {PP_PLACEHOLDER.SLIDE_NUMBER, PP_PLACEHOLDER.FOOTER, PP_PLACEHOLDER.DATE}


def _font_file(family: str, bold: bool) -> str | None:
    stem = STAND_INS.get(family.casefold())
    names = ([f"{stem}-{'Bold' if bold else 'Regular'}.ttf"] if stem else []) + [FALLBACK_FILES[bold]]
    for name in names:
        found = glob.glob(f"/usr/share/fonts/**/{name}", recursive=True)
        if found:
            return found[0]
    return None


@lru_cache(maxsize=256)
def font(family: str, size_pt: float, bold: bool) -> ImageFont.FreeTypeFont:
    """The face a deck's family is measured with at ``size_pt`` points, one pixel per hundredth of a point of size so widths stay precise."""
    path = _font_file(family, bold)
    scale = 100
    return (ImageFont.truetype(path, round(size_pt * scale)) if path else ImageFont.load_default(round(size_pt * scale)))


def width_in(text: str, family: str, size_pt: float, bold: bool) -> float:
    return font(family, size_pt, bold).getlength(text) / (100 * POINTS_PER_INCH)


def line_height_in(family: str, size_pt: float, bold: bool) -> float:
    ascent, descent = font(family, size_pt, bold).getmetrics()
    return (ascent + descent) / (100 * POINTS_PER_INCH)


# ---- the inheritance chain --------------------------------------------------------------------------------------------------------------


def _family(kind) -> str:
    """Which text style a placeholder takes: titles, the slide number, the footer and the date have their own; everything else is body text."""
    return "title" if kind in _TITLE_TYPES else str(kind) if kind in _FURNITURE_TYPES else "body"


def _counterpart(container, idx: int, kind) -> object | None:
    """The placeholder of a layout or master that a placeholder inherits from: the same number and family, else the first of the family."""
    same_family = [item for item in container.placeholders if _family(item.placeholder_format.type) == _family(kind)]
    return next((item for item in same_family if item.placeholder_format.idx == idx), same_family[0] if same_family else None)


def _style_sources(shape, slide) -> list:
    """The elements that can state a level's properties, nearest first: the shape's own list style, then the same placeholder on its layout and
    on the master, then the master's text style for what kind of shape it is."""
    sources = [shape._element.find(f".//{qn('a:lstStyle')}")]
    master = slide.slide_layout.slide_master
    if shape.is_placeholder:
        idx, kind = shape.placeholder_format.idx, shape.placeholder_format.type
        on_layout = _counterpart(slide.slide_layout, idx, kind)
        on_master = _counterpart(master, idx, kind)
        sources += [item._element.find(f".//{qn('a:lstStyle')}") for item in (on_layout, on_master) if item is not None]
        style = {"title": "titleStyle", "body": "bodyStyle"}.get(_family(kind), "otherStyle")
    else:
        style = "otherStyle"
    styles = master._element.find(qn("p:txStyles"))
    sources.append(styles.find(qn(f"p:{style}")) if styles is not None else None)
    return [source for source in sources if source is not None]


def _level_property(sources: list, level: int, read):
    for source in sources:
        level_element = source.find(qn(f"a:lvl{level + 1}pPr"))
        if level_element is not None and (found := read(level_element)) is not None:
            return found
    return None


def theme_blob(master) -> bytes:
    """The theme part a slide master is dressed by."""
    return next(rel.target_part for rel in master.part.rels.values() if rel.reltype.endswith("/theme")).blob


def _theme_font(slide, token: str) -> str:
    scheme = re.search(rb"<a:%sFont>\s*<a:latin typeface=\"([^\"]*)\"" % (b"major" if token.startswith("+mj") else b"minor"),
                       theme_blob(slide.slide_layout.slide_master))
    return scheme.group(1).decode("utf-8") if scheme else "Calibri"


def _spacing_value(parent, tag: str):
    node = parent.find(qn(tag))
    if node is None:
        return None
    points, percent = node.find(qn("a:spcPts")), node.find(qn("a:spcPct"))
    return ("pt", int(points.get("val")) / 100) if points is not None else ("pct", int(percent.get("val")) / 100_000)


def _default_run_value(sources: list, level: int, read):
    """What the list styles say of a run at ``level``: ``read`` is given the level's ``defRPr`` and answers None when it says nothing."""
    return _level_property(sources, level, lambda item: read(item.find(qn("a:defRPr"))) if item.find(qn("a:defRPr")) is not None else None)


def _run_properties(run_element, sources: list, level: int, slide, scale: float) -> tuple[str, float, bool]:
    """``(family, size in points, bold)`` of a run: its own, else what the chain states, else the theme's body font at 18 pt."""
    own = run_element.find(qn("a:rPr"))
    own_face = own.find(qn("a:latin")) if own is not None else None
    size = (own.get("sz") if own is not None else None) or _default_run_value(sources, level, lambda defaults: defaults.get("sz"))
    bold = (own.get("b") if own is not None else None) or _default_run_value(sources, level, lambda defaults: defaults.get("b"))
    family = (own_face.get("typeface") if own_face is not None else None) or _default_run_value(
        sources, level, lambda defaults: defaults.find(qn("a:latin")).get("typeface") if defaults.find(qn("a:latin")) is not None else None)
    family = family or "+mn-lt"
    if family.startswith("+"):
        family = _theme_font(slide, family)
    return family, (int(size) / 100 if size else DEFAULT_SIZE_PT) * scale, bold in ("1", "true")


def _wrap_lines(words: list[tuple[str, tuple[str, float, bool]]], first_width: float, width: float) -> tuple[int, float, float]:
    """``(lines, tallest line, widest unbreakable word)`` for ``words`` (each with its face) wrapped to the widths in inches."""
    lines, used, limit, tallest, widest = 1, 0.0, first_width, 0.0, 0.0
    for text, face in words:
        space = width_in(" ", *face)
        piece = width_in(text, *face)
        widest = max(widest, piece)
        tallest = max(tallest, line_height_in(*face))
        if used and used + space + piece > limit:
            lines, used, limit = lines + 1, piece, width
        else:
            used += (space if used else 0) + piece
    return lines, tallest, widest


def needed_height(shape, slide) -> tuple[float, float, float]:
    """``(inches the text needs, inches of room across, widest word)`` for ``shape``'s text frame, wrapped the way it is shown."""
    body = shape._element.find(f".//{qn('a:bodyPr')}")
    inset = {name: int(body.get(name) if body is not None and body.get(name) is not None else default) / EMU_PER_INCH
             for name, default in DEFAULT_INSETS.items()}
    shrink = body.find(qn("a:normAutofit")) if body is not None else None
    scale = int(shrink.get("fontScale", 100_000)) / 100_000 if shrink is not None else 1.0
    reduction = int(shrink.get("lnSpcReduction", 0)) / 100_000 if shrink is not None else 0.0
    wraps = body is None or body.get("wrap") != "none"
    sources = _style_sources(shape, slide)
    room = shape.width / EMU_PER_INCH - inset["lIns"] - inset["rIns"]
    total, widest_word, first = 0.0, 0.0, True
    for paragraph in shape._element.iter(qn("a:p")):
        properties = paragraph.find(qn("a:pPr"))
        level = int(properties.get("lvl", 0)) if properties is not None else 0

        left, indent = (int(_paragraph_attribute(properties, sources, level, name) or 0) / EMU_PER_INCH for name in ("marL", "indent"))
        words = []
        for run in (*paragraph.iter(qn("a:r")), *paragraph.iter(qn("a:fld"))):
            face = _run_properties(run, sources, level, slide, scale)
            words += [(word, face) for word in (run.findtext(qn("a:t")) or "").split()]
        end = paragraph.find(qn("a:endParaRPr"))
        face = words[0][1] if words else _run_properties(end if end is not None else paragraph, sources, level, slide, scale)
        spacing = _paragraph_spacing(properties, sources, level, face[1])
        line_spacing = spacing["lnSpc"]
        lines, tallest, widest = (_wrap_lines(words, room - left - max(indent, 0), room - left) if wraps and words
                                  else (1, line_height_in(*face), 0.0))
        tallest = tallest or line_height_in(*face)
        factor = max(line_spacing[1] - reduction, 0.1) if line_spacing[0] == "pct" else 1.0
        line = line_spacing[1] / POINTS_PER_INCH if line_spacing[0] == "pt" else tallest * factor
        before = 0.0 if first else _spacing_in(spacing["spcBef"], face[1])
        total += before + lines * line + _spacing_in(spacing["spcAft"], face[1])
        widest_word, first = max(widest_word, widest), False
    return total, room, widest_word


def _paragraph_attribute(properties, sources: list, level: int, name: str):
    own = properties.get(name) if properties is not None else None
    return own if own is not None else _level_property(sources, level, lambda item: item.get(name))


def _spacing_in(spacing: tuple[str, float], size_pt: float) -> float:
    return spacing[1] / POINTS_PER_INCH if spacing[0] == "pt" else spacing[1] * size_pt / POINTS_PER_INCH


def _paragraph_spacing(properties, sources: list, level: int, size_pt: float) -> dict[str, tuple[str, float]]:
    found = {}
    for tag, default in (("lnSpc", ("pct", 1.0)), ("spcBef", ("pt", 0.0)), ("spcAft", ("pt", 0.0))):
        own = _spacing_value(properties, f"a:{tag}") if properties is not None else None
        found[tag] = own or _level_property(sources, level, lambda item, tag=tag: _spacing_value(item, f"a:{tag}")) or default
    return found


def available_height(shape) -> float:
    body = shape._element.find(f".//{qn('a:bodyPr')}")
    top, bottom = (int(body.get(name)) if body is not None and body.get(name) is not None else DEFAULT_INSETS[name] for name in ("tIns", "bIns"))
    return shape.height / EMU_PER_INCH - (top + bottom) / EMU_PER_INCH


def grows_with_text(shape) -> bool:
    """A shape set to resize itself to its text (``spAutoFit``) has no height the text can overflow: it grows, and can only leave the slide."""
    body = shape._element.find(f".//{qn('a:bodyPr')}")
    return body is not None and body.find(qn("a:spAutoFit")) is not None
