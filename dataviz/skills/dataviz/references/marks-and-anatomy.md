<!-- SURFACE_REASON: the mark specs, spacers, labels and figures of the dataviz skill, loaded on demand when an app draws a chart -->
# Marks and anatomy

A quiet chart is a few fixed specs and some empty space. Only the data is allowed to be loud.

## Mark specs

| Mark | Spec |
|---|---|
| Bar or column | At most 24px thick (never fill the slot; leftover space stays empty). Rounded 4px at the data end, square at the baseline. Grows from one baseline at zero |
| Line | 2px, round joins and caps |
| Dot or end marker | 8px or more across (radius 4), filled with the series colour |
| Area | The series colour at about 10% opacity: a wash, never a block |
| Gridlines and axes | One shade off the surface (`--grid`, `--axis`), 1px, solid, recessive. Never dashed |

## The two spacers

- **Surface gap.** A 2px gap in the surface colour separates every touching mark: each segment of a stack and each adjacent bar, one width
  throughout. Neighbours a step apart read as distinct because of the gap, not because of an outline.
- **Surface ring.** A dot or end marker carries a 2px ring in the surface colour so it stays clear where it crosses a line or another dot.
  The ring counts as part of the mark's hit area (see `interaction.md`).

Never outline a mark to separate it. An outline is ink that is not data.

## Labels and legend

Two or more series always have a legend: it is the channel that never depends on matching colours by eye. Direct labels then sit on the
marks as a supplement. A single series needs no legend, because the title already says what is plotted.

- **Label selectively.** A number beside every point is noise. Label the end, the extreme, or the series the story is about; the axis,
  legend and tooltip carry the rest.
- **Direct labels before gridlines, gridlines before a second axis.**
- **Bars carry the value at the tip, columns on the cap, lines at their end.** Axis ticks round to clean values and shorten from 1,000 up
  (0, 1K, 2K); keep them unless every mark is labelled.
- **Measure before placing a label inside a mark.** It goes inside only if the rendered text fits with room on both sides. If not, a bar
  or column takes it just outside its end; a stacked segment has no free end, so it drops the label and the legend and tooltip carry
  it. Never `overflow: hidden` to fit one: cropped characters are worse than none. A value pushed out of its mark stays in the tooltip
  and in the table view.
- **Text never wears the data colour.** Marks carry series colours; labels, values, legends and axis text use the ink tokens (`--ink`,
  `--ink-2`, `--ink-3`). A pale hue is unreadable as text. Identity comes from a coloured dot, short line or swatch beside the text. The one
  exception is a label inside a coloured fill, which takes the white or dark colour `palette.md` names for that fill.
- **Colliding end labels are not stacked.** Nudging labels apart detaches them from their lines. Use leader lines, split into small
  charts, or fall back to the legend and tooltip. Past about four converging series, small charts are usually right.

## Figures: when the form is a number

- **Stat tile:** a label (sentence case, no colon); the value (semibold, compacted: 1,284, 12.9K, 4.2M); an optional change (signed, against a
  named period, coloured by direction and by whether up is good); an optional trend of about twelve points, the past in grey and the
  current period in the accent.
- **Meter:** the fill moves from accent to warning to danger as severity rises; the unfilled track is a paler step of the same hue so the
  whole bar reads as one state.
- **Hero figure:** the one number the page leads with, 48px or more, in the page's sans, one per view.
- **Proportional figures for big numbers**, tabular only in columns that must line up. Equal-width digits make a large `121` look loose.

## Texture, the backup channel

Where hue cannot carry identity (full colour blindness, black-and-white print, forced colours), a diagonal hatch does. Use 45 degrees and its
135-degree mirror only, since horizontal and vertical read as gridlines and bars. Draw it in a step of the fill's own colour, with the same
weight on every slot. On a value scale the angle or spacing follows magnitude and, on a diverging scale, the arm's direction carries the
sign, so the texture never misstates the value. It is switched on by an accessibility control, print or `forced-colors`, never by default and
never as decoration.
