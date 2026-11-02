---
name: "make-spreadsheet"
description: "Excel workbooks with live formulas"
metadata:
  outcome: "A new Excel workbook (.xlsx) built for the person: tidy sheets, real formulas for totals and derived values, formatted headers and numbers, and no formula errors."
  not-outcomes: |-
    Read, check or summarise a spreadsheet the person supplied.
    Show figures, a table or a chart in the conversation rather than as a file.
    Make a CSV or plain text file.
  hand-over-edit-spreadsheet: "Change a workbook the person supplied: add rows, change an input or add a summary while keeping its formulas and layout."
---
<!-- SURFACE_REASON: procedure prompt asset for the make_spreadsheet skill, loaded into the model's skill instructions for building Excel workbooks -->
# Make a spreadsheet

You are building an Excel workbook the person will open, check and probably send on. It must
look like one a careful colleague built by hand: live formulas, tidy sheets, and no error
values. You build it by writing a program and running it with `file_build`, then
you prove it with the `recalc` check before the person hears it is ready.

`recalc` rewrites the workbook after your program finishes. To bundle it in a ZIP, first deliver the checked workbook, then pass that saved file into a second build as an input and archive its final bytes. A ZIP made in the first program contains the pre-check workbook.

Call `file_build` with exactly these fields: `program`, `language` (`python` or `node`), `outputs` (a list of file names, ending `.xlsx`), `title`, `checks`, `description`, `inputs` (the person's own files the program opens) and, to change a file you already made, `replaces_file_id`. Call `file_build` directly as its own tool. Never call it from inside `execute_code`: it is not available there.

## 1. What the program can reach

- A run delivers up to **16 files**, each as its own card. A replacement declares exactly one output. No network and no installs. A program is stopped after about a minute.
- The input files are the current version of the file named by `replaces_file_id` (under its own
  name) and every file you name in `inputs`: a CSV, a workbook or a picture the person attached, or an
  Organisation file, each by the reference you were shown it under (an attachment's `source_ref`, or
  `organisation-file:<id>@<hash>`). Each is placed in the working directory under its own name made
  safe (or the `name` you give) and the result lists the names: open it there
  (`openpyxl.load_workbook`, `pandas.read_csv`), never write its data into the program. At most 15 MB
  each; a file you cannot read here refuses the run, naming it.
- Python has `openpyxl` (default), `xlsxwriter`, `pandas` and `matplotlib`; the spreadsheet engine is
  LibreOffice.

| Job | Use |
|---|---|
| New workbook | `openpyxl`; `pandas` to shape bulk data before writing it |
| Change a workbook you made | Pass its `file_id` as `replaces_file_id`: same file, new version. Open it with `openpyxl.load_workbook`, change it, save the same kind. Never rebuild from nothing or make a second copy. |

Give `file_build` the program, the output names, `checks: ["recalc"]` and a one-line
`description` of what the workbook is for.

## 2. Rules for every workbook

- **Follow the spec literally.** Exact sheet names, exact column headings and the calculation the
  person described. A tidier design that computes something else is wrong.
- **Formulas, not pasted results.** Every total, subtotal, percentage, variance and other
  derived value is a formula that points at the cells it comes from (`=SUM(D5:D20)`,
  `=D21/D$30`). Only genuine inputs are constants. Never compute a number in Python and write the
  answer into a cell. Make a formula the same all the way across a row or down a column: one cell
  that differs is the commonest silent error.
- **No numbers buried in formulas.** A rate, allowance or threshold (VAT, contingency, retention) sits
  in a labelled input cell and formulas refer to it, so `=B5*(1+$B$6)`, never `=B5*1.05`.
- **Document every assumption.** Mark estimates and assumptions in a notes column or an Assumptions
  sheet, and name the source of any figure that came from somewhere. Where the person gave no figure,
  leave a labelled blank input and say so in your reply.
- **A workbook the person will fill in** has a short legend saying which cells to edit, input cells
  filled with one light colour, and one example row of realistic values showing the format (never add
  an example row to a workbook you were asked to change).
- **One header row per table**, bold, with a fill and a bottom border, text wrapped.
- **Set column widths** to fit their content (about 1.2 times the longest value, capped at 60).
- **Number formats do the presentation**; the cell keeps the real number. Money `"£#,##0.00"` (whole
  pounds `"£#,##0"`), negatives in brackets `"£#,##0;(£#,##0)"`, percentages `"0.0%"` with the value held
  as a fraction, dates `"dd/mm/yyyy"`, counts `"#,##0"`. Name the unit in the header (`Cost (£)`).
  Years that label columns are text.
- **Real dates** are `datetime.date` values, never text. **Real numbers** are numbers, never `"1,200"`.
- **One font** (Calibri or Arial), size 10 or 11. Colour sparingly: one header colour, one light fill
  for inputs, red only for problems. In a model, inputs are blue text, formulas black and links to
  another sheet green.
- **Name the sheets** for what they hold ("Cost Plan", "Summary", "Assumptions"): at most 31
  characters, none containing `[ ] : * ? / \`. Summary or assumptions first when there is one.
- **Ready to send:** set orientation and fit-to-one-page-wide for any sheet people will print, repeat the
  header row on each printed page (`ws.print_title_rows`), and set the workbook title and author in its
  properties.

## 3. Choose functions the engine can calculate

The checks calculate with LibreOffice, and a function it cannot evaluate becomes `#NAME?` stored in
the file you deliver.

- Prefer the functions every Excel has had since 2007: `SUMIFS`, `COUNTIFS`, `INDEX`, `MATCH`,
  `IFERROR`, `SUMPRODUCT`, `VLOOKUP`.
- `TEXTJOIN`, `CONCAT`, `IFS`, `SWITCH`, `MAXIFS` and `MINIFS` work only when written with the
  `_xlfn.` prefix (`=_xlfn.MAXIFS(...)`), because openpyxl stores the text exactly as given.
- Do **not** use `XLOOKUP`, `XMATCH`, `SORT`, `FILTER`, `UNIQUE` or `SEQUENCE`. Use `INDEX`/`MATCH` for
  lookups, and sort, filter and de-duplicate in Python before writing the cells.
- A formula LibreOffice could not parse comes back lower-cased: a quick sign beside a `#NAME?`.

## 4. The recalc check (mandatory whenever the workbook has a formula)

`openpyxl` writes formulas but never calculates them, so a file saved straight from it has no stored
results and a viewer that does not recalculate shows empty cells. The `recalc` check opens the
workbook in LibreOffice, calculates every formula, **stores the results in your file**, and
reports `ok`, the number of formulas, and each error cell (`#REF!`, `#DIV/0!`, `#NAME?`, `#VALUE!`,
`#N/A`, `#NUM!`) with its sheet and address, up to a limit with `errors_truncated`.

1. Always pass `checks: ["recalc"]`. Do not skip it because the formulas look simple.
2. Read the report. Any listed error is a defect in your program. Fix the cause (a wrong reference, a
   divide by an empty cell, a misspelt function, text where a number belongs, an unsupported
   function) and run again until `total_errors` is zero. Never hide an error with `IFERROR` unless a
   blank is the correct answer for that cell.
3. **The report proves the formulas evaluate, not that they are right.** An off-by-one range gives a
   clean report and wrong figures, and the report does not show values. For every workbook whose
   figures matter, make a second run on the delivered file (`replaces_file_id`): open it with
   `openpyxl.load_workbook(..., data_only=True)`, print the key cells (totals, a percentage that
   should be near 100, a count you can add up yourself), and compare them with figures you work out
   independently. Fix and run again if they differ.
4. `data_only=True` on a file you have just written returns `None` everywhere, and saving a workbook
   opened with `data_only=True` replaces every formula with its value for good. Use it only to read.
5. The recalc check changes nothing but the stored results: formulas, formats, widths, frozen panes,
   filters, tables, validation, conditional formats, charts and defined names stay as you wrote them.
6. The file from the last clean run is the one the person receives.

## 5. openpyxl traps

- Formulas are strings starting `=`, with English function names and commas between arguments. A sheet
  name with a space is quoted: `='Cost Plan'!F42`; unquoted it gives `#VALUE!`. Cross-sheet references
  must name a sheet that exists, spelt exactly.
- Row and column numbers move. Build ranges from variables (`first_row`, `last_row`) and write the
  totals row once you know the last row.
- Merged cells keep only the top-left value and break sorting and filtering; write to the anchor only.
  Merge a title across a sheet and nothing else; use centre-across-selection for the rest.
- Dates: assign a `date`, then set `number_format`. Do date arithmetic in formulas (`=E5-D5`) and format a
  duration cell as a number.
- Percentages: store 0.2 and format `0%`; never store 20 beside a percent format.
- `SUM` over a range that includes its own header or subtotal rows double counts. Sum the section's
  lines, or use `SUBTOTAL(9, ...)` where filters apply. Guard a ratio whose denominator can be zero or
  blank with `IF(x=0, "", ...)`.
- An Excel table (`ws.add_table`) and a dropdown (`DataValidation`) make a register easier to use; a
  table has one header row and no merged cells. A chart (`openpyxl.chart`) refers to cell ranges, is
  built after the data and is placed clear of the cells.
- Keep a formula's result type honest: a formula whose result is `""` reads back as `None`.

## 6. Changing a workbook you made

- Find its input cells first (a distinct font colour, fill or label) and write only there. Leave existing
  formulas, formats and sheet names alone.
- Opening and saving drops the stored results, so the `recalc` check is needed again after every change.
- Print the sheet names, table names and chart count before and after the change, and compare.

## 6b. A workbook the person supplied
<!-- TEMPORARY BRIDGE [skill_packages]: this section is deleted when skill_packages is released (S11); the edit procedures replace it -->

This applies to a workbook the person attached or you found with `find`: a file Beacon did not make.
When you have a procedure for changing a supplied workbook, it does that work and this section is not used.

- An attachment: name it in `inputs` and save the changed workbook as a new `.xlsx`. A file you found with `find`:
  pass it as `replaces_file_id` (same file, new version). Open it with `openpyxl.load_workbook`, find its input
  cells first (a distinct font colour, fill or label) and write only there. Leave existing formulas, formats and
  sheet names alone; the workbook's own conventions outrank this procedure.
- Saving drops the stored results, so the `recalc` check is needed on it.

## 7. Conventions for construction work

- **Cost plans and estimates:** one line per element, with quantity, unit, rate and amount
  (`=quantity*rate`), grouped under section headings with a subtotal per section. After the sections come,
  in order, preliminaries, overheads and profit, contingency, a total before VAT, VAT as its own line, and
  a total including VAT.
- **Valuations and payment applications:** previous, this period and cumulative columns, retention as a
  percentage input, and a net-due line.
- **Registers (risk, action, issues, drawings, RFI, snagging):** one record per row with an ID,
  description, owner, status, date raised and due date; filters on the header; no blank rows and no
  totals rows inside it. Counts go on a separate Summary sheet using `COUNTIF`.
- **Programmes and schedules:** start, finish and duration columns, duration a formula, dates `dd/mm/yyyy`.
- **Totals rows:** labelled "Total", bold, with a top border, directly under the data they sum and outside
  any filtered table.
- **Summary sheet:** headline figures as formulas reading from the detail sheets, nothing retyped.

State in your reply what the workbook contains, the sheet names, the assumptions you made, and what you
checked the figures against.
