"""Change a supplied Excel workbook and deliver it with its formulas, formatting and sheets intact, recalculated.

    edit_spreadsheet.py WORKBOOK.xlsx 'PLAN JSON'

``WORKBOOK`` is the supplied file (name it by its issued reference; it arrives as a path). The plan (``workbook_plan``) says what to change in
terms of the workbook as supplied. The workbook is edited with openpyxl (``workbook_edits``), saved, recalculated by the sandbox's own
``recalc`` check (LibreOffice calculates, and its results are stored in this file's formulas as their cached values, nothing else is rewritten),
and read back (``workbook_audit``) against the supplied one. The edited workbook is written to ``$SKILL_OUTPUT_DIR`` only when that proves
it faithful; otherwise the run stops with what differs and nothing is delivered. The one line printed is the report the model reads.

Libraries, each checked against its own licence (S10b of the skill-packages plan, 1 Nov 2026): openpyxl 3.1.5 (MIT) edits the package; lxml 6.1.3
(BSD-3-Clause) reads the package parts for the audit; both are the sandbox image's own pinned requirements, nothing is added. LibreOffice 7.4
(MPL-2.0, unmodified Debian build already in the image) calculates, run as its own process by the sandbox's ``recalc`` check, never linked or
copied. Anthropic's professional xlsx skill is proprietary; it was studied for what an edit must achieve (formulas kept, recalculated, errors
looked for) and none of its text or code is used here.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import openpyxl
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from workbook_audit import (
    KINDS,
    AuditFailed,
    compare_cells,
    errors_in,
    inventory,
    losses,
)
from workbook_edits import apply_plan, formula_text
from workbook_parts import PartsUnmovable, restore_parts
from workbook_plan import PlanRefused, parse_plan

#: The sandbox's own recalculation (``docker/file-sandbox/checks/recalc``): there is one, and this uses it.
RECALC = "/opt/checks/recalc"
RECALC_SECONDS = 55
LISTED = 8


def _load(path: Path, *, values: bool = False):
    return openpyxl.load_workbook(path, data_only=values, rich_text=True)


def recalculate(path: Path) -> dict:
    """LibreOffice calculates the workbook and its results are stored in ``path`` beside each formula; the check's own report, as it printed it."""
    if not Path(RECALC).is_file():
        raise AuditFailed(f"This sandbox has no recalculation step ({RECALC}), so the formulas cannot be recalculated and nothing was delivered.")
    try:
        done = subprocess.run([sys.executable, RECALC, str(path)], capture_output=True, text=True, timeout=RECALC_SECONDS, stdin=subprocess.DEVNULL, check=False)
    except subprocess.TimeoutExpired as failure:
        raise AuditFailed(f"Recalculating took longer than {RECALC_SECONDS} seconds (the workbook is too large for one run).") from failure
    lines = [line for line in done.stdout.splitlines() if line.strip()]
    if done.returncode != 0 or not lines:
        raise AuditFailed(f"The recalculation did not run: {(done.stderr or done.stdout).strip()[-600:]}")
    return json.loads(lines[-1])


def _listed(items: list[str]) -> str:
    return "; ".join(items[:LISTED]) + (f"; and {len(items) - LISTED} more" if len(items) > LISTED else "")


def run(source: Path, plan_text: str) -> dict:
    plan = parse_plan(plan_text)
    if source.suffix.lower() != ".xlsx":
        raise PlanRefused(f"{source.name} is not an .xlsx workbook. Only .xlsx can be edited here (a .xlsm would lose its macros and a .xls cannot be opened).")
    if (unknown := sorted(plan.accept_losses - set(KINDS))):
        raise PlanRefused(f"accept_losses names {', '.join(map(repr, unknown))}, which is not a kind of content. The kinds: {', '.join(KINDS)}.")
    try:
        before = inventory(source.read_bytes())
        workbook = _load(source)
    except (zipfile.BadZipFile, KeyError, etree.XMLSyntaxError, OSError, ValueError) as failure:
        raise PlanRefused(f"{source.name} cannot be opened as a workbook: {failure}") from failure
    applied = apply_plan(workbook, plan)
    staged = Path(tempfile.mkdtemp()) / (plan.output_name or source.name)  # the supplied file's own name is a new version of it; another name is a new file
    workbook.save(staged)
    workbook.close()
    del workbook
    recalc = recalculate(staged)
    try:
        delivered, kept = restore_parts(source.read_bytes(), staged.read_bytes(), applied.rows)
    except PartsUnmovable as failure:
        raise AuditFailed(f"{failure}. The edited workbook was not delivered.") from failure
    staged.write_bytes(delivered)
    after = inventory(delivered)

    problems: list[str] = []
    refused, accepted = losses(before, after, plan.accept_losses)
    if refused:
        problems.append("The edit would lose content the workbook has and this edit cannot carry: " + _listed(refused)
                        + ". If the person agrees to lose a kind, say so and name it in accept_losses; otherwise do not edit this workbook here.")
    formulas_before = sum(count for (_, kind), count in before.items() if kind == "formulas")
    formulas_after = sum(count for (_, kind), count in after.items() if kind == "formulas")
    expected = formulas_before - len(applied.overwritten) + applied.formulas_added
    if formulas_after != expected:
        problems.append(f"The workbook holds {formulas_after} formulas where {expected} were expected ({formulas_before} supplied, "
                        f"{len(applied.overwritten)} replaced by a value, {applied.formulas_added} written): formulas were lost or altered.")
    original, edited = _load(source), _load(staged)
    differences = compare_cells(original, edited, applied)
    if differences:
        problems.append("What the person had no longer matches: " + _listed(differences))
    original_errors = {(sheet, applied.rows.row(sheet, row), column): value for (sheet, row, column), value in errors_in(_load(source, values=True)).items()}
    values = _load(staged, values=True)
    now_errors = errors_in(values)
    new_errors = [f"{sheet}!{openpyxl.utils.get_column_letter(column)}{row} shows {value} (formula {formula_text(edited[sheet].cell(row, column).value)})"
                  for (sheet, row, column), value in now_errors.items() if (sheet, row, column) not in original_errors]
    if new_errors:
        problems.append("Recalculation leaves errors the supplied workbook did not have: " + _listed(new_errors)
                        + ". Correct the plan (a wrong reference, a function this engine cannot calculate, text where a number belongs).")
    if problems:
        raise AuditFailed("\n".join(problems) + "\nThe edited workbook was not delivered.")
    empty = sum(1 for sheet in values.worksheets for cell in sheet._cells.values() if cell.value is None and
                formula_text(edited[sheet.title].cell(cell.row, cell.column).value) is not None)

    output = Path(os.environ["SKILL_OUTPUT_DIR"]) / staged.name
    output.write_bytes(delivered)
    report = {
        "delivered": staged.name,
        "formulas": {"supplied": formulas_before, "now": formulas_after, "replaced_by_a_value": len(applied.overwritten), "calculated_to_nothing": empty},
        "recalculated": {"engine": "LibreOffice", "errors_now": len(now_errors), "errors_supplied_with": len(original_errors),
                         "formulas_checked": recalc.get("formulas")},
        "checked_against_the_supplied_workbook": "values, formulas, formatting, widths, heights, panes, sheet order and the count of every kind of content",
        "cells_set": len(plan.sets), "rows_inserted": applied.inserted, "sheets_added": applied.sheets_added,
    }
    if kept:
        report["kept_exactly_as_supplied"] = kept
    if applied.extended:
        report["formulas_now_including_the_new_rows"] = applied.extended[:LISTED]
        if len(applied.extended) > LISTED:
            report["formulas_now_including_the_new_rows_more"] = len(applied.extended) - LISTED
    if applied.blank:
        report["new_cells_left_blank_because_the_copied_row_held_a_value"] = applied.blank
    if accepted:
        report["losses_the_person_accepted"] = accepted
    return report


def main(argv: list[str]) -> None:
    if len(argv) != 3:
        sys.exit("Usage: edit_spreadsheet.py WORKBOOK.xlsx 'PLAN JSON': the workbook, then one JSON plan.")
    try:
        report = run(Path(argv[1]), argv[2])
    except (PlanRefused, AuditFailed) as refusal:
        sys.exit(str(refusal))
    sys.stdout.write(json.dumps(report, separators=(",", ":"), default=str) + "\n")


if __name__ == "__main__":
    main(sys.argv)
