"""Carry a plan out on an open workbook: set inputs, add a sheet, insert rows, and move everything that points at the rows that moved.

openpyxl's own ``insert_rows`` moves only the cells: every formula, name, conditional format, validation, table, merge, chart and print area
keeps pointing at the old rows, which is how a totals formula silently stops counting the new rows. Here the insertions are held once
(``RowMap``) and every one of those things is moved by it. What this does not move is refused by name before anything changes, and the audit
(``workbook_audit``) reads the saved file back to prove nothing else was lost.
"""
from __future__ import annotations

import datetime
from collections import Counter
from copy import copy
from dataclasses import dataclass, field, replace
from typing import Any

from openpyxl.cell.cell import MergedCell
from openpyxl.formatting.formatting import ConditionalFormattingList
from openpyxl.formula.translate import Translator
from openpyxl.styles import DEFAULT_FONT
from openpyxl.styles.numbers import is_date_format
from openpyxl.utils.cell import (
    column_index_from_string,
    get_column_letter,
)
from openpyxl.worksheet.cell_range import MultiCellRange
from openpyxl.worksheet.formula import ArrayFormula, DataTableFormula
from workbook_plan import InsertRows, NewSheet, Plan, PlanRefused, SetCell, cell_address
from workbook_refs import (
    OWN_ROW,
    Insertion,
    RowMap,
    UnmovableReference,
    remap_formula,
    remap_reference,
    remap_sqref,
)

Address = tuple[str, int, int]  # sheet, row, column, as the workbook was supplied


@dataclass
class Applied:
    """What the plan did, as the audit and the report need it."""
    rows: RowMap = field(default_factory=lambda: RowMap([]))
    overwritten: set[Address] = field(default_factory=set)  # formulas the plan replaced with a value, as supplied
    edited: set[Address] = field(default_factory=set)  # cells the plan set, as supplied
    formulas_added: int = 0
    inserted: list[dict[str, Any]] = field(default_factory=list)
    extended: list[str] = field(default_factory=list)  # formulas that now include the new rows, as they now read
    blank: dict[str, str] = field(default_factory=dict)  # new rows' columns the copied row held a value in and nothing was given
    sheets_added: list[str] = field(default_factory=list)


def formula_text(value: Any) -> str | None:
    if isinstance(value, ArrayFormula):
        return value.text
    if isinstance(value, DataTableFormula):
        return "(data table)"
    return value if isinstance(value, str) and value.startswith("=") else None


BaseFont = tuple[str, float]  # the (name, size) a workbook's cells are mostly written in


def base_font(workbook: Any) -> BaseFont:
    """The (name, size) most of the workbook's cells with something in them are written in.

    Read once, from the workbook as supplied, before the plan writes anything: a cell the plan makes is written in what the person's own cells are
    written in, not in openpyxl's Calibri 11 (which is what an unstyled cell reads as, and so how a new cell would otherwise look beside Arial 10).
    On a tie the font met first (sheet order, then cell order) wins. A workbook with nothing in it has only the default font.
    """
    held = Counter((cell.font.name, cell.font.sz) for sheet in workbook.worksheets for cell in sheet._cells.values()
                   if cell.value is not None and cell.font.name and cell.font.sz)
    return held.most_common(1)[0][0] if held else (DEFAULT_FONT.name, DEFAULT_FONT.sz)


def _in_base_font(cell: Any, base: BaseFont) -> None:
    """Write ``cell`` in the workbook's base font, keeping everything else about its font (bold, colour). A font tied to the theme's font
    (``scheme``) would show the theme's font whatever its name says, so it is let go when the name changes."""
    if (cell.font.name, cell.font.sz) != base:
        font = copy(cell.font)
        font.name, font.sz = base
        font.scheme = None
        cell.font = font


def _sheet(workbook: Any, name: str) -> Any:
    if name not in workbook.sheetnames:
        raise PlanRefused(f"The workbook has no sheet {name!r}. Its sheets: {', '.join(repr(item) for item in workbook.sheetnames)}.")
    return workbook[name]


def _typed(cell: Any, value: Any) -> Any:
    """``value`` as the cell holds it: an ISO date or date-time text written into a date-formatted cell becomes a real date."""
    if isinstance(value, str) and not value.startswith("=") and is_date_format(cell.number_format):
        try:
            moment = datetime.datetime.fromisoformat(value)
        except ValueError:
            return value
        return moment.date() if len(value) <= 10 else moment
    return value


def _set(workbook: Any, step: SetCell, applied: Applied, base: BaseFont) -> None:
    sheet = _sheet(workbook, step.sheet)
    cell = sheet[step.cell]
    if isinstance(cell, MergedCell):
        anchor = next(item for item in sheet.merged_cells.ranges if step.cell in item)
        raise PlanRefused(f"{step.sheet}!{step.cell} is inside the merged range {anchor.coord}: write to its top-left cell {anchor.start_cell.coordinate}.")
    held = formula_text(cell.value)
    if held is not None and not step.confirmed_fixed_value:
        raise PlanRefused(f"{step.sheet}!{step.cell} holds the formula {held}. A formula is not an input: change the input it reads. Turning this cell "
                          "into a fixed value is more than was asked, since it stops calculating: ask the person in words, naming the cell and what stops "
                          f"calculating, and only after their yes put \"confirmed_fixed_value\": \"{step.cell}\" on this entry.")
    if held is not None:
        applied.overwritten.add((step.sheet, cell.row, cell.column))
    new = cell.value is None and not cell.has_style  # a cell the person did not have: the audit leaves it out, so it may take the base font
    cell.value = _typed(cell, step.value)
    if new:
        _in_base_font(cell, base)
    applied.edited.add((step.sheet, cell.row, cell.column))
    applied.formulas_added += formula_text(cell.value) is not None


def _add_sheet(workbook: Any, step: NewSheet, applied: Applied, base: BaseFont) -> None:
    if step.name.casefold() in {name.casefold() for name in workbook.sheetnames}:
        raise PlanRefused(f"The workbook already has a sheet called {step.name!r}; sheet names are the same in any letter case.")
    sheet = workbook.create_sheet(step.name, step.position)
    for item in step.cells:
        cell = sheet[item.cell]
        if item.style_from:
            name, _, address = item.style_from.rpartition("!")
            source = _sheet(workbook, name.strip("'").replace("''", "'"))[cell_address(address, f"style_from {item.style_from!r}")]
            cell._style = copy(source._style)
        else:
            _in_base_font(cell, base)
        cell.value = _typed(cell, item.value)
        if item.number_format:
            cell.number_format = item.number_format
        if item.bold is not None:
            font = copy(cell.font)
            font.bold = item.bold
            cell.font = font
        applied.formulas_added += formula_text(cell.value) is not None
    for column, width in step.column_widths.items():
        sheet.column_dimensions[column].width = width
    applied.sheets_added.append(step.name)


def _check_can_move(sheet: Any, step: InsertRows) -> None:
    if step.before_row > sheet.max_row + 1:
        raise PlanRefused(f"insert_rows on {sheet.title!r}: before_row {step.before_row} is past the sheet's last row ({sheet.max_row}). "
                          f"Use {sheet.max_row + 1} to add rows after the last one.")
    if step.like_row > sheet.max_row:
        raise PlanRefused(f"insert_rows on {sheet.title!r}: like_row {step.like_row} is past the sheet's last row ({sheet.max_row}).")
    if sheet._pivots:
        raise PlanRefused(f"{sheet.title!r} holds a pivot table, whose source range this edit cannot move: add the rows below the pivot's source "
                          "another way, or tell the person it needs doing in Excel.")
    if any(isinstance(cell.value, DataTableFormula) for cell in sheet._cells.values()):
        raise PlanRefused(f"{sheet.title!r} holds a what-if data table, which this edit cannot move when rows are inserted.")


def _move_formula(value: Any, sheet: str | None, rows: RowMap) -> Any:
    try:
        return remap_formula(value, sheet, rows)
    except UnmovableReference as failure:
        raise PlanRefused(str(failure)) from failure


def _moved(text: str, sheet: str, rows: RowMap, *, extend: bool) -> str:
    return remap_reference(text, sheet, rows, extend=extend) or text


def _remap_dimensions(sheet: Any, rows: RowMap) -> None:
    held = dict(sheet.row_dimensions.items())
    sheet.row_dimensions.clear()
    for index, dimension in held.items():
        dimension.index = rows.row(sheet.title, index)
        sheet.row_dimensions[dimension.index] = dimension


def _remap_conditional_formats(sheet: Any, rows: RowMap) -> None:
    moved = ConditionalFormattingList()
    for block in sheet.conditional_formatting:
        where = remap_sqref(str(block.sqref), sheet.title, rows, extend=True)
        for rule in block.rules:
            rule.formula = [_move_formula("=" + text, sheet.title, rows)[1:] for text in rule.formula]
            moved.add(where, rule)
    sheet.conditional_formatting = moved


def _remap_validations(sheet: Any, rows: RowMap) -> None:
    for validation in sheet.data_validations.dataValidation:
        validation.sqref = MultiCellRange(remap_sqref(str(validation.sqref), sheet.title, rows, extend=True))
        for name in ("formula1", "formula2"):
            text = getattr(validation, name)
            if text and not text.startswith('"'):
                setattr(validation, name, _move_formula("=" + text, sheet.title, rows)[1:])


def _remap_page_and_view(sheet: Any, rows: RowMap) -> None:
    name = sheet.title
    for table in sheet.tables.values():
        table.ref = _moved(table.ref, name, rows, extend=True)
        if table.autoFilter is not None and table.autoFilter.ref:
            table.autoFilter.ref = _moved(table.autoFilter.ref, name, rows, extend=True)
    if sheet.auto_filter.ref:
        sheet.auto_filter.ref = _moved(sheet.auto_filter.ref, name, rows, extend=True)
    if sheet.print_area:
        sheet.print_area = [_moved(area, name, rows, extend=True).rpartition("!")[2] for area in str(sheet.print_area).split(",")]
    if sheet.print_title_rows:
        sheet.print_title_rows = _moved(sheet.print_title_rows, name, rows, extend=False).replace("$", "")
    if sheet.freeze_panes:
        sheet.freeze_panes = _moved(sheet.freeze_panes, name, rows, extend=False)
    for merged in list(sheet.merged_cells.ranges):
        merged.min_row, merged.max_row = rows.span(name, merged.min_row, merged.max_row, extend=False)
    sheet.merged_cells.ranges = set(sheet.merged_cells.ranges)
    for drawn in (*sheet._images, *sheet._charts):
        anchor = drawn.anchor
        for end in (getattr(anchor, "_from", None), getattr(anchor, "to", None)):
            if end is not None:
                end.row = rows.row(name, end.row + 1) - 1
    for chart in sheet._charts:
        for plot in getattr(chart, "_charts", None) or [chart]:
            for series in plot.series:
                for part in (series.tx, series.cat, series.val, series.xVal, series.yVal):
                    for reference in (getattr(part, "numRef", None), getattr(part, "strRef", None)):
                        if reference is not None and reference.f:
                            reference.f = _move_formula("=" + reference.f, None, rows)[1:]
    for cell in sheet._cells.values():
        if cell.hyperlink is not None:
            cell.hyperlink.ref = cell.coordinate


def _remap_formulas(sheet: Any, rows: RowMap, plain: RowMap, applied: Applied) -> None:
    for cell in sheet._cells.values():
        value = cell.value
        if cell.data_type != "f":
            continue
        if isinstance(value, ArrayFormula):
            value.text = _move_formula(value.text, sheet.title, rows)
            value.ref = remap_reference(value.ref, sheet.title, rows, extend=False)
            continue
        moved = _move_formula(value, sheet.title, rows)
        if moved != value:
            cell.value = moved
            if moved != _move_formula(value, sheet.title, plain):
                applied.extended.append(f"{sheet.title}!{cell.coordinate}: {moved}")


def _move_rows(workbook: Any, plan: Plan, rows: RowMap, applied: Applied) -> None:
    plain = RowMap([replace(item, extend=False) for item in rows.insertions])
    for step in plan.inserts:
        _check_can_move(_sheet(workbook, step.sheet), step)
    for name in {item.sheet for item in rows.insertions}:
        sheet = workbook[name]
        for item in sorted((item for item in rows.insertions if item.sheet == name), key=lambda item: item.before, reverse=True):
            sheet.insert_rows(item.before, item.count)
        _remap_dimensions(sheet, rows)
        _remap_conditional_formats(sheet, rows)
        _remap_validations(sheet, rows)
        _remap_page_and_view(sheet, rows)
    for sheet in workbook.worksheets:
        _remap_formulas(sheet, rows, plain, applied)
        for held in sheet.defined_names.values():
            held.attr_text = _move_formula("=" + (held.attr_text or ""), None, rows)[1:]
    for held in workbook.defined_names.values():
        held.attr_text = _move_formula("=" + (held.attr_text or ""), None, rows)[1:]


def _fill_new_rows(workbook: Any, step: InsertRows, insertion: Insertion, rows: RowMap, plain: RowMap, applied: Applied, base: BaseFont) -> None:
    sheet = workbook[step.sheet]
    first = rows.first_new_row(insertion)
    model = rows.row(step.sheet, step.like_row) if step.like_row else None
    named = {column_index_from_string(column) for row in step.rows for column in row}
    columns = sorted(set(range(1, sheet.max_column + 1)) | named)
    held_height = sheet.row_dimensions[model].height if model and model in sheet.row_dimensions else None
    unfilled: set[int] = set()
    for offset, given in enumerate(step.rows):
        row = first + offset
        if held_height is not None:
            sheet.row_dimensions[row].height = held_height
        for column in columns:
            target = sheet.cell(row, column)
            source = sheet.cell(model, column) if model else None
            if source is not None and not isinstance(source, MergedCell):
                target._style = copy(source._style)
            letter = get_column_letter(column)
            if letter in given:
                value = given[letter]
                if isinstance(value, str) and value.startswith("="):
                    # Written for a row of the workbook as supplied: the references move with it, and "{row}" is this row.
                    value = _move_formula(value.replace("{row}", str(OWN_ROW)), step.sheet, plain).replace(str(OWN_ROW), str(row))
                target.value = _typed(target, value)
                if not target.has_style and target.value is not None:  # no row above to copy a look from, or its cell here had none
                    _in_base_font(target, base)
                applied.formulas_added += formula_text(target.value) is not None
            elif source is not None and formula_text(source.value) is not None and not isinstance(source.value, ArrayFormula):
                target.value = Translator(source.value, origin=source.coordinate).translate_formula(target.coordinate)
                applied.formulas_added += 1
            elif source is not None and source.value not in (None, ""):
                unfilled.add(column)
    applied.inserted.append({"sheet": step.sheet, "first_row": first, "rows": len(step.rows), "copied_from_row": model})
    if unfilled:
        applied.blank[f"{step.sheet} rows {first}-{first + len(step.rows) - 1}"] = ", ".join(get_column_letter(column) for column in sorted(unfilled))


def apply_plan(workbook: Any, plan: Plan) -> Applied:
    """Carry out ``plan`` on ``workbook`` (every address in it as the workbook was supplied) and report what was done."""
    applied = Applied()
    base = base_font(workbook)  # before any step writes, so a step's own cells never decide it
    for step in plan.sets:
        _set(workbook, step, applied, base)
    for step in plan.sheets:
        _add_sheet(workbook, step, applied, base)
    insertions = [Insertion(step.sheet, step.before_row, len(step.rows), step.extend_ranges) for step in plan.inserts]
    applied.rows = rows = RowMap(insertions)
    if insertions:
        _move_rows(workbook, plan, rows, applied)
        plain = RowMap([replace(item, extend=False) for item in insertions])
        for step, insertion in zip(plan.inserts, insertions, strict=True):
            _fill_new_rows(workbook, step, insertion, rows, plain, applied, base)
    return applied
