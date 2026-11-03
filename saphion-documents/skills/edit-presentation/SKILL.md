---
name: "edit-presentation"
description: "Add slides to a PowerPoint template or deck on its own layouts, and update its slides"
user-invocable: false
metadata:
  outcome: "A PowerPoint template or deck the person supplied, changed and returned: slides added on its own layouts, slides updated, its layouts, theme and placeholders kept, every slide measured and looked at, nothing overflowing."
  not-outcomes: |-
    Build a new deck from nothing, or one that no template or supplied deck is the base of.
    Summarise or read a deck without changing it.
    Make a Word document, PDF or spreadsheet.
---
<!-- SURFACE_REASON: procedure prompt asset and helper scripts for the edit_presentation skill, loaded into the model's skill instructions for changing a PowerPoint template or deck the person supplied -->
# Edit a presentation

The person gave you a PowerPoint template or a deck and wants slides added or changed in it: three
new slides for a project review, one slide brought up to date. The result must still be their deck:
the same layouts, theme and placeholders, the new slides on the template's own layouts, each slide
measured and looked at, nothing overflowing. Two helper scripts do the file work with `python-pptx`
inside the file sandbox; you decide the content and the layouts, and you look at every slide.

Run a script from `execute_code` with `skill_script(skill="edit-presentation", script="scripts/<name>.py", args=[...], input_continuation_refs=[...])`. A file is named in `input_continuation_refs` by the `reference` you were shown it under; in `args` its path is `{input_1}` (the first file), `{input_2}` and so on. The
sandbox has no network and no installs. A deck built from nothing, or with no template or supplied deck behind it, is not changed
here: it is built new, by a program that makes it.

## 1. Know the template

1. Run `scripts/inspect_deck.py` with `args: ["{input_1}"]`. It prints each slide (its layout,
   its first text, anything it found wrong) and each layout with its placeholders as
   `number:kind widthxheight` in inches. It writes no file. The run shows the last 2,000 characters: for a
   long deck run it again with `slides` or `layouts` as a second argument to list only that part.
2. Look at the template itself: `read` the deck's reference with `at` `1-6` (then `7-12`) and say what
   you see: the look, how titles and bullets sit, what the slides of each layout carry. A layout you
   will add is best understood from a slide that already uses it.
3. Choose, for every slide you will add, the layout whose placeholders fit its content: title and
   body, two columns, a section divider, title only. Use the placeholder sizes from the printed list to
   judge capacity: a line of 20 pt text is about 0.33 in high, and a bullet that wraps takes two.

## 2. Plan the change

Write the plan before running anything: for each new slide the layout, the title and the
text of each placeholder; for each slide to update, which placeholders change and to what.

- A title **states its point** ("Programme is two weeks behind on the frame"), never a topic label.
  At the template's title size this is usually one or two lines: write for the box.
- One idea per slide: a title and at most five short bullets (about 12 words each). More is two slides.
- Use the person's facts and what the tools returned for figures, names and dates. A fact you do not
  have is a bracketed placeholder (`[client name]`), listed in your reply.
- Match the deck's own wording style, capitalisation and units (`£`, `dd Month yyyy`, metric).
- Speaker notes carry the presenter's detail, not the slide. A slide's existing notes are kept: `notes` on an
  update adds a paragraph after them. Replace them only when the person asked, with `replace_notes`.

## 3. Make the change

Run `scripts/edit_deck.py` with `args: ["{input_1}", <spec>]`, and optionally a third argument,
the output name (it must end `.pptx`); leave it out and the deck is saved under its own name, as a new version of itself (a file the person uploaded is never changed: the first edit makes one working copy beside it). Name it only when the person asks for a copy. The spec is one
JSON text:

```
{"slides": [
  {"update": 3, "set": {"title": "...", "1": ["first point", "second point"]}, "notes": "..."},
  {"add": "Title and Content", "after": 3, "set": {"title": "...", "1": ["..."]}, "notes": "..."},
  {"delete": 6}
]}
```

- Slide numbers are the template's own, whatever else you add or delete; `after: 0` is the front and no
  `after` is the end. Slides added after the same slide keep the order you list them in.
- `add` is a layout's exact name, or its number from the printed list when two layouts share a name.
- A `set` key is `title`, a placeholder number from the printed list, or an exact shape name. Its value is a
  text (a line break starts a paragraph) or a list of paragraphs, each a text or `{"text": "...", "level": 1}`
  for a sub-point. Only the shapes you list change; an updated shape keeps its own formatting and bullets.
- A placeholder you leave out of an added slide is dropped, not left empty. Picture, chart and table
  placeholders are not filled by this skill: a new slide that needs one is a gap to tell the person about.
- The script writes the deck only if nothing on a slide you added or updated overflows its box, leaves the
  slide or keeps sample wording. Otherwise it stops and names the slide and the box: cut words, split the
  slide or choose a larger layout, and run it again. Never ask for smaller type to get past it.
- Run it again from the **original** template with the corrected spec, never from your own output, so
  edits do not compound. Say which file is the final one.

## 4. Look at every slide (mandatory)

The script's measurement is an estimate; the render is the proof. `read` the delivered deck by its
`continuation_ref` with `at` `1-6`, then `7-12` and on, until every slide has been shown, and say what is
on each one before judging it:

- text running past its box, the bottom or the right edge; a title wrapping into the body;
- an empty or half-filled placeholder, sample wording, a stray font or colour;
- an added slide that looks different from a template slide on the same layout (compare them);
- a chart, table or group the script said it did not measure: judge it here.

Fix each cause in the spec, run again and look at the new images. Deliver only when every slide of the
final file has been viewed.

## 5. Reply

Say which slides were added and on which layouts, which was updated and what changed, the final slide
count, how many slides you viewed, and every bracketed placeholder still to complete. Say what the
skill did not do (a picture or chart the person asked for) rather than leaving it unmentioned.
