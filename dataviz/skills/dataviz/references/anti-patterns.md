<!-- SURFACE_REASON: the failure modes the dataviz skill checks every chart against before it ships, loaded on demand by the procedure -->
# Anti-patterns: what goes wrong

Check every chart against this list before it ships. If a chart matches an entry it is wrong, and the fix is the "Instead".

## Colour and encoding

- **A second y-axis.** The two scales line up by accident, so the chart invents a link between the series. A users-against-sessions chart
  with ranges 0 to 30k and 0 to 800k looks like a causal story and is not one. *Instead:* two charts, small multiples, or both series
  indexed to 100 at the start on one axis.
- **Recolouring when a filter changes.** Giving colours by current rank repaints the survivors, and the reader who learned "Acme is
  indigo" is misled. *Instead:* a colour belongs to the entity; the rest keep theirs.
- **An eighth hue, or cycling.** A generated or reused colour past the palette is indistinguishable from an existing one. *Instead:*
  fold the tail into "Other", split into small charts, or add a second encoding such as shape.
- **Judging colour-blind safety by eye.** "They look different enough." *Instead:* run `scripts/validate_palette.py` and read the verdict.
- **A magnitude ramp on nominal categories.** Darker-where-bigger on products or teams double-encodes the bar's length as colour and fails
  the categorical checks by design. *Instead:* one colour, slot 1, for every bar; an ordinal ramp only for ordered categories.
- **A rainbow for magnitude.** *Instead:* one hue, pale to strong. A multi-hue ramp is only acceptable for a natural heat scale, with a
  scale legend.
- **A coloured midpoint, or two cool hues as the poles of a diverging scale.** The middle must read as nothing and the sides as opposite.
  *Instead:* the blue and orange pair around the neutral grey. Never red against green.
- **A status colour on a plain series, or a series colour on a status.** *Instead:* status marks only for what means good or bad, with an
  icon and a word; categorical otherwise.

## Form

- **Several colours when the story is one number.** The commonest way a chart misses its point. *Instead:* emphasis (one in the accent, the
  rest grey), a stat tile, or the hero figure.
- **A one-bar bar chart, or a two-slice pie.** *Instead:* a stat tile; the number is the chart.
- **A pie or donut to compare close values.** *Instead:* bars, or the numbers. Part-to-whole at a glance only, five slices at most.
- **More than about seven meaningful colour classes.** Adjacent classes blur. *Instead:* a table, or a table and a chart.
- **A truncated bar axis.** Bars start at zero; a baseline that starts elsewhere exaggerates every difference. A line may start elsewhere
  if the axis says so.

## Marks and chrome

- **Thick, saturated blocks, heavy gridlines, no air.** Loud, even childish, at scale. *Instead:* thin marks, hairline recessive
  gridlines, generous padding; saturation for small marks and accents only.
- **Dashed gridlines or axes.** Dashes read as a projection or a threshold. *Instead:* solid hairlines one shade off the surface.
- **A number on every point.** *Instead:* a legend for two or more series; label the end, the extreme or the series that matters.
- **An outline around marks to separate them.** *Instead:* the 2px surface gap between fills and the 2px surface ring on dots.
- **A label clipped by, or overflowing, a small mark**, including `overflow: hidden` cropping the ends of a label. *Instead:* label inside
  only when it fits with room, otherwise outside the end or in the tooltip and table.
- **Data-coloured text.** A pale hue is unreadable as text. *Instead:* ink tokens for text, and a coloured dot or line beside it.
- **A fixed container height that leaves out the x-axis band.** The plot fits and the axis labels do not, so the card scrolls. *Instead:*
  size to plot plus axis labels, or let the container grow.
- **A display or serif face on the hero figure,** or tabular figures on a large standalone number. *Instead:* the page's sans with
  proportional figures; tabular only in columns.
- **Texture by default or as decoration.** Dense angled fields are a vestibular risk and noise on a value scale. *Instead:* opt-in, 45 or
  135 degrees only, ordered on value scales.
- **A 3D chart, a gradient fill, a shadow on a mark.** Depth distorts size and adds no data.

## Interaction and accessibility

- **A tooltip as the only way to read a value.** *Instead:* direct labels or the table view as well; focus shows what hover shows.
- **A pinpoint target** such as an 8px dot hit dead centre. *Instead:* a 24px target, or a nearest-point layer.
- **A filter inside a chart card, or one per chart.** *Instead:* one row above everything it scopes.
- **A skeleton flash on refresh.** *Instead:* hold the last drawing at reduced opacity.
- **No table view, or colour as the only encoding on a continuous scale.** *Instead:* every chart has its table twin, and a scale legend.
- **Names put into the page as HTML.** A series name from a record can carry markup. *Instead:* `textContent`.
- **A figure typed into the page** that a live source or a program already gives. It goes stale and shows the maker's numbers to everyone.
