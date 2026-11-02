"""The edit plan: what the model asks for, checked completely before any workbook is opened.

Every address in a plan is as the workbook was supplied (the cells and rows the model read), never as they will be once rows are inserted:
the edit moves them. A refusal names what is wrong and what to write instead, so the model corrects the plan, never guesses.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from openpyxl.utils.cell import column_index_from_string, coordinate_from_string
from openpyxl.utils.exceptions import CellCoordinatesException

MAX_INSERTED_ROWS = 1_000
MAX_CELL_EDITS = 5_000
SHEET_NAME_FORBIDDEN = re.compile(r"[\[\]:*?/\\]")
OUTPUT_SUFFIX = ".xlsx"


class PlanRefused(ValueError):
    """The plan cannot be carried out; ``str(error)`` says why and what to write instead."""


@dataclass(frozen=True)
class SetCell:
    sheet: str
    cell: str
    value: Any
    confirmed_fixed_value: bool  # the plan names this cell as one the person agreed to turn into a fixed value


@dataclass(frozen=True)
class InsertRows:
    sheet: str
    before_row: int
    like_row: int
    rows: tuple[dict[str, Any], ...]
    extend_ranges: bool


@dataclass(frozen=True)
class NewCell:
    cell: str
    value: Any
    style_from: str | None
    number_format: str | None
    bold: bool | None


@dataclass(frozen=True)
class NewSheet:
    name: str
    position: int | None
    cells: tuple[NewCell, ...]
    column_widths: dict[str, float]


@dataclass(frozen=True)
class Plan:
    output_name: str | None = None
    sets: tuple[SetCell, ...] = ()
    inserts: tuple[InsertRows, ...] = ()
    sheets: tuple[NewSheet, ...] = ()
    accept_losses: frozenset[str] = frozenset()


def _object(value: Any, where: str, allowed: set[str], required: set[str] = frozenset()) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PlanRefused(f"{where} must be an object.")
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise PlanRefused(f"{where} has {', '.join(map(repr, unknown))}, which the plan does not know. It knows: {', '.join(sorted(allowed))}.")
    missing = sorted(required - set(value))
    if missing:
        raise PlanRefused(f"{where} needs {', '.join(missing)}.")
    return value


def _list(value: Any, where: str, limit: int) -> list[Any]:
    if not isinstance(value, list):
        raise PlanRefused(f"{where} must be a list.")
    if len(value) > limit:
        raise PlanRefused(f"{where} holds {len(value)} entries; one run takes at most {limit}. Split the work across runs.")
    return value


def _text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PlanRefused(f"{where} must be text.")
    return value


def cell_address(value: Any, where: str) -> str:
    """A single cell as ``B4`` (upper-cased, no ``$``)."""
    try:
        column, row = coordinate_from_string(_text(value, where).replace("$", "").upper())
        column_index_from_string(column)
    except (CellCoordinatesException, ValueError) as failure:
        raise PlanRefused(f"{where} is {value!r}, which is not a single cell such as B4.") from failure
    return f"{column}{row}"


def column_letters(value: Any, where: str) -> str:
    letters = _text(value, where).upper()
    try:
        column_index_from_string(letters)
    except ValueError as failure:
        raise PlanRefused(f"{where} is {value!r}, which is not a column letter such as B.") from failure
    return letters


def _scalar(value: Any, where: str) -> Any:
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise PlanRefused(f"{where} must be a number, text, true/false, a formula starting with '=', or null; not {type(value).__name__}.")


def _row_number(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise PlanRefused(f"{where} must be a whole row number from 1.")
    return value


def _sets(items: list[Any]) -> tuple[SetCell, ...]:
    made = []
    for number, item in enumerate(items, start=1):
        where = f"set[{number}]"
        item = _object(item, where, {"sheet", "cell", "value", "confirmed_fixed_value"}, {"sheet", "cell", "value"})
        address = cell_address(item["cell"], f"{where}.cell")
        confirmed = "confirmed_fixed_value" in item and cell_address(item["confirmed_fixed_value"], f"{where}.confirmed_fixed_value")
        if confirmed and confirmed != address:
            raise PlanRefused(f"{where}.confirmed_fixed_value names {confirmed}, which is not this entry's cell {address}: it confirms one cell.")
        made.append(SetCell(_text(item["sheet"], f"{where}.sheet"), address, _scalar(item["value"], f"{where}.value"), bool(confirmed)))
    return tuple(made)


def _inserts(items: list[Any]) -> tuple[InsertRows, ...]:
    made, seen, total = [], set(), 0
    for number, item in enumerate(items, start=1):
        where = f"insert_rows[{number}]"
        item = _object(item, where, {"sheet", "before_row", "like_row", "rows", "extend_ranges"}, {"sheet", "before_row", "rows"})
        before = _row_number(item["before_row"], f"{where}.before_row")
        like = _row_number(item["like_row"], f"{where}.like_row") if "like_row" in item else before - 1  # 0: nothing above to copy
        if like >= before:
            raise PlanRefused(f"{where}.like_row is {like}: it must be a row above before_row ({before}), the row whose formats and formulas the new rows copy.")
        rows = []
        for position, row in enumerate(_list(item["rows"], f"{where}.rows", MAX_INSERTED_ROWS), start=1):
            if not isinstance(row, dict):
                raise PlanRefused(f"{where}.rows[{position}] must be an object keyed by column letter, for example {{\"B\": \"Skirting\", \"D\": 12}}.")
            rows.append({column_letters(column, f"{where}.rows[{position}] key"): _scalar(value, f"{where}.rows[{position}].{column}")
                         for column, value in row.items()})
        if not rows:
            raise PlanRefused(f"{where}.rows is empty: name the rows to add.")
        key = (_text(item["sheet"], f"{where}.sheet"), before)
        if key in seen:
            raise PlanRefused(f"{where}: rows are already inserted before row {before} of {key[0]!r}; put all of them in one entry.")
        seen.add(key)
        total += len(rows)
        if total > MAX_INSERTED_ROWS:
            raise PlanRefused(f"The plan inserts more than {MAX_INSERTED_ROWS} rows in all; split the work across runs.")
        made.append(InsertRows(key[0], before, like, tuple(rows), item.get("extend_ranges", True) is not False))
    return tuple(made)


def _sheets(items: list[Any]) -> tuple[NewSheet, ...]:
    made = []
    for number, item in enumerate(items, start=1):
        where = f"add_sheet[{number}]"
        item = _object(item, where, {"name", "position", "cells", "column_widths"}, {"name", "cells"})
        name = _text(item["name"], f"{where}.name")
        if len(name) > 31 or SHEET_NAME_FORBIDDEN.search(name) or name.startswith("'") or name.endswith("'"):
            raise PlanRefused(f"{where}.name {name!r} is not a sheet name: at most 31 characters, none of [ ] : * ? / \\ and no quote at either end.")
        position = item.get("position")
        if position is not None and (isinstance(position, bool) or not isinstance(position, int) or position < 0):
            raise PlanRefused(f"{where}.position must be 0 for first, 1 for second and so on; leave it out to put the sheet last.")
        cells = []
        for index, cell in enumerate(_list(item["cells"], f"{where}.cells", MAX_CELL_EDITS), start=1):
            label = f"{where}.cells[{index}]"
            cell = _object(cell, label, {"cell", "value", "style_from", "number_format", "bold"}, {"cell", "value"})
            style_from = cell.get("style_from")
            if style_from is not None and (not isinstance(style_from, str) or "!" not in style_from):
                raise PlanRefused(f"{label}.style_from must name a cell of the supplied workbook as 'Sheet name'!B4.")
            number_format = cell.get("number_format")
            if number_format is not None and not isinstance(number_format, str):
                raise PlanRefused(f"{label}.number_format must be text such as \"#,##0.00\".")
            bold = cell.get("bold")
            if bold is not None and not isinstance(bold, bool):
                raise PlanRefused(f"{label}.bold must be true or false.")
            cells.append(NewCell(cell_address(cell["cell"], f"{label}.cell"), _scalar(cell["value"], f"{label}.value"), style_from, number_format, bold))
        widths = item.get("column_widths", {})
        if not isinstance(widths, dict):
            raise PlanRefused(f"{where}.column_widths must be an object such as {{\"A\": 30}}.")
        for column, width in widths.items():
            column_letters(column, f"{where}.column_widths key")
            if isinstance(width, bool) or not isinstance(width, (int, float)) or not 0 < width <= 255:
                raise PlanRefused(f"{where}.column_widths.{column} must be a width in characters, up to 255.")
        made.append(NewSheet(name, position, tuple(cells), {column_letters(c, "column"): float(w) for c, w in widths.items()}))
    return tuple(made)


def parse_plan(text: str) -> Plan:
    """The plan in ``text`` (JSON), or the ``PlanRefused`` that says what to correct."""
    try:
        raw = json.loads(text)
    except ValueError as failure:
        raise PlanRefused(f"The plan is not valid JSON: {failure}. Pass one JSON object as the second argument.") from failure
    raw = _object(raw, "The plan", {"output_name", "set", "insert_rows", "add_sheet", "accept_losses"})
    name = raw.get("output_name")
    if name is not None and (not isinstance(name, str) or not name.lower().endswith(OUTPUT_SUFFIX) or "/" in name or "\\" in name):
        raise PlanRefused(f"output_name must be a plain file name ending {OUTPUT_SUFFIX}.")
    accepted = raw.get("accept_losses", [])
    if not isinstance(accepted, list) or not all(isinstance(item, str) for item in accepted):
        raise PlanRefused("accept_losses must be a list of the kinds of content the person agreed to lose, by the names a refusal gave.")
    plan = Plan(name, _sets(_list(raw.get("set", []), "set", MAX_CELL_EDITS)), _inserts(_list(raw.get("insert_rows", []), "insert_rows", 100)),
                _sheets(_list(raw.get("add_sheet", []), "add_sheet", 20)), frozenset(accepted))
    if not (plan.sets or plan.inserts or plan.sheets):
        raise PlanRefused("The plan changes nothing: give at least one of set, insert_rows or add_sheet.")
    return plan
