---
name: "dataviz"
description: "Build a dashboard as an app: work out its figures in code, then publish one app that draws them"
user-invocable: false
metadata:
  outcome: "A dashboard the person asked for, made as one app: its figures worked out in code from the Organisation's real data, checked, drawn honestly (labelled, dated, every state) and kept live or written as the app's own data."
  not-outcomes: |-
    Open, change or arrange a Dashboard the person already has: that is theirs to do in the Dashboard itself; Beacon finds and reads one but never changes it.
    A single figure, table or chart that belongs in the reply: say it, or use the chart card.
    A designed page, calculator or explorer with no Organisation data.
    A Word, PDF, PowerPoint or Excel file.
---
<!-- SURFACE_REASON: procedure prompt asset for the dataviz skill, loaded into the model's skill instructions as the procedure for a dashboard made as an app -->
# Build a dashboard as an app

Beacon builds apps, not Dashboards. The Dashboard product is a place people build by hand (New, then Dashboard); Beacon can
`find` and `read` one but has no way to make or change one. A person who asks you for a dashboard, a scorecard or "a view of the
numbers" gets an app, made once and kept. Say that in one plain line the first time ("I'll build it as an app"), and never call
the result a Dashboard. The app tool's description carries the sandbox and the live-data contract; this procedure carries the data
and the dashboard craft, and the app design rules carry the page.

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
  `app_data_write` (one entry per day, the date as the key) and draw it newest first with its `written_at` as "as of". A later turn
  or a scheduled run writes the next entry; the app is not rebuilt.
- Never mix them silently: each figure says whether it is live or as of a date.

## 4. Draw it as a dashboard, not a poster

The page itself (tokens, light and dark, every state, accessibility, the sandbox) follows the app design rules the app tool points to,
loaded beside this procedure; this is what a dashboard adds.

- The one number that matters first and largest, with its period and a comparison (last period, a target). Then the supporting
  figures, then the table behind them.
- A chart for a pattern, a number for a total, a table for lookup. Bars sorted, one baseline at zero, the value on or beside each
  mark, units and period on every axis. No 3D, no second y-axis; the same colour means the same thing everywhere.
- Any in-page control (a period, a group) filters what the page already holds; it does not read again.
- Mark every figure with `data-source` and `data-field` where it comes from a source, so a number can be traced; a refused or failed
  source says why where the figure would be.

## 5. Publish once

Make it with `generateSandboxedUi`. To change an app already made (here or in an earlier chat: `find` it, then `read` it), use
`app_edit` or pass `replaces` for a rewrite; never make a second copy. After each write, fix what the check report confirms, at
most twice, then say what still fails; the check has no person to read for, so it proves the controls and the loading state, not
how the live figures draw. Say so.

In your reply say what the dashboard answers, which figures are live and which are as of a date, what each includes, and link it.
