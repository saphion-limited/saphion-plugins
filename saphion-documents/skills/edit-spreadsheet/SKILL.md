---
name: "edit-spreadsheet"
description: "Change an Excel workbook the person supplied: add rows, change an input or add a summary, with its formulas, formatting and sheets kept"
---
<!-- SURFACE_REASON: procedure prompt asset for the edit_spreadsheet skill, loaded into the model's skill instructions for changing a supplied Excel workbook without losing its formulas -->
# Edit a spreadsheet

The person gave you a working workbook and wants it changed: rows added, an input changed, a summary added. It goes back
looking like their own file with the change made: every formula still a formula and recalculated, every format, named
cell and sheet where it was. You do not rebuild it and you do not re-save it with a program of your own (`file_build`,
`execute_code`): this package's script does the edit and then proves, from the file it wrote, that nothing was lost.

Building a new workbook from nothing is not this procedure's job. A `.xlsm` (macros) or an old `.xls` is not edited here: say so.

## 1. Read before you plan

`read` the workbook (its `continuation_ref` comes with the attachment, or from `find`). Take from it, exactly as printed:

- The sheet names, spelt and cased as they are.
- Where each table starts and ends, and what sits directly under it: a subtotal or totals row, usually a `SUM` over the lines.
- Which cells are inputs (a different font colour or fill, or a label such as "VAT rate") and which hold formulas. A formula
  is never an input.
- Merged ranges: a merged cell takes a value only in its top-left cell.

## 2. Plan the change, then run it once

Run `run_skill_script` with this skill, script `scripts/edit_spreadsheet.py` and two `args`: the workbook's
`continuation_ref`, and the plan as one JSON object (text). The edited workbook arrives as a new file for the person.

**Every address in the plan is as the workbook was supplied.** Do not work out where rows will land: the script moves
every formula, name, rule, validation list, table, chart and print area for you, including what you write in the plan.

```json
{
  "set":         [{"sheet": "Assumptions", "cell": "B3", "value": 0.175}],
  "insert_rows": [{"sheet": "Cost Plan", "before_row": 9,
                   "rows": [{"A": "Ceiling grid", "B": 30, "C": "m2", "D": 22.0}]}],
  "add_sheet":   [{"name": "Summary", "position": 0, "column_widths": {"A": 26, "B": 16},
                   "cells": [{"cell": "A1", "value": "Cost summary", "style_from": "'Cost Plan'!A1"},
                             {"cell": "B3", "value": "='Cost Plan'!E13", "style_from": "'Cost Plan'!E13"}]}]
}
```

- **`set`: change an input.** `sheet`, `cell`, `value`: a number, text, `true`/`false`, `null` to clear, or a formula
  beginning `=`. Text in ISO form (`2026-11-01`) written into a date-formatted cell becomes a real date. A cell that holds a
  formula is refused: a formula is not an input, so change the input it reads. Replacing it with a fixed value stops it calculating,
  which "set it to 20000" does not ask for. Ask in words first, naming the cell and what stops calculating ("E4 calculates
  quantity times rate; setting it to 20000 stops that. Replace it?"), end your reply there, and only after the person's yes put
  `"confirmed_fixed_value": "E4"` (that entry's own cell) on the entry.
- **`insert_rows`: add rows.** `before_row` is the row the new rows go ahead of: the subtotal or totals row under the table,
  or the row after the last used row to add at the bottom. `rows` is a list of objects keyed by column letter. The new rows copy
  their formatting from `like_row` (default: the row above `before_row`, and name another if that row is a heading or total) and
  copy its formulas down, so give only the columns that are inputs. A column you leave out is left as copied (formula) or blank;
  `null` forces blank. A formula you write in `rows` may use `{row}` for its own row: `"=B{row}*D{row}"`.
  A range that ends on the row just above `before_row` (the totals over the table) grows to take the new rows; the report lists
  each one that did, so check every total you expect is there. A total that does not end there needs its own `set`.
- **`add_sheet`: add a summary.** `name` (at most 31 characters), optional `position` (0 first; omit for last), `cells` with
  `cell`, `value` (a formula reads other sheets' cells as supplied) and optional `style_from` (a cell of the supplied workbook
  whose look the cell takes), `number_format`, `bold`; and `column_widths`. Summaries read figures through formulas, never
  retyped numbers.
- `output_name` (ending `.xlsx`) names the new file; the default is the supplied file's name with `-edited` added
  (`Cost plan.xlsx` comes back as `Cost plan-edited.xlsx`), so it never replaces or duplicates the original in the person's files.
- `accept_losses`: see section 4.

Keep to what was asked. A rate, allowance or threshold stays in its input cell and formulas refer to it; never write
`=B5*1.05`. Use functions LibreOffice calculates: `SUMIFS`, `COUNTIFS`, `INDEX`/`MATCH`, `IFERROR`, `SUMPRODUCT`,
`VLOOKUP`; `TEXTJOIN`, `CONCAT`, `IFS`, `SWITCH`, `MAXIFS` and `MINIFS` only as `_xlfn.MAXIFS(...)`; never `XLOOKUP`,
`XMATCH`, `SORT`, `FILTER`, `UNIQUE` or `SEQUENCE`.

## 3. What comes back, and what you check

The script recalculates with LibreOffice, stores the results beside every formula, and reads the delivered file back against
the supplied one: each cell's value, formula and formatting, column widths, row heights, frozen panes and sheet order, and the
count of merges, rules, validation lists, tables, charts, pictures, shapes, comments and names. Charts, pictures, shapes and comments are
not rebuilt: the supplied file's own parts are put back byte for byte (a chart keeps its style, colours and extensions, a note its size),
moved only by the rows that moved. It prints a report: formulas
before and now, errors, the rows inserted (`first_row`, `copied_from_row`), the formulas that now include the new rows, and
any new cell left blank because the row it copied held a value there (fill those with a second plan on the delivered file).

**A clean report proves the formulas calculate and nothing was lost, not that the numbers are right.** An off-by-one range
gives a clean report. `read` the delivered file (its `continuation_ref` is in the result), look at the cells that matter (the
changed input's effects, the totals, the summary), and compare them with figures you work out yourself from the supplied
values. If they differ, correct the plan and run again on the supplied workbook, never on the delivered one.

Tell the person what changed in their terms: which rows now sit where, which input changed and what it did to the totals, what
the summary shows, and anything that was left blank for them.

## 4. When it refuses

It stops and delivers nothing, saying what and where:

- **A plan it cannot carry out**: an unknown sheet, a merged cell, a row past the end, a name the plan does not know. Correct the plan.
- **Errors the supplied workbook did not have** (`#REF!`, `#NAME?`, `#DIV/0!`, `#VALUE!`): a wrong reference, a function the
  engine cannot calculate, text where a number belongs, or a cell that reads another workbook (that file is not here, so it
  cannot be recalculated). Errors the workbook already had are reported, not blamed on the edit.
- **Content it cannot carry through a save**: shapes and text boxes on a sheet that has no chart or picture (on a sheet that has one they
  are carried with it), sparklines, slicers, form controls, newer-Excel conditional
  formats and dropdowns, and pivot tables where rows are inserted. The refusal names each kind. Tell the person what would be lost. Only if they agree to lose a kind, run again with its
  name (as the refusal printed it, for example `"accept_losses": ["shapes"]`). Never add one on your own.
- **A formula count or a cell that differs** from what the plan explains: the file is not delivered.

Limits: one run is stopped after about a minute, recalculation included, so a very large workbook is refused with that reason;
at most 1,000 inserted rows and 5,000 cell edits in one plan. The script cannot open a workbook that is password protected.
