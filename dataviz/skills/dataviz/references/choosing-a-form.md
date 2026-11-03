<!-- SURFACE_REASON: how the dataviz skill picks the form of each figure before any colour, loaded on demand by the procedure -->
# Choosing the form

Decide the form first, then the colour. What the reader has to do with the figure picks the form, and often the right form is not a chart.

## Is it a chart at all?

| The figure is | Draw | Not |
|---|---|---|
| One current value, perhaps with a change | A stat tile: the value, the change against a named period, optionally a small trend | A bar chart of one bar |
| A few headline numbers | A row of stat tiles | A grouped bar chart |
| The one number the page leads with | The hero figure, 48px or more, in the page's own sans | Anything decorative |
| One amount against a limit or target | A meter whose track is a paler step of the fill's own colour | A pie of two slices |
| A lookup, or more than seven classes that all matter | A table (with a chart above it if a pattern matters) | More colours |

## What the reader must do, and the form that does it

| The reader must | Default form | Colour job |
|---|---|---|
| Compare amounts | Bars (columns for time or few items); a heatmap when it is a grid | Sequential, or one categorical colour |
| See a change over time | Line; an area for one series | One categorical colour, or sequential |
| Tell several series apart | Grouped or stacked bars, several lines | Categorical |
| See that one series is the story | Emphasis: that series in the accent, the rest in grey | One hue and grey |
| See above or below a baseline, or against a target | Diverging bars, or a line against its baseline | Diverging |
| See parts of a whole | One stacked bar (horizontal when names are long or many) | Categorical |
| Read an ordered scale (agree to disagree, low to high) | A diverging stacked bar centred on the neutral | Diverging |
| See before and after for each item | A dumbbell: two dots joined by a line | One hue, two shades |

## The reasoning

- **Sequential is the safe default.** One hue, more is darker. Use another colour job only when the data is about identity (which series) or
  polarity (which side).
- **Categorical is for when the series themselves are the subject**, and it has a cost: eight colours bury the one thing that matters. If
  the story is "this one rose", draw emphasis, not a rainbow of series.
- **Nominal bars are one colour.** Names with no natural order (products, teams, sites) all take slot 1 when they are one series. Colouring
  each bar by its value spends the colour channel on what the bar's length already says.
- **Ordered categories are ordinal**: funnel stages, size tiers, age bands. Swap the order and the meaning changes, so they take one hue in
  steps. Swap the order and nothing changes (regions, teams) and they are nominal.
- **Pie and donut** only for shares of a whole at a glance, five slices at most, never to compare close values. A bar says it better.
- **Texture** is a backup channel for accessibility and print, never a form (see `marks-and-anatomy.md`).

## How many series

| Series | Treatment |
|---|---|
| 1 to 3 | Colour is enough for everyone; still label directly |
| 4 | Fine for stacks, bars and lines, where only neighbours touch; direct labels become required. Scatter, bubble and map charts, where any two marks touch, stop at three |
| 5 to 6 | The practical limit; a legend or small charts |
| 7 | The palette's end |
| More | Fold the tail into "Other", split into small charts, or draw a table. Never invent an eighth hue: it cannot be told from an existing one |
