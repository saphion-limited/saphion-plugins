---
name: "dataviz"
description: "Build a dashboard as an app, only when the person asks for an app or the data is not Saphion's: work out its figures in code, then publish one app that draws them"
user-invocable: false
metadata:
  outcome: "A dashboard made as an app because the person asked for an app or its data is not Saphion's: figures worked out in code, checked, drawn honestly, kept live or written as the app's own data."
  not-outcomes: |-
    A dashboard, scorecard, KPI page or chart over Saphion's own data (Projects, Actions, records, Boards): a Saphion Dashboard made with `dashboard_change`, or a widget in the Document the person is in made with `document_change`'s `card`. Not an app.
    Open, change or arrange a Dashboard the person already has: `dashboard_change`.
    A single figure, table or chart for the reply: say it, or use a chart or table widget.
    A designed app, page or calculator with no Organisation data.
    A Word, PDF, PowerPoint or Excel file.
---
<!-- SURFACE_REASON: procedure prompt asset for the dataviz skill, loaded into the model's skill instructions as the procedure for a dashboard made as an app -->
# Build a dashboard as an app

A dashboard, scorecard, KPI page or chart over Saphion's own data is a Saphion Dashboard: make or change it with `dashboard_change`
(read `dashboard_guide` first; it holds the craft), or, when the person is in a Document, add a widget to that Document with
`document_change`'s `card`. Beacon reads one with `read`. This procedure is only for a dashboard made as an app: the person explicitly
asked for an app, or the data is not Saphion's (figures or a file they gave you). If neither is so, stop here and make the Dashboard.
Say it in one plain line the first time ("I'll build it as an app"), and never call the app a Dashboard. The app tool's description carries the sandbox and the live-data contract; the app design rules carry the page
(tokens, states, controls); this procedure carries the data and the chart craft. Its files are read on demand: `read` the reference this skill's load gave, with `at` set to
`references/<name>.md`: `palette.md` is needed by every build; the others are named at the step
that uses them.

## 1. Decide what it answers

Name the one question the dashboard serves, who reads it and over what period; choose three to six figures that answer it, one of
them first. If the Organisation already has a Dashboard on this subject, `find` it (kind dashboard) and `read` it: its widgets
show which Boards and measures the Organisation already trusts, so build over the same ones and never copy figures out of it. If
the question is open (a different dashboard would answer a different question), ask one short question first.

## 2. Learn the data, then compute it in code

- `find` and `read` the Boards and record classes the figures come from, and read a few rows, so you know the fields and what an
  empty value means.
- Work every figure out with `execute_code`, as one program over all the data: counts, totals, groups, joins across classes,
  trends, percentages. Never add up rows you read by hand, never estimate, never take a count from one page of a list.
- Check before you draw: a count by group adds to the total, the total is what the Board shows, a ratio's denominator is not zero.
  Print the finished figures; those printed values are what the app draws.
- Say what each figure includes and excludes (archived, closed, the period) in the app, from the program, not from memory.

## 3. Keep it current or write it down

- **Live.** Where the Saphion read can give the figure as it stands, declare it as a live source (the app tool's host contract):
  every viewer sees their own access, so a refusal is a normal state, and the figure is never typed into the page. Use this for lists, simple counts and anything
  a person should see change when they open it.
- **Written.** Where it takes code (a join, a ratio, a trend), run the program now and write the result as the app's own data with
  `app_data_change` (`set` one entry per day, the date as the key) and draw it newest first with its `written_at` as "as of". A later turn
  or a scheduled run writes the next entry; the app is not rebuilt.
- Never mix them silently: each figure says whether it is live or as of a date.

## 4. Choose the form of each figure

Decide the form before any colour (`references/choosing-a-form.md`). It is sometimes not a chart.

- One value, with its change: a stat tile. A few headline values: a row of tiles. The number the page leads with: the hero figure, one only.
- One amount against a limit: a meter. A lookup, or more than seven classes that all matter: a table.
- Otherwise the job picks the form: compare amounts (bars, sequential colour); a change over time (line); tell series apart (grouped or
  stacked bars, categorical colour); one series is the story (emphasis: it in the accent, the rest grey); above or below a baseline
  (diverging); parts of a whole (one stacked bar).
- Nominal bars are one colour. Ordered categories (stages, tiers) are ordinal and take one hue in steps. A one-bar bar chart and a two-slice
  pie are a stat tile.

## 5. Colour by job, then validate it

Colour has five jobs: categorical (which series), ordinal, sequential (how much), diverging (which side of a baseline) and status
(a state). Read `references/color-formula.md` for the method and `references/palette.md` for Saphion's values: tokens only, never a hex of
your own.

- Series take the palette's slots in order from slot 1, and keep their slot as filters change. Seven is the ceiling; past it fold into
  "Other", draw small charts or a table. A chart where any two marks touch (scatter, bubble, map, small charts) carries at most three.
- Status colours mean a state and nothing else, always beside an icon and a word. A chart that has status keeps the amber, green and orange
  slots out of its series.
- Validate the colours you assigned, in both modes, before you write the page: from `execute_code` call
  `skill_script(skill="dataviz", script="scripts/validate_palette.py", args=[<colours in slot order>, "--mode", "light"])` and again with
  `"dark"` (add `"--pairs", "all"` for an all-pairs chart; `"--kind", "ordinal"` or `"sequential"` for a ramp). It prints each check and a
  verdict last. A FAIL means change the colours, the series count or the form, and run it again; never ship a failed set. A WARN is allowed
  only with a second channel (direct labels or the table view), and your reply says which.

## 6. Mark specs, labels and the hover layer

Draw to the specs in the parameter table below and `references/marks-and-anatomy.md`: thin marks with a 2px gap of surface colour between
them, hairline solid gridlines, one baseline at zero for bars, labels only where they earn it (the end, the extreme, the story), text in
ink tokens and never in a series colour. Two or more series have a legend. A label that does not fit inside a mark goes outside its end or
into the tooltip; never clip it.

Every chart gets a hover layer (`references/interaction.md`): a crosshair that snaps to the X on lines and areas, each mark its own target
on bars and cells with a lift, one tooltip listing every series with the value first, line keys, a 24px target for small dots. Series and
category names are data: put them in with `textContent`. Any in-page control (a period, a group) sits in one row above the charts and
filters what the page already holds; it does not read again, and while live data refreshes the last drawing stays in place, dimmed.

## 7. The accessibility pass

Four checks, each a step of its own (`references/components.md`, `references/anti-patterns.md`):

1. **Legend** for two or more series, so identity never rests on colour matching alone.
2. **Table view**: every chart has a toggle to a real `<table>` built from the same array the chart draws; nothing a tooltip shows is
   reachable only by hover.
3. **Dark mode** is a step, not a side effect: both palettes defined as in `palette.md`, marks and ink read from the tokens, a canvas redrawn on
   the theme change, and the validator run for dark as well as light.
4. **Texture** (a 45 or 135 degree hatch) only behind an accessibility control, for print or in forced colours; never by default.

Read the page once more against `references/anti-patterns.md` before it is written; a chart that matches an entry is wrong.

## 8. Publish once, then check

Make it with `app_change` (`create`). To change an app already made (here or in an earlier chat: `find` it, then `read` it), use
`app_change` (`edit` with `edits`, or `rewrite` with the whole `html`); never make a second copy. Mark every figure with `data-source` and `data-field` where it comes from
a source, so a number can be traced; a refused or failed source says why where the figure would be.

After each write, the result carries the app tool's check report: the app run once, headless, in the light theme at the pane's width, its
controls tried once, listing what it raised (uncaught errors, console errors) and drew wrong (invalid text such as NaN, a chart that drew
nothing, labels overlapping or cut off). Fix what the report confirms, at most twice, then say what still fails. That report is the only look
you get: it is words, not a picture, it does not run dark, and its live sources stay `loading` (there is no person), so it proves the controls,
the loading state and the page's structure, not how the live figures or the colours draw. Colour and dark mode rest on the validator and the
tokens. Say so, and never claim more than the report shows.

## Non-negotiables

- One y-axis. Two scales on one plot suggest a link between the series: draw two charts, or index both to 100 on one axis.
- Colour follows the entity: a series keeps its colour when others are filtered out.
- Never a rainbow, never a ramp on nominal categories, never a hue past the palette's seven.
- Status colours are reserved for a state, with an icon and a word.
- Text is in ink tokens; a series colour is for marks only (the one exception is the label inside a fill, `palette.md`).
- Bars start at zero. Value on or beside the mark where it fits, units and period on every axis, bars sorted.
- Tokens only from `palette.md`; the validator run on the colours you assigned, both modes.
- Every chart has a hover layer and a table view.
- No 3D, no gradient, no shadow on a mark.

## Parameters (Saphion's values; the files give the reasons)

| Parameter | Light | Dark |
|---|---|---|
| Page, chart surface | `#ffffff`, `#ffffff` | `#1a1a19`, `#1d1d1c` |
| Ink, secondary, muted | `#1d1c1a`, `#57544e`, `#6b6760` | `#eceae5`, `#b5b2ab`, `#9a968f` |
| Gridline, axis | `#e9e7e2`, `#dad7d0` | `#2c2b29`, `#3a3936` |
| Series order | indigo, rose, amber, blue, green, violet, orange | the same hues, lighter set |
| Lightness band (OKLCH L) | 0.43 to 0.77 | 0.60 to 0.80 |
| Chroma floor | 0.10 | 0.10 |
| Colour-blind separation (neighbours) | 8 target, 6 floor (floor needs a second channel) | same |
| Normal-vision separation (worst pair) | 15 | 15 |
| Contrast, marks and text | 3:1 marks (under it needs labels or a table), 4.5:1 text | same |

| Mark | Spec |
|---|---|
| Bar, column | 24px thick at most, 4px rounded at the data end, square at the baseline |
| Line, dot | 2px line with round joins; dots 8px or more with a 2px surface ring |
| Area | the series colour at about 10% |
| Gap between touching marks | 2px of surface colour, one width throughout |
| Gridlines, axes | 1px, solid, one step off the surface |
| Hit target | at least 24px around any small mark |
| Hero figure | 48px or more, the page's sans, proportional figures; tabular only in table columns |
| Type | Geist from Google Fonts, then the system sans |

## Your reply

Say what the dashboard answers, which figures are live and which are as of a date, what each includes, what the validator said about the
colours (and any second channel a WARN needed), what the check report did and did not prove, and link it.
