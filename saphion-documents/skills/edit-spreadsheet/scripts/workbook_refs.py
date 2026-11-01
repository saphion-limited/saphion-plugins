"""Where a reference lands when rows are inserted: Excel's own rule, applied to every formula, range and name of a workbook.

Excel moves a reference to a row at or below the insertion; a range that spans the insertion grows; a range that ends on the row just above it
is a table's last rows and, for a person adding rows to that table, grows too (a single cell does not). Every reference is moved by its address
text, so the answer does not depend on where the formula sits. ``RowMap`` holds the insertions of a plan once; everything else asks it.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from openpyxl.formula.tokenizer import Token, Tokenizer, TokenizerError

LAST_ROW = 1_048_576
#: Stands for "the new row itself" in a formula typed for new rows. It lies beyond the last row, so no insertion ever moves it.
OWN_ROW = LAST_ROW + 1


class UnmovableReference(ValueError):
    """A reference that cannot be moved by its text (a 3-D range across sheets, a formula that does not parse)."""


@dataclass(frozen=True)
class Insertion:
    sheet: str
    before: int  # the row the new rows go ahead of, as the workbook was supplied
    count: int
    extend: bool  # a range ending on the row above ``before`` grows to take the new rows


class RowMap:
    def __init__(self, insertions: list[Insertion]) -> None:
        self.insertions = insertions
        self._by_sheet: dict[str, list[Insertion]] = defaultdict(list)
        for insertion in insertions:
            self._by_sheet[insertion.sheet].append(insertion)

    def __bool__(self) -> bool:
        return bool(self.insertions)

    def touches(self, sheet: str) -> bool:
        return sheet in self._by_sheet

    def row(self, sheet: str, row: int) -> int:
        """Where the row supplied as ``row`` is now."""
        if row > LAST_ROW:
            return row
        return row + sum(item.count for item in self._by_sheet.get(sheet, ()) if item.before <= row)

    def span(self, sheet: str, first: int, last: int, *, extend: bool) -> tuple[int, int]:
        """Where the rows ``first``..``last`` (a range of at least two rows when it may grow) are now."""
        if last > LAST_ROW:
            return first, last
        grown = sum(item.count for item in self._by_sheet.get(sheet, ()) if extend and item.extend and first < last and item.before == last + 1)
        return self.row(sheet, first), self.row(sheet, last) + grown

    def first_new_row(self, insertion: Insertion) -> int:
        """Where the rows of ``insertion`` begin now."""
        return self.row(insertion.sheet, insertion.before) - insertion.count


_CELL = re.compile(r"^(\$?)([A-Za-z]{1,3})(\$?)(\d+)$")
_ROW = re.compile(r"^(\$?)(\d+)$")
_COLUMN = re.compile(r"^\$?[A-Za-z]{1,3}$")
_QUALIFIED = re.compile(r"^(?:(?P<sheet>'(?:[^']|'')+'|[^'!\[\]:]+)!)?(?P<ref>[^!]+)$")


def _sheet_of(prefix: str | None, own: str | None) -> str | None:
    if prefix is None:
        return own
    return prefix[1:-1].replace("''", "'") if prefix.startswith("'") else prefix


def _with_row(part: re.Match, row: int) -> str:
    """The cell or row reference ``part`` matched, with its row number replaced (its ``$`` marks and column kept)."""
    groups = part.groups()
    return "".join((*groups[:-1], str(row)))


def remap_reference(text: str, own_sheet: str | None, rows: RowMap, *, extend: bool = True) -> str | None:
    """``text`` (``A1``, ``'Cost Plan'!$B$4:$B$20``, ``3:5``) after the insertions. A defined name, a table column, a column range and another
    workbook's cell have no row to move and come back as they are; ``None`` is a text not shaped like a reference at all (a range across
    sheets), which the caller refuses."""
    found = _QUALIFIED.match(text)
    if found is None:
        return None
    sheet = _sheet_of(found.group("sheet"), own_sheet)
    parts = found.group("ref").split(":")
    if sheet is None or len(parts) > 2 or not rows.touches(sheet):
        return text
    cells = [_CELL.match(part) for part in parts]
    only_rows = [_ROW.match(part) for part in parts]
    if all(cells):
        numbers = [int(cell.group(4)) for cell in cells]
        sources = cells
    elif all(only_rows):
        numbers = [int(part.group(2)) for part in only_rows]
        sources = only_rows
    else:
        return text  # a name, a column range (no row moves) or a table column
    if len(parts) == 1:
        moved = [rows.row(sheet, numbers[0])]
    else:
        low, high = sorted(numbers)
        moved = list(rows.span(sheet, low, high, extend=extend))
        moved = moved if numbers[0] <= numbers[1] else moved[::-1]
    prefix = found.group(0)[: len(found.group(0)) - len(found.group("ref"))]
    return prefix + ":".join(_with_row(source, number) for source, number in zip(sources, moved, strict=True))


def remap_formula(formula: str, own_sheet: str | None, rows: RowMap) -> str:
    """A formula (with its leading ``=``) with every reference moved; text that is not a formula, and any formula when nothing moves, is returned as it is."""
    if not rows or not isinstance(formula, str) or not formula.startswith("="):
        return formula
    try:
        tokens = Tokenizer(formula)
    except TokenizerError as failure:
        raise UnmovableReference(f"{formula} is not a formula this edit can read: {failure}") from failure
    for item in tokens.items:
        if item.type != Token.OPERAND or item.subtype != Token.RANGE or item.value.startswith(("[", "'[")):
            continue  # another workbook's cell is that workbook's
        moved = remap_reference(item.value, own_sheet, rows, extend=True)
        if moved is None:
            raise UnmovableReference(f"{formula} holds {item.value}, a reference that cannot be moved (a range across sheets): "
                                     "write the rows into the workbook another way, or leave that formula out of the edit.")
        item.value = moved
    return tokens.render()


def remap_sqref(text: str, own_sheet: str, rows: RowMap, *, extend: bool) -> str:
    """A space-separated list of ranges (a conditional format's, a validation's) after the insertions."""
    return " ".join((remap_reference(part, own_sheet, rows, extend=extend) or part) for part in text.split())
