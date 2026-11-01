"""Put back what openpyxl rebuilds from its own model: a sheet's drawing (charts, pictures, shapes) and its comments, as the person's file had them.

openpyxl rewrites a chart from the part of it that it models: the chart's style and colour parts, its extension elements, a picture's own
part and the box Excel sized for a note are not in that model, and the counts of charts and comments stay equal while they change. The
edit never changes a drawing or a comment, so for every sheet that has one both before and after, the supplied package's own parts replace
the rebuilt ones: the drawing, the charts it holds with their style and colour parts, the media, the comments and the note boxes, each byte
for byte. Only where a row inserted on a sheet moves what they point at is a part edited, and only in the numbers that moved: the rows of an
anchor or of a note, the cells a chart reads (``workbook_refs``).
"""
from __future__ import annotations

import io
import posixpath
import zipfile
from collections.abc import Callable
from dataclasses import dataclass

from lxml import etree
from workbook_refs import RowMap, UnmovableReference, remap_formula, remap_reference

PACKAGE_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_ID = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
DRAWING = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
CHART = "http://schemas.openxmlformats.org/drawingml/2006/chart"
EXCEL = "urn:schemas-microsoft-com:office:excel"
#: The relationships of a sheet whose target is put back, by the last word of the relationship type.
RESTORED = ("drawing", "comments", "vmlDrawing")


class PartsUnmovable(ValueError):
    """A part that must move with inserted rows cannot be read to move it; ``str(error)`` says which."""


@dataclass
class Rel:
    id: str
    type: str
    target: str  # the package part it points at, from the package root, no leading slash


def _parser() -> etree.XMLParser:
    return etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)


def _rels_name(part: str) -> str:
    return posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")


def _rels(files: dict[str, bytes], part: str) -> list[Rel]:
    name = _rels_name(part)
    if name not in files:
        return []
    found = []
    for rel in etree.fromstring(files[name], _parser()).iter(f"{{{PACKAGE_REL}}}Relationship"):
        if rel.get("TargetMode") == "External":
            continue
        target = rel.get("Target") or ""
        found.append(Rel(rel.get("Id") or "", (rel.get("Type") or "").rsplit("/", 1)[-1],
                         target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(part), target))))
    return found


def _sheets(files: dict[str, bytes]) -> dict[str, str]:
    targets = {rel.get("Id"): rel.get("Target") for rel in etree.fromstring(files["xl/_rels/workbook.xml.rels"], _parser()).iter(f"{{{PACKAGE_REL}}}Relationship")}
    found = {}
    for sheet in etree.fromstring(files["xl/workbook.xml"], _parser()).iter(f"{{{MAIN}}}sheet"):
        target = targets[sheet.get(f"{{{REL_ID}}}id")]
        found[sheet.get("name")] = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("xl", target))
    return found


def _closure(files: dict[str, bytes], root: str) -> list[str]:
    """``root`` and every part it reaches through relationships, in the order reached."""
    seen, pending = [], [root]
    while pending:
        part = pending.pop(0)
        if part in seen or part not in files:
            continue
        seen.append(part)
        pending.extend(rel.target for rel in _rels(files, part))
    return seen


def _content_types(files: dict[str, bytes]) -> tuple[dict[str, str], dict[str, str]]:
    root = etree.fromstring(files["[Content_Types].xml"], _parser())
    return ({item.get("PartName").lstrip("/"): item.get("ContentType") for item in root.iter(f"{{{CONTENT_TYPES}}}Override")},
            {item.get("Extension").lower(): item.get("ContentType") for item in root.iter(f"{{{CONTENT_TYPES}}}Default")})


def _free(name: str, taken: set[str]) -> str:
    stem, dot, extension = name.rpartition(".")
    candidate, number = name, 1
    while candidate in taken:
        number += 1
        candidate = f"{stem}-{number}{dot}{extension}"
    return candidate


def _row_text(element: etree._Element, sheet: str, rows: RowMap) -> bool:
    """Move a zero-based row number held as text; whether it changed."""
    moved = str(rows.row(sheet, int(element.text) + 1) - 1)
    changed = moved != element.text.strip()
    element.text = moved
    return changed


def _patch_drawing(data: bytes, sheet: str, rows: RowMap) -> bytes:
    root, changed = etree.fromstring(data, _parser()), False
    for end in (*root.iter(f"{{{DRAWING}}}from"), *root.iter(f"{{{DRAWING}}}to")):
        for row in end.iter(f"{{{DRAWING}}}row"):
            changed |= _row_text(row, sheet, rows)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True) if changed else data


def _patch_chart(data: bytes, rows: RowMap, sheet: str, part: str) -> bytes:
    root, changed = etree.fromstring(data, _parser()), False
    for formula in root.iter(f"{{{CHART}}}f"):
        try:
            moved = remap_formula("=" + (formula.text or ""), None, rows)[1:]
        except UnmovableReference as failure:
            raise PartsUnmovable(f"the chart {part!r} on {sheet!r} reads a range that cannot be moved with the inserted rows ({failure})") from failure
        changed |= moved != formula.text
        formula.text = moved
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True) if changed else data


def _patch_comments(data: bytes, sheet: str, rows: RowMap) -> bytes:
    root, changed = etree.fromstring(data, _parser()), False
    for comment in root.iter(f"{{{MAIN}}}comment"):
        moved = remap_reference(comment.get("ref"), sheet, rows, extend=False) or comment.get("ref")
        changed |= moved != comment.get("ref")
        comment.set("ref", moved)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True) if changed else data


def _patch_note_boxes(data: bytes, sheet: str, rows: RowMap) -> bytes:
    try:
        root = etree.fromstring(data, _parser())
    except etree.XMLSyntaxError as failure:
        raise PartsUnmovable(f"the note boxes of {sheet!r} cannot be read to move them with the inserted rows: {failure}") from failure
    changed = False
    for data_ in root.iter(f"{{{EXCEL}}}ClientData"):
        for row in data_.iter(f"{{{EXCEL}}}Row"):
            changed |= _row_text(row, sheet, rows)
        for anchor in data_.iter(f"{{{EXCEL}}}Anchor"):
            numbers = [item.strip() for item in (anchor.text or "").split(",")]
            for index in (2, 6):
                moved = str(rows.row(sheet, int(numbers[index]) + 1) - 1)
                changed |= moved != numbers[index]
                numbers[index] = moved
            anchor.text = ", ".join(numbers)
    return etree.tostring(root, encoding="UTF-8") if changed else data


def _patcher(part: str, content_type: str, sheet: str, rows: RowMap) -> Callable[[bytes], bytes] | None:
    if content_type.endswith("drawing+xml"):
        return lambda data: _patch_drawing(data, sheet, rows)
    if content_type.endswith("drawingml.chart+xml"):
        return lambda data: _patch_chart(data, rows, sheet, part)
    if content_type.endswith("spreadsheetml.comments+xml"):
        return lambda data: _patch_comments(data, sheet, rows)
    if part.endswith(".vml"):
        return lambda data: _patch_note_boxes(data, sheet, rows)
    return None


def restore_parts(original: bytes, delivered: bytes, rows: RowMap) -> tuple[bytes, list[str]]:
    """``delivered`` with each sheet's drawing and comments (and what they hold) replaced by the supplied package's own, moved by ``rows``;
    the sheets it put back, in words."""
    with zipfile.ZipFile(io.BytesIO(original)) as archive:
        before = {item.filename: archive.read(item.filename) for item in archive.infolist()}
    with zipfile.ZipFile(io.BytesIO(delivered)) as archive:
        after = {item.filename: archive.read(item.filename) for item in archive.infolist()}
    original_types, original_defaults = _content_types(before)
    types, defaults = _content_types(after)
    original_sheets, sheets, kept = _sheets(before), _sheets(after), []
    for name, sheet_part in sheets.items():
        if name not in original_sheets:
            continue
        had = {rel.type: rel for rel in _rels(before, original_sheets[name]) if rel.type in RESTORED}
        now = {rel.type: rel for rel in _rels(after, sheet_part) if rel.type in RESTORED}
        for kind in (kind for kind in RESTORED if kind in had and kind in now):
            for gone in _closure(after, now[kind].target):
                for dropped in (gone, _rels_name(gone)):
                    after.pop(dropped, None)
                types.pop(gone, None)
            names: dict[str, str] = {}
            for part in _closure(before, had[kind].target):
                names[part] = _free(part, set(after) | set(names.values()))
            for part, new in names.items():
                data = before[part]
                if rows and (patch := _patcher(part, original_types.get(part, ""), name, rows)):
                    data = patch(data)  # unchanged bytes when nothing it points at has moved
                after[new] = data
                extension = part.rpartition(".")[2].lower()
                if part in original_types:
                    types[new] = original_types[part]
                elif extension not in defaults:
                    defaults[extension] = original_defaults[extension]
                if _rels_name(part) in before:
                    after[_rels_name(new)] = _renamed(before[_rels_name(part)], part, names)
            sheet_rels = etree.fromstring(after[_rels_name(sheet_part)], _parser())
            for rel in sheet_rels.iter(f"{{{PACKAGE_REL}}}Relationship"):
                if rel.get("Id") == now[kind].id:
                    rel.set("Target", "/" + names[had[kind].target])
            after[_rels_name(sheet_part)] = etree.tostring(sheet_rels, xml_declaration=True, encoding="UTF-8", standalone=True)
            kept.append(f"{name}: {kind}")
    after["[Content_Types].xml"] = _write_content_types(types, defaults)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target:
        for part in sorted(after, key=lambda item: (item != "[Content_Types].xml", item)):
            target.writestr(part, after[part])
    return out.getvalue(), kept


def _renamed(rels: bytes, part: str, names: dict[str, str]) -> bytes:
    """A part's relationships file with each target that was given a new name pointing at it; the bytes themselves when no name changed."""
    root, changed = etree.fromstring(rels, _parser()), False
    for rel in root.iter(f"{{{PACKAGE_REL}}}Relationship"):
        target = rel.get("Target") or ""
        absolute = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(part), target))
        if rel.get("TargetMode") != "External" and names.get(absolute, absolute) != absolute:
            rel.set("Target", "/" + names[absolute])
            changed = True
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True) if changed else rels


def _write_content_types(types: dict[str, str], defaults: dict[str, str]) -> bytes:
    root = etree.Element(f"{{{CONTENT_TYPES}}}Types", nsmap={None: CONTENT_TYPES})
    for extension, content_type in defaults.items():
        etree.SubElement(root, f"{{{CONTENT_TYPES}}}Default", Extension=extension, ContentType=content_type)
    for part, content_type in types.items():
        etree.SubElement(root, f"{{{CONTENT_TYPES}}}Override", PartName="/" + part, ContentType=content_type)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
