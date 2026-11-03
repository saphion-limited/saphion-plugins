<!-- SURFACE_REASON: the parts a dataviz app's charts are assembled from, and the accessible table twin, loaded on demand by the procedure -->
# Components: the pieces a chart is made of

An app draws charts from a few parts in plain HTML and SVG (the sandbox also loads `chart.js/auto` and `d3` by bare name; hand-written SVG
is the lighter choice for a bar, a line or a meter). Build the foundations once, then reuse them for every chart on the page.

## Foundations

- **Colour roles** as CSS custom properties at the top of the document: categorical slots, the sequential ramp, diverging pairs, status,
  the grey for "Other", gridline, axis and ink. `palette.md` gives the block. Marks read the variables, so a theme switch needs no redraw
  (a canvas is the exception: it reads them with `getComputedStyle` and redraws on the theme change).
- **The chart container**: a `<figure>` with a `<figcaption>` (title and one-line caption), owning its size, and holding the **table-view
  toggle**. A fixed height includes the x-axis band (plot plus axis labels), so the card never gains a small scroll of its own; better,
  let it grow with its content.
- **Legend**: one entry per series, keyed to the mark (a rectangle for bars and areas, a line for lines); clicking an entry may isolate its
  series, and the entry keeps its colour while the others dim.
- **Tooltip, axis, data label**: as `interaction.md` and `marks-and-anatomy.md` specify them.
- **Texture fills**, where an accessibility control, print or forced colours switches them on.

## The charts people ask for

Bar (grouped, stacked, horizontal or vertical, thin by default), line (several series, an area variant, markers for keyboard and print),
stat tile, meter. Then the rest of the kit: stacked area, sparkline, heatmap, a scale legend for a sequential or diverging ramp, the filter
row, and an empty state. Part-to-whole rides on the stacked bar; a donut is rarely the right answer. Small multiples is a layout over these,
not another chart.

## The table twin

Every chart has a table of the same data, one toggle away, and it is the accessible reading of the chart. Build it from the same array the
chart draws, never typed separately, so the two cannot disagree:

```js
function tableOf(rows, columns) {            // rows: the array the chart draws; columns: [{key, label, format}]
  const table = document.createElement('table');
  const head = table.createTHead().insertRow();
  for (const c of columns) head.appendChild(Object.assign(document.createElement('th'), {scope: 'col', textContent: c.label}));
  const body = table.createTBody();
  for (const row of rows) {
    const tr = body.insertRow();
    for (const c of columns) tr.insertCell().textContent = (c.format || String)(row[c.key]);
  }
  return table;                               // names and values go in with textContent, never as HTML
}
```

The toggle switches the figure between the drawing and its table (a real `<button>` with `aria-pressed`), keeps focus on itself, and the
table scrolls inside its own container when narrow. Numbers in its columns are right-aligned with tabular figures; the unit is in the
column heading.

## An empty state

A chart with no data says what is missing and what would fill it ("No actions closed in this period"), in the chart's own place and size,
so the layout does not jump when data arrives. It never draws an empty axis with a made-up scale, and it never shows a different number.
