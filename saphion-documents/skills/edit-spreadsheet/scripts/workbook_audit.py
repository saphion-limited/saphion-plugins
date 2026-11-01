"""Prove an edit lost nothing, from the saved file itself.

openpyxl carries most of a workbook through a load and a save, and silently drops some of it: shapes and text boxes, sparklines, slicers,
form controls, and what Excel stores in its extension lists. So the audit counts what the supplied package holds, by what a person would
call it and by sheet, reads the delivered package the same way, and refuses a delivery that holds less (unless the person agreed to lose that
kind of thing). It then compares every cell the person had, moved to where the edit put it: its value, its formula, its formatting; and the
sheet's widths, heights, panes and order. Nothing here trusts the edit: it reads what was written.
"""
from __future__ import annotations

import io
import posixpath
import zipfile
from collections import Counter
from copy import copy
from typing import Any

import openpyxl
from lxml import etree
from workbook_edits import Applied, formula_text
from workbook_refs import remap_formula, remap_reference

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
X14 = "http://schemas.microsoft.com/office/spreadsheetml/2009/9/main"
DRAWING = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
CHART = "http://schemas.openxmlformats.org/drawingml/2006/chart"
REL_ID = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
WORKBOOK_SCOPE = "the workbook"

#: What the audit counts, by the name an ``accept_losses`` entry uses and the words a refusal says. Formulas are not here: they are never
#: given up, and are counted exactly against what the plan wrote.
KINDS = {
    "merged_cells": "merged cells", "conditional_formatting": "conditional formatting rules", "dropdowns_and_rules": "dropdowns and input rules",
    "hyperlinks": "hyperlinks", "comments": "comments", "threaded_comments": "threaded comments", "tables": "Excel tables", "pivot_tables": "pivot tables",
    "slicers": "slicers", "frozen_panes": "frozen panes", "sheet_protection": "protected sheets", "filters": "filters", "form_controls": "form controls",
    "charts": "charts", "pictures": "pictures", "shapes": "shapes or text boxes", "other_drawing_objects": "other drawn objects",
    "sparklines": "sparklines", "extended_conditional_formatting": "extended conditional formatting (icon sets and data bars from newer Excel)",
    "extended_dropdowns": "extended dropdowns", "names": "named ranges", "external_links": "links to other workbooks", "pivot_caches": "pivot caches",
    "macros": "macros", "embedded_objects": "embedded objects", "custom_xml": "custom data parts", "workbook_protection": "workbook protection",
}
_SHEET_TAGS = {
    (MAIN, "mergeCell"): "merged_cells", (MAIN, "conditionalFormatting"): "conditional_formatting", (MAIN, "dataValidation"): "dropdowns_and_rules",
    (MAIN, "hyperlink"): "hyperlinks", (MAIN, "tablePart"): "tables", (MAIN, "pane"): "frozen_panes", (MAIN, "sheetProtection"): "sheet_protection",
    (MAIN, "autoFilter"): "filters", (MAIN, "control"): "form_controls", (X14, "sparkline"): "sparklines",
    (X14, "conditionalFormatting"): "extended_conditional_formatting", (X14, "dataValidation"): "extended_dropdowns",
}
_DRAWING_TAGS = {
    (DRAWING, "sp"): "shapes", (DRAWING, "cxnSp"): "shapes", (DRAWING, "grpSp"): "shapes", (DRAWING, "pic"): "pictures", (CHART, "chart"): "charts",
}
_RELATED = {"comments": "comments", "threadedComment": "threaded_comments", "pivotTable": "pivot_tables", "slicer": "slicers", "ctrlProp": "form_controls"}


class AuditFailed(ValueError):
    """The edited file is not a faithful edit; ``str(error)`` names what differs, for the model to correct or to tell the person."""


def _parse(archive: zipfile.ZipFile, name: str) -> etree._Element:
    return etree.fromstring(archive.read(name), etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True))


def _related(archive: zipfile.ZipFile, part: str) -> list[tuple[str, str]]:
    """The (relationship type, part) pairs a part points at."""
    rels = posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")
    if rels not in archive.namelist():
        return []
    found = []
    for rel in _parse(archive, rels).iter(f"{{{PACKAGE_REL}}}Relationship"):
        target = rel.get("Target") or ""
        if rel.get("TargetMode") == "External":
            continue
        resolved = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(part), target))
        found.append(((rel.get("Type") or "").rsplit("/", 1)[-1], resolved))
    return found


def _tally(root: Any, tags: dict[tuple[str, str], str], counts: Counter, scope: str) -> None:
    for element in root.iter():
        if isinstance(element.tag, str):
            name = etree.QName(element)
            if (kind := tags.get((name.namespace, name.localname))):
                counts[(scope, kind)] += 1


def inventory(data: bytes) -> Counter:
    """What the package holds, as ``(sheet or the workbook, kind) -> count`` (``KINDS`` and ``formulas``)."""
    counts: Counter = Counter()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        workbook = _parse(archive, "xl/workbook.xml")
        parts = {rel.get("Id"): rel.get("Target") for rel in _parse(archive, "xl/_rels/workbook.xml.rels").iter(f"{{{PACKAGE_REL}}}Relationship")}
        for sheet in workbook.iter(f"{{{MAIN}}}sheet"):
            name, target = sheet.get("name"), parts[sheet.get(f"{{{REL_ID}}}id")]
            part = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("xl", target))
            root = _parse(archive, part)
            counts[(name, "formulas")] = sum(1 for _ in root.iter(f"{{{MAIN}}}f"))
            _tally(root, _SHEET_TAGS, counts, name)
            for kind, related in _related(archive, part):
                if kind == "drawing":
                    drawing = _parse(archive, related)
                    _tally(drawing, _DRAWING_TAGS, counts, name)
                    frames = sum(1 for _ in drawing.iter(f"{{{DRAWING}}}graphicFrame"))
                    counts[(name, "other_drawing_objects")] += max(frames - counts[(name, "charts")], 0)
                elif kind in _RELATED:
                    counts[(name, _RELATED[kind])] += (sum(1 for _ in _parse(archive, related).iter(f"{{{MAIN}}}comment")) if kind == "comments" else 1)
        counts[(WORKBOOK_SCOPE, "names")] = sum(1 for item in workbook.iter(f"{{{MAIN}}}definedName") if not (item.get("name") or "").startswith("_xlnm."))
        counts[(WORKBOOK_SCOPE, "external_links")] = sum(1 for _ in workbook.iter(f"{{{MAIN}}}externalReference"))
        counts[(WORKBOOK_SCOPE, "pivot_caches")] = sum(1 for _ in workbook.iter(f"{{{MAIN}}}pivotCache"))
        counts[(WORKBOOK_SCOPE, "workbook_protection")] = sum(1 for item in workbook.iter(f"{{{MAIN}}}workbookProtection") if item.attrib)
        counts[(WORKBOOK_SCOPE, "macros")] = sum(1 for name in names if name.endswith("vbaProject.bin"))
        counts[(WORKBOOK_SCOPE, "embedded_objects")] = sum(1 for name in names if name.startswith(("xl/embeddings/", "xl/activeX/")))
        counts[(WORKBOOK_SCOPE, "custom_xml")] = sum(1 for name in names if name.startswith("customXml/") and name.endswith(".xml") and "item" in name
                                                    and "Props" not in name)
    return +counts


def losses(before: Counter, after: Counter, accepted: frozenset[str]) -> tuple[list[str], list[str]]:
    """``(refused, accepted)``: the content the delivered file holds less of than the supplied one, said in plain words."""
    refused, agreed = [], []
    for (scope, kind), held in sorted(before.items()):
        if kind == "formulas" or after[(scope, kind)] >= held:
            continue
        said = f"{held - after[(scope, kind)]} of {held} {KINDS[kind]} on {scope!r}" if scope != WORKBOOK_SCOPE else f"{KINDS[kind]} ({held} before, {after[(scope, kind)]} now)"
        (agreed if kind in accepted else refused).append(f"{said} [{kind}]")
    return refused, agreed


def _same_style(left: Any, right: Any) -> bool:
    return (left.number_format == right.number_format and all(copy(getattr(left, name)) == copy(getattr(right, name))
            for name in ("font", "fill", "border", "alignment", "protection")))


def _columns(sheet: Any) -> dict[int, tuple[Any, bool]]:
    found = {}
    for dimension in sheet.column_dimensions.values():
        for index in range(dimension.min or 1, (dimension.max or dimension.min or 1) + 1):
            found[index] = (dimension.width, bool(dimension.hidden))
    return found


def compare_cells(original: Any, edited: Any, applied: Applied) -> list[str]:
    """What differs between every cell the person had and the cell the edit left in its place; empty when nothing does."""
    problems: list[str] = []
    rows = applied.rows
    names = [sheet.title for sheet in edited.worksheets]
    held = [name for name in names if name in original.sheetnames]
    if held != original.sheetnames:
        problems.append(f"the sheets are {names} where the supplied workbook's {original.sheetnames} should keep their order")
    for name in original.sheetnames:
        if name not in edited.sheetnames:
            problems.append(f"sheet {name!r} is missing")
            continue
        before, after = original[name], edited[name]
        if before.sheet_state != after.sheet_state:
            problems.append(f"sheet {name!r} was {before.sheet_state} and is now {after.sheet_state}")
        for (row, column), cell in before._cells.items():
            if not (cell.has_style or cell.value is not None):
                continue
            moved = after._cells.get((rows.row(name, row), column))
            where = f"{name}!{cell.coordinate}"
            if moved is None:
                problems.append(f"{where} has no cell where it should now be")
                continue
            address = (name, row, column)
            held_formula = formula_text(cell.value)
            if address in applied.edited:
                pass
            elif held_formula is not None:
                now = formula_text(moved.value)
                expected = remap_formula(held_formula, name, rows)
                if now != expected:
                    problems.append(f"{where} was {held_formula} and should now read {expected}, but reads {now}")
            elif cell.value != moved.value:
                problems.append(f"{where} held {cell.value!r} and now holds {moved.value!r}")
            if not _same_style(cell, moved):
                problems.append(f"{where} lost its formatting")
        if _columns(before) != _columns(after):
            problems.append(f"the column widths or hidden columns of {name!r} changed")
        for index, dimension in before.row_dimensions.items():
            moved = after.row_dimensions.get(rows.row(name, index))
            if moved is None or (dimension.height, dimension.hidden) != (moved.height, moved.hidden):
                problems.append(f"the height or hiding of row {index} of {name!r} changed")
        if before.freeze_panes and remap_reference(before.freeze_panes, name, rows, extend=False) != after.freeze_panes:
            problems.append(f"the frozen panes of {name!r} moved from {before.freeze_panes} to {after.freeze_panes}")
        if (before.sheet_properties.tabColor, before.sheet_view.zoomScale, before.sheet_view.showGridLines) != (
                after.sheet_properties.tabColor, after.sheet_view.zoomScale, after.sheet_view.showGridLines):
            problems.append(f"the tab colour, zoom or gridlines of {name!r} changed")
    return problems


def errors_in(workbook: Any) -> dict[tuple[str, int, int], str]:
    """Every cell showing an error value, in a workbook opened for its values."""
    found = {}
    for sheet in workbook.worksheets:
        for (row, column), cell in sheet._cells.items():
            if isinstance(cell.value, str) and (cell.value in openpyxl.cell.cell.ERROR_CODES or cell.value.startswith("Err:")):
                found[(sheet.title, row, column)] = cell.value
    return found
