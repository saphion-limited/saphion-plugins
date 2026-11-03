<!-- SURFACE_REASON: the hover layer and in-page filter rules of the dataviz skill, loaded on demand when an app draws a chart -->
# Interaction: the hover layer and filters

A chart in an app responds by default. The hover layer is part of the deliverable, and leaving it out is the exception (a bare stat tile),
never the default. Design it as carefully as the still picture.

## Tooltips and hover

A tooltip adds; it never gates. Every value it shows is also reachable without it, through a direct label or the table view, and keyboard
focus shows what hover shows.

- **A crosshair finds the X.** On line and area charts a hairline follows the pointer and snaps to the nearest position on the axis, so
  the reader aims at a date, not at a 2px line.
- **On bars, segments, dots and cells the mark is the target.** No crosshair. Each carries its own pointer and focus handler showing the
  category and value, and the hovered mark lifts (a slight lightening or an outline) so the reader sees it answer.
- **One tooltip lists every series at that X**, so the pointer never has to land on a line to get a value.
- **Values lead, names follow.** The value is the strong, high-contrast part and the series name is secondary: the legend's order turned
  over, because here the reader already has the series and wants the number.
- **Line keys, not boxes.** Tooltip rows key a series with a short stroke of its colour. A filled box is ink doing a label's job.
- **The target is bigger than the mark.** A mark's hit area includes its 2px gap and more. Give a small dot a transparent target of at least
  24px, or for a dense scatter use a nearest-point layer so the pointer only has to be closest, not exact.
- **Series and category names are untrusted data.** They come from records, files and tool output. Put them into the tooltip, legend and
  table with `textContent` or `createTextNode`, never by building an HTML string.
- **A label pushed off its mark lives in the tooltip** (see `marks-and-anatomy.md`).

## Filters and periods

These are ordinary controls, styled to match the page. What this skill adds is where they go and what they scope.

- **One row above the charts**, left-aligned, never inside a card and never one per chart. If one chart wants its own range it belongs on
  another page.
- **The period first**, with presets (today, last 7, 30, 90 days, this month) before a custom range. Presets are rows with the chosen one
  marked by a 16px check; hover is a pale wash that never competes with the selection; a custom range sits behind a hairline at the foot.
- **A filter scopes everything below it.** Every chart, figure and table redraws against the same slice so the numbers always agree. It
  filters what the page already holds and never reads again.
- **A refreshed figure keeps its frame.** While live data reloads, the previous drawing stays in place at reduced opacity: no skeleton, no
  jump of layout, no flash.
- **Dimension filters** (a project, a team) are a standard select or combobox.
