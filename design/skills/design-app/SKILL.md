---
name: "design-app"
description: "Polished single-file HTML apps and pages for the side pane, design included"
user-invocable: false
metadata:
  outcome: "A polished, substantial single-file HTML app or page for the side pane: designed for its subject, clear hierarchy, light and dark themes, every state, accessible, and honest about its data."
  not-outcomes: |-
    A quick or throwaway app, calculator or widget where no polish was asked for.
    Figures, tables, charts, records or places that Saphion already shows natively.
    Make a Word, PDF, PowerPoint or Excel file.
---
<!-- SURFACE_REASON: procedure prompt asset for the design_app skill, loaded into the model's skill instructions for polished single-file apps -->
# Design an app

You are making a polished single-file HTML app or page that opens in Saphion's side pane: a
calculator, an explorer of figures, a timeline, a dashboard, a briefing page, a small tool. You
make it with `app_change` (`create`). This procedure carries the design and the mechanics of a good
one (section 3 is the look). A quick throwaway app does not need it; a person who asks for something polished, presentable or
substantial does. A dashboard of the Organisation's data is built with the dashboard procedure beside this one: that carries the
data, this carries the page.

An app already made, here or in an earlier chat, is changed in place with `app_change`: `find` it, `read` it, then its `edit` takes `edits` for a small
change and its `rewrite` the whole new `html`. A second copy is never the answer. `read` with view `versions` lists the versions an app keeps and
the `restore` change puts one back. `app_delete` puts an app into the Bin once the person confirms.

After each write the result carries a check report: the app was run as the pane runs it, its
selects and tabs were used once, and what it raised (uncaught errors, console errors) and drew
wrong (NaN or undefined text, blank charts, overlapping or cut-off labels) is listed. Fix what
the report confirms, at most twice, then say what still fails. Never claim the app works beyond
what the report shows. The check has no person to read for, so an app's live sources stay
`loading` in it: it proves the loading state and the controls, not how the figures draw. Say so.

## 1. Decide first

- **Is an app the right thing?** A table, chart, metric, records list, spreadsheet, progress
  visual or set of places on a map already has a native Saphion form: use that, never rebuild it
  in HTML. A dashboard Beacon makes is the exception: Beacon builds apps, not Dashboards, so its
  figures and charts are drawn in the page. A project's programme belongs to the Programme timeline. An app is for bespoke
  interaction: explorers, calculators, simulations, 3D, games, a designed page.
- **Default to business work:** reports, dashboards, explorers of figures, timelines, calculators, site and supplier
  views. Games, simulations and 3D models are fully available whenever the person asks.
- **Who uses it and what do they do first?** Name the one task the opening screen serves, then
  put that task's controls and result where the eye lands first.
- **What data is real?** What the person gave is written into the document. The Organisation's
  records, targets, projects and actions are read live (section 5), never copied in from reads you
  made while building: copies go stale, are cut off where your read was, and show the maker's
  numbers to everyone whatever their own access. Where the person asks for an example, template or demo and gives no records,
  use illustrative data and say plainly, in the app and in your reply, that it is illustrative,
  and never as the Organisation's own.

## 2. Rules for every app

- **A full, self-contained HTML document** that styles itself. The host supplies no stylesheet,
  tokens or controls: every colour, font, control and size is yours. Write it once, complete.
- **Your own tokens.** Declare `:root` custom properties for `--bg`, `--surface`, `--text`,
  `--muted`, `--border`, `--accent` and what else you need, your font stack, and your own
  radii and spacing. Style every control you use, including inputs, selects and buttons.
- **Light and dark.** Define both palettes. The host sets `data-theme="light"` or `"dark"` on the
  root element and changes it live: switch on `:root[data-theme="dark"]`, and on
  `@media (prefers-color-scheme: dark)` for a document with no `data-theme`. A canvas or WebGL
  scene reads its colours from the tokens (`getComputedStyle`) and redraws when the theme
  changes.
- **Fill the pane.** It opens in the side pane: use its full width and height (`min-height:
  100vh`, flexible layout, no fixed outer size) and stay usable as the pane narrows.
- **Accessible.** Semantic HTML (`header`, `main`, headings in order), labels tied to inputs, real
  `<button type="button">`s, visible `:focus-visible`, contrast in both modes, meaning never
  carried by colour alone, and a text summary or table beside any canvas.
- **Meaningful before it runs.** The HTML shows its heading, controls and a status line first and
  the module script wires them up. Wrap setup in try/catch, write failures into the status
  line and also `console.error` them, which is how the check report sees them. Never leave a
  blank frame.
- **Correct.** Check inputs before calculating (finite numbers, domain limits, non-zero
  denominators; HTML `min` and `max` do not validate typed values). Stop on invalid input and say
  why; never leave a stale result shown as current. Keep full precision and format with
  `Intl.NumberFormat` (`en-GB`, `GBP`). State the formula, units and limits. Never `eval` user
  text; render strings with `textContent`, never interpolated HTML.
- **Efficient.** Update an existing chart instead of recreating it on every input, run one
  animation loop and pause it when idle, and prefer SVG or HTML when they say it with less
  machinery.

## 3. Craft for an app

For visual foundations, read the reference this skill's load gave, with `at` set to `references/design_basics.md`. Read the reference when choosing the visual direction;
apply the guidance relevant to this deliverable.

For an app, add the layout to the plan: one sentence on how the eye travels and a rough text sketch of
the main screen, with boldness in one place only. Copy is design: name things as the person would, make a
button say what will happen ("Save changes"), an error say how to fix it and an empty screen what to do
next.

What follows is what an app needs beyond that.

- **Tokens carry the design.** Put the palette, type scale and a spacing scale (4, 8, 12, 16, 24,
  32 px) in your `:root` tokens and use only those. Use tabular figures
  (`font-variant-numeric: tabular-nums`) where numbers line up.
- **Every state.** Define default, hover, active, focus-visible, disabled, loading, empty and
  error for the controls and the result area. One restrained accent; motion has a purpose and
  respects `prefers-reduced-motion`. A game or scene may be as expressive as it needs to be.
- **Responsive.** Lay out with CSS grid or flexbox and `minmax`, `auto-fit` and `clamp()`. Stack
  columns when narrow, allow tables to scroll inside their own container, and give touch targets
  at least 40 px.
- **Data presentation.** Label axes, units and the date of the data. Sort bars. Show the actual
  value on or beside a mark. Use `Chart.js` (`import('chart.js/auto')`) or hand-written SVG for
  charts; `d3` for custom scales and layouts.

## 4. Pitfalls

- A fixed pixel width or height on the outer container, which leaves the pane half empty or
  forces a horizontal scroll.
- Colours copied into a canvas as literals; they will not follow the theme.
- Placeholder text such as "Lorem ipsum", dummy names and unlabelled sample numbers.
- Recreating a chart or scene on every keystroke.
- Anything needing the network beyond Google Fonts: remote scripts, images or APIs. The sandbox
  has none.
- Sound started on load. Browsers keep audio silent until the person first clicks, taps or
  presses a key, so create or resume the `AudioContext` inside that first input handler, and give
  any sound a mute control.

## 5. Live Saphion data

An app that shows the Organisation's own figures declares sources and draws what the host reads for
whoever has it open; the declaration format, the `saphionData` calls and their states are the host
contract in the `app_change` description. Do the reads yourself first, with the `find` or `read` you
would normally use, to learn what comes back; then declare the same call and arguments and design the
drawing from what it returned.

- **Per person.** Each viewer's read uses their access, so two people may see different rows or a
  refusal. Write the app so that is a normal state.
- **Draw every state.** `loading`: a placeholder in the shape of the figure. `refused`, `not_connected`
  or `error`: say `message` where the figure would be; never another number. Empty: say what to do.
  `has_more`: say the figures cover the first rows only; for exact totals or groups declare a count
  read as its own source instead of counting rows in the page.
- **Mark every figure.** Put `data-source` (and `data-field` for the value) on each figure, chart and
  table drawn from a source, so a number can be traced to where it was read. Calculations over `data`
  are yours, in the page, from the source's own values; state the formula.
- **Name everything.** A source reads as whoever opens the app, with no conversation behind it: name
  the Project or class it reads.
- **Data that recurs is the app's own data.** A daily summary or a status you work out is not typed
  into the app or regenerated: `set` entries with `app_data_change` (the same key replaces its entry;
  use the date; `update` sets fields into one) and draw them newest first with their `written_at` as "as of". Design the app once;
  later turns and scheduled runs only write data.

## 6. The person's files

A drawing, photograph or CSV the person attached, or an Organisation file, is used by reference,
declared as the host contract describes; never write its bytes into the document.

- **The viewer's own access.** The file is fetched as whoever opens the app, never your copy: an
  attachment belongs to its uploader, so a colleague gets a refusal. A refused or failed promise
  rejects with the reason; draw it where the file would be (`catch (error) => status.textContent =
  error.message`), never a stand-in picture.
- **Over a picture, draw in the page.** Put the file in an `<img>` or a CSS background and lay
  your own SVG or canvas grid, markers and colour-coding over it, positioned in the picture's own
  proportions so they follow it as the pane resizes. Say what the overlay is (illustrative
  squares, or read from the drawing) and never present a guess about the picture as a fact; look
  at the image first (`read` of the attachment returns it to you).
- **The check run has no person**, so a file stays pending in it: it proves the page around the
  picture and its states, not the picture. Say so.

## 7. Dependencies

The sandbox loads `three`, `d3`, `chart.js/auto` and `gsap` by bare name, and a scene helper
(`saphion/scene3d`), as described with `app_change`. Fonts are the system's or any
Google Fonts family, loaded with a `<link>` and followed by a system fallback in the stack. Nothing
else is available and nothing can be installed. Per-person settings (a best score, a
preference) are kept with `saphionStorage`, never `localStorage`: Saphion keeps them for this person and this app, and
they are always there when the app is open in Saphion. Handle a refused call quietly in code, and in your reply say
only what is kept ("your best score is kept"), never whether storage is available. Say in your reply what the app does and, where its data
is illustrative, that it is.
