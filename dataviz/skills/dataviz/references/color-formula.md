<!-- SURFACE_REASON: the colour method of the dataviz skill (the jobs colour does, the six checks and how to run them), loaded on demand by the procedure -->
# Colour by job, then measure it

Colour in a chart is never picked by eye. Each colour does one of five jobs, and a categorical set is allowed only if it passes the checks
below. `palette.md` holds Saphion's values; this file is the method they were checked with, so it can be run again on any colours.

## The five jobs

| Job | It says | Shape |
|---|---|---|
| Categorical | Which series | Up to seven hues in a fixed order, assigned in sequence, never skipped or cycled |
| Ordinal | Where in an ordered set | One hue in steps, lightness running one way; the palest step still shows on the surface |
| Sequential | How much | One hue, pale to strong; the palest step may recede, it means almost nothing |
| Diverging | Which side of a baseline | Two opposite hues and a neutral grey midpoint, the same number of steps each side |
| Status | A state, good to critical | A small fixed set with reserved meaning, always with an icon and a word |

Categorical or ordinal? If swapping the order would change the meaning (funnel stages, size tiers, age bands), it is ordinal. If not
(products, teams, regions), it is nominal: one series takes slot 1 for every bar, and N separate series take slots 1 to N. Colouring
nominal bars by their value is the mistake to avoid.

## The checks a categorical set must pass

1. **Fixed order.** The order of the hues is what keeps neighbours apart, so it is never changed to suit a chart. Structural: a rule, not a measurement.
2. **Lightness band.** Every colour's OKLCH lightness sits inside the band for the mode (too pale vanishes on the surface; too dark or too loud overpowers).
3. **Chroma floor.** OKLCH chroma of 0.10 or more. Below it a hue reads as grey and no longer says which series it is.
4. **Colour-blind separation.** The distance between neighbouring colours, measured in OKLab times 100, with protanopia and deuteranopia
   simulated (Machado, Oliveira and Fernandes, 2009, full severity), is at least 8, and never under 6. A pair between 6 and 8 is
   allowed only with a second channel: direct labels, a visible gap or texture.
5. **Normal-vision floor.** The same distance with no simulation is at least 15 for the worst pair. Full-colour readers must tell neighbours
   apart too, and a second channel does not excuse this one.
6. **Contrast on the surface.** Marks reach 3:1 against the surface. Under 3:1 is a warning that obliges a relief: a visible label on the
   mark, or the table view. Shipping a pale fill with neither is a failure.
7. **Tokens only.** Every hex comes from `palette.md`. Structural: a colour not in it is invented.

Which pairs count depends on the chart. Stacks, bars and lines only ever put neighbours side by side, so adjacent pairs are enough. Scatter,
bubble, map and small-multiples charts can put any two marks together, so every pair must pass (`--pairs all`), which is stricter and is
why those forms stop at three series. If an all-pairs run fails over many series, that is the series limit, not a colour to fix: use fewer
series, split into small charts, or change the form. Reordering cannot make seven colours all pairwise distinct.

## Run the check

From `execute_code`, run the script with the colours in the order the app will assign them, once per mode, against that mode's surface:

```
skill_script(skill="dataviz", script="scripts/validate_palette.py",
             args=["#5a67d8,#c54b78,#c48a1e", "--mode", "light"])
skill_script(skill="dataviz", script="scripts/validate_palette.py",
             args=["#8e9af3,#e68aab,#d8a443", "--mode", "dark", "--pairs", "all"])
```

The surfaces default to Saphion's (`--surface` overrides); `--band LOW,HIGH` overrides the lightness band. Other kinds: `--kind ordinal`
(a one-hue stepped set: lightness runs one way, steps at least 0.06 apart, the palest step 2:1 on the surface, one hue),
`--kind sequential` (lightness runs one way, one hue; judging a ramp as categorical fails it by design) and `--kind text` (each colour as
text needs 4.5:1). It prints one line per check as PASS, WARN or FAIL and ends with a verdict. It exits normally whatever the verdict, so
read the last line: a FAIL is the answer, not a broken run, and a bad colour string is refused by name.

- A WARN on colour-blind separation or contrast stands only with its relief channel, and your reply to the person says which.
- A FAIL on the normal-vision floor means two neighbours look alike to anyone: change one, or reduce the series.
- Never ship a set that failed. Change the colours, the order within the palette's rules, the series count or the form, and run again.

## When the person gives their own colours

Use them when asked, in the order they will be assigned. For each slot pick the step whose lightness sits in the band and chroma meets the
floor; run the check; for each neighbouring pair that falls short, move one of the two a step (keep its hue, change its lightness) and
run again until the worst pair clears. If no set of their hues can pass, say which pair collides and offer Saphion's palette instead.

## Order is a choice, not a guess

If a set of hues has no tested order, do not guess. Try the orderings of the hues, run the check on each, keep those that pass in both
modes and pick among them the one with the widest worst-pair separation and the best opening colours. That is how `palette.md`'s order was
found. An order is adopted for a whole app and never mixed with another inside it.

## What the checks do not judge

They judge a categorical set. They do not judge a lone status or text colour (use `--kind text`) and a ramp is judged as a ramp, not as
categorical. They say nothing about whether the chart reads well; the form, the labels and the table view do that.

## Status is fixed

Status never follows a theme or an app's taste. It is the small set in `palette.md`, with the reserved meaning of good, warning, serious
and critical, and it always comes with an icon and a word because colour alone must never carry a state (and warning's amber is only 3:1 on a light surface). When a series means
good or bad (error rate, pass or fail) it wears status; when it is only "series 4" it wears categorical; never both in one chart.
