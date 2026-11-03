<!-- SURFACE_REASON: Saphion's chart colours and chrome for the dataviz skill, each value a token of the product's one colour owner (ramps.css) so an app draws with the same colours as the product -->
# Saphion's palette

Every colour in an app's chart is one of the product's own, never one chosen for the occasion. Saphion keeps its colours in one place
(`ramps.css`, the "label palette" that chips, avatars and the product's charts all draw from, with `tokens.css` pointing at it). An
app cannot see those files, so it copies the values below into its own `:root` tokens. The tables name the product token each value is,
so a value can be traced and a changed token is found by the test that compares them. Where a step is a mix, the table says what is
mixed with what.

The method is the one in `color-formula.md`; this file is only the values it is run on.

## The tokens block

Write the roles an app uses, light first, then dark under both scopes. The host sets `data-theme` on the root and changes it live;
a document with no `data-theme` follows the system. The `:not([data-theme])` scope covers that case and the `[data-theme="dark"]` one
covers the host's, so neither can win over the other by order.

```css
:root {
  color-scheme: light;
  --bg: #ffffff;          --surface: #ffffff;       --surface-sunken: #f7f6f3;
  --ink: #1d1c1a;         --ink-2: #57544e;         --ink-3: #6b6760;
  --grid: #e9e7e2;        --axis: #dad7d0;
  --good-text: #25754b;   --bad-text: #b23c30;      --warn-text: #8f5e0e;
  --s1: #5a67d8; --s2: #c54b78; --s3: #c48a1e; --s4: #3b82c4; --s5: #2e8456; --s6: #8662c9; --s7: #c0612b;
  --other: #8a867e;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    color-scheme: dark;
    --bg: #1a1a19;        --surface: #1d1d1c;       --surface-sunken: #181817;
    --ink: #eceae5;       --ink-2: #b5b2ab;         --ink-3: #9a968f;
    --grid: #2c2b29;      --axis: #3a3936;
    --good-text: #5cba86; --bad-text: #e57d70;      --warn-text: #d8a443;
    --s1: #8e9af3; --s2: #e68aab; --s3: #d8a443; --s4: #72a5ea; --s5: #5cba86; --s6: #a98deb; --s7: #e3925f;
    --other: #8f8b84;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #1a1a19;          --surface: #1d1d1c;       --surface-sunken: #181817;
  --ink: #eceae5;         --ink-2: #b5b2ab;         --ink-3: #9a968f;
  --grid: #2c2b29;        --axis: #3a3936;
  --good-text: #5cba86;   --bad-text: #e57d70;      --warn-text: #d8a443;
  --s1: #8e9af3; --s2: #e68aab; --s3: #d8a443; --s4: #72a5ea; --s5: #5cba86; --s6: #a98deb; --s7: #e3925f;
  --other: #8f8b84;
}
```

A canvas (Chart.js, a WebGL scene) reads these with `getComputedStyle` and redraws when the theme changes; a hex copied into a canvas
will not follow it.

## Categorical: the series order

Seven slots, assigned in this order and never skipped, cycled or reshuffled. A series keeps its slot for the life of the app, so
filtering one out never recolours the rest. Past seven, fold the tail into "Other" (`--other`), split into small charts or use a table.

| Slot | Hue | Light token | Light | Dark token | Dark |
|---|---|---|---|---|---|
| 1 | indigo | `--color-label-indigo` | `#5a67d8` | `--color-night-label-indigo` | `#8e9af3` |
| 2 | rose | `--color-label-rose` | `#c54b78` | `--color-night-label-rose` | `#e68aab` |
| 3 | amber | `--color-label-amber` | `#c48a1e` | `--color-night-label-amber` | `#d8a443` |
| 4 | blue | `--color-label-blue` | `#3b82c4` | `--color-night-label-blue` | `#72a5ea` |
| 5 | green | `--color-label-green` | `#2e8456` | `--color-night-label-green` | `#5cba86` |
| 6 | violet | `--color-label-violet` | `#8662c9` | `--color-night-label-violet` | `#a98deb` |
| 7 | orange | `--color-label-orange` | `#c0612b` | `--color-night-label-orange` | `#e3925f` |

How this order was reached, so it can be redone if the palette ever changes: every ordering of the product's data hues was run through
`scripts/validate_palette.py` in both modes and only orderings that clear every adjacent check were kept; this one opens with the product's
own lead hue (indigo) and puts the two hues that stay apart under all-pairs checking (rose, amber) next to it. The product's native chart
order is not used here, because it seats blue beside violet and indigo, which are close under colour blindness.

Two hues of the label palette are left out on purpose. **Red** is the status colour for bad, so it is never a series. **Teal** has
chroma 0.095 in light and 0.098 in dark, under the 0.10 floor: it reads as grey-green and does no identity work.

What the validator measured on this order (adjacent pairs, the default; stacks, bars and lines only ever touch neighbours):

| Check | Light | Dark |
|---|---|---|
| Worst colour-blind separation (target 8, floor 6) | 14.6 | 10.9 |
| Worst normal-vision separation (floor 15) | 17.5 | 16.3 |
| Lightness band | inside | inside |
| Contrast on the surface (3:1 for marks) | amber 3.00, a hair under: relief required | all pass |

Light amber is the one mark under 3:1, so wherever slot 3 is drawn the value must also be readable another way (a label on the mark, or the
table view). The first three slots (indigo, rose, amber) also clear the stricter **all-pairs** test in both modes, so scatter, bubble,
map and small-multiples charts, where any two marks can touch, carry at most three series. A fourth slot would put blue beside indigo.

**Dark band.** The lightness band for dark is 0.60 to 0.80, wider and lighter than a darker palette would use, because Saphion's dark data
colours are one lighter set (`--color-night-label-*`, L 0.70 to 0.75). On the dark surface every one clears 3:1 by a wide margin, which is
what the band protects. Light uses 0.43 to 0.77.

## Other (de-emphasis)

The grey for "Other", for context series in an emphasis chart and for an unfilled track.

| Role | Light token | Light | Dark token | Dark |
|---|---|---|---|---|
| Other / context | `--color-label-grey` | `#8a867e` | `--color-night-label-grey` | `#8f8b84` |

## Sequential: magnitude in one hue

Indigo mixed into the surface (`--chart-heat-1` to `--chart-heat-5`, the product's own steps), lightest meaning least. Each step is the
indigo (light `#5a67d8`, dark `#8e9af3`) at the share shown, mixed with the surface (light `#ffffff`, dark `#1d1d1c`) in sRGB. Light runs
pale to strong; dark runs from nearly the surface to bright, so "more" is always the stronger step. The palest step is allowed to recede:
it means "close to nothing".

| Step | Share of indigo | Light | Dark |
|---|---|---|---|
| 1 | 22% | `#dbdef6` | `#36384b` |
| 2 | 42% | `#babfef` | `#4c5276` |
| 3 | 62% | `#99a1e7` | `#636aa1` |
| 4 | 82% | `#7882df` | `#7a84cc` |
| 5 | 100% | `#5a67d8` | `#8e9af3` |

A second sequential measure on the same page takes orange (slot 7), mixed the same way, as its own ramp.

**Ordinal** (discrete ordered marks: funnel stages, tiers) takes steps 3, 4 and 5 and no more: the palest of them keeps 2.4:1 on light and
3.3:1 on dark. Steps 1 and 2 are too near the surface to be a separate mark, and a fourth ordered stage is a label, not a fourth shade.

## Diverging: two sides of a baseline

Blue and orange (warm against cool, so they read as opposites), with the chart's neutral as the midpoint (`--color-chart-neutral`: light
`#dad7d0`, dark `#262523`). Three steps either side, each the pole mixed into the neutral at 33%, 66% and 100%. Never red and green, which
a colour-blind reader cannot tell apart, and never a coloured midpoint.

| Side | Midpoint | 33% | 66% | Pole |
|---|---|---|---|---|
| Blue, light | `#dad7d0` | `#a6bbcc` | `#719fc8` | `#3b82c4` |
| Orange, light | `#dad7d0` | `#d1b09a` | `#c98963` | `#c0612b` |
| Blue, dark | `#262523` | `#3f4f65` | `#5879a6` | `#72a5ea` |
| Orange, dark | `#262523` | `#644937` | `#a36d4b` | `#e3925f` |

Check each side with `--kind sequential`, midpoint first.

## Status: reserved

Status colours mean a state and nothing else, and always sit beside an icon and a word. Marks use the product's label hues; text (a delta,
a verdict) uses the signal set, which is darker and readable as text.

| State | Mark, light | Mark, dark | Text token | Text, light | Text token, dark | Text, dark |
|---|---|---|---|---|---|---|
| good | `#2e8456` | `#5cba86` | `--color-signal-green` | `#25754b` | `--color-night-green` | `#5cba86` |
| warning | `#c48a1e` | `#d8a443` | `--color-signal-amber` | `#8f5e0e` | `--color-night-amber` | `#d8a443` |
| serious | `#c0612b` | `#e3925f` | | | | |
| critical | `#b23c30` | `#e57d70` | `--color-signal-red` | `#b23c30` | `--color-night-red` | `#e57d70` |

The marks are the same hexes as green, amber, orange and red of the label palette, because Saphion has one palette. So a status colour
and a series colour can be the same hue, and the rule is on the chart: when a series means good or bad it wears these and the icon and
word; when it is only "series 5" it wears its categorical slot; one chart never does both. In a chart that has status, keep slots 3, 5 and 7
(amber, green, orange) out of its series and use slots 1, 4 and 6; slot 2 (rose) sits near critical red (separation 10.2 light, 7.7 dark),
so it needs direct labels there.

## Chrome and ink

| Role | Light token | Light | Dark token | Dark |
|---|---|---|---|---|
| Page (`--bg`) | `--color-white` | `#ffffff` | `--color-night-page` | `#1a1a19` |
| Chart surface (`--surface`) | `--color-white` | `#ffffff` | `--color-night-surface` | `#1d1d1c` |
| Sunken plane (`--surface-sunken`) | `--color-neutral-60` | `#f7f6f3` | `--color-night-sunken` | `#181817` |
| Primary ink (`--ink`) | `--color-neutral-950` | `#1d1c1a` | `--color-night-text` | `#eceae5` |
| Secondary ink (`--ink-2`) | `--color-neutral-500` | `#57544e` | `--color-night-text-2` | `#b5b2ab` |
| Muted ink, axis labels (`--ink-3`) | `--color-neutral-450` | `#6b6760` | `--color-night-text-3` | `#9a968f` |
| Gridline hairline (`--grid`) | `--color-neutral-200` | `#e9e7e2` | `--color-night-border` | `#2c2b29` |
| Baseline and axis (`--axis`) | `--color-neutral-300` | `#dad7d0` | `--color-night-border-strong` | `#3a3936` |

All three inks pass 4.5:1 on their surface in both modes (primary 17.0 and 14.0, secondary 7.5 and 8.0, muted 5.6 and 5.7).

**The label inside a coloured fill** (a stacked segment, a tile) takes whichever of two colours reads better on it, the same two in every
chart. Light: white (`#ffffff`) on indigo, rose, green, violet, orange and red; primary ink (`#1d1c1a`) on amber and blue. Dark: the dark
surface colour (`#1d1d1c`) on every fill. A label that does not clear 3:1 on its fill goes outside the mark.

## Type and the page

Everything, the hero figure included, is one sans: Geist (loaded from Google Fonts with a `<link>`) then `system-ui, -apple-system,
"Segoe UI", sans-serif`. Large single numbers use proportional figures; `font-variant-numeric: tabular-nums` only for columns that line up
(table rows, axis ticks). Controls, focus rings and the page layout follow the app design rules, which this skill sits beside.
