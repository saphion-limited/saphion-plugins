---
name: "make-presentation"
description: "PowerPoint decks (.pptx) with one idea per slide"
user-invocable: false
metadata:
  outcome: "A new PowerPoint deck (.pptx) built for the person: one idea per slide, a designed consistent theme, real charts and tables where there is data, and every slide checked for overflow."
  not-outcomes: |-
    Outline or script a talk in the conversation without making a file.
    Make a Word document, PDF or spreadsheet.
    Make an interactive app or page.
  hand-over-edit-presentation: "Add slides to, or update slides in, a template or a deck the person supplied."
---
<!-- SURFACE_REASON: procedure prompt asset for the make_presentation skill, loaded into the model's skill instructions for building PowerPoint decks -->
# Make a presentation

You are building a PowerPoint deck the person will present or send: a client update, a bid
presentation, a safety briefing, a project review. A good deck is a small number of clear
slides, each carrying one idea, laid out consistently. You build it by writing a program and
running it with `file_build`, then you check the file and look at the slide images before the
person hears it is ready. This procedure carries its own design guidance (section 2).

Call `file_build` with exactly these fields: `program`, `language` (`python` or `node`), `outputs` (a list of file names, ending `.pptx`), `title`, `checks`, optional `render_pages` (`output`, `first`, `last`), `description`, `inputs` (the person's own files the program opens) and, to change a file you already made, `replaces_file_id`. Call `file_build` directly as its own tool. Never call it from inside `execute_code`: it is not available there.

## 1. What the program can reach

- A run delivers up to **16 files**, each as its own card. A replacement declares exactly one output. No network and no installs, so no downloaded images, icons or
  fonts. A program is stopped after about a minute.
- The input files are the current version of the file named by `replaces_file_id` (under its own
  name) and every file you name in `inputs`: site photographs, drawings or tables the person attached,
  or Organisation files, each by the reference you were shown it under (an attachment's `source_ref`,
  or `organisation-file:<id>@<hash>`). Each is placed in the working directory under its own name
  made safe (or the `name` you give) and the result lists the names: put a photograph on a slide from
  there (`slide.shapes.add_picture("site-1.jpg", ...)`, `pptxgenjs` `addImage({path})`), never write its
  bytes into the program. Pictures, CSV, Excel, Word, PowerPoint and PDF, at most 15 MB each; a file you
  cannot read here refuses the run, naming it.
- Node has `pptxgenjs`; Python has `python-pptx`, `pillow` and `matplotlib`. LibreOffice renders the
  checks. Fonts present: Calibri, Arial, Cambria, Times New Roman and Courier New (as metric-matched
  stand-ins), and DejaVu.

| Job | Use |
|---|---|
| New deck | Node with `pptxgenjs` (masters, rich native charts, tables, shapes) or Python with `python-pptx` (native charts and tables too, plus text measuring with `pillow`) |
| Change a deck you made | Pass its `continuation_ref` as `replaces_file_id`: same file, new version. Open it with `pptx.Presentation`, change it, save a `.pptx`. Never rebuild from nothing or make a second copy. |

Give `file_build` the program, the output names, `checks: ["validate_ooxml", "render_pages"]` and a
one-line `description`. Both checks are mandatory.

## 2. Plan before you code

Write the storyline first, as comments at the top of the program: the audience, what they should
decide or remember, and one sentence per slide. Then build.

- **A normal deck is 5 to 12 slides.** If the person gave a number, match it exactly.
- **Order:** title, the headline message or ask, the evidence in a few slides, the
  recommendation or next steps, a close. An agenda only above about eight slides.
- Each slide has a **title that states its point** ("Programme is two weeks behind on the frame"),
  not a topic label ("Programme").
- Missing facts: use what the person supplied or the tools returned for figures, quotes, client
  names and logos. A missing fact is a bracketed placeholder, listed in your reply.

For visual foundations, use `read_skill_resource` with `skill_name: "design"` and
`resource_name: "references/design_basics.md"`. Read the reference when choosing the visual direction;
apply the guidance relevant to this deliverable.

For a deck, plan the look in the same comments as the storyline and define the theme once, on the slide
master. A pale tint or thin grey line vanishes on a projector.

## 3. Rules for every deck

- **One idea per slide.** A title plus at most five short bullets (about 12 words a line), or a
  title plus one chart, one table or one image with a caption. If you need more, make two slides.
  Never shrink the type to fit more.
- **Real charts and tables where there is data.** A native bar, line or pie chart from the
  numbers, or a table with a styled header row; not a screenshot, and not bullets that read out
  figures. Label axes and units, and give the figures that matter a data label. Only a chart with no
  native form goes in as an image drawn with `matplotlib`, with alt text.
- **Vary the layout, keep the system.** Two columns, a large figure with a small label, a comparison,
  a timeline or process, a full-bleed image with a scrim. Every content slide shows something
  (figure, chart, table, diagram, image); a slide of plain bullets is the exception. Dark title and
  closing slides with light content slides is a common sandwich; so is one ground throughout.
- **16:9, 13.33 x 7.5 in.** Margins of at least 0.5 in; 0.3 to 0.5 in between blocks, one gap used
  consistently. Nothing outside the slide; nothing overlapping except text over an image with a scrim.
- **One theme**, set once from the look plan. Titles 28 to 36 pt, body at least 18 pt, captions
  and sources at least 12 pt, strong contrast. Use only the faces above: a serif for titles with a
  sans for body gives contrast and reliable text fit. Left-align body text; centre only titles.
  Avoid fonts with no matching stand-in here (Aptos, Georgia, Trebuchet): the render would
  mislead you about fit.
- **Same positions on every slide:** title in one place and size, body below, footer with the slide
  number. Build repeated structure from a helper or a slide master, not by pasting.
- **Speaker notes** hold the presenter's detail, not the slide: `slide.addNotes` (pptxgenjs) or
  `slide.notes_slide.notes_text_frame.text` (python-pptx).
- **Alt text** on every image, and a caption on every chart that states its finding; no information
  held only in colour. RAG status as a word as well as a colour.

## 4. Library traps that corrupt a file or hide content

`validate_ooxml` opens the file with python-pptx, which accepts several things PowerPoint refuses. Avoid
these in the program; the check will not catch them.

**pptxgenjs**
- Set `layout` before adding slides. The default canvas is 10 x 5.625 in; `"LAYOUT_WIDE"` is
  13.33 x 7.5. Anything placed past the edge is written, not clamped, so it is simply off the slide.
- Colours are six hex digits without `#`. A `#`, or alpha folded into eight digits, corrupts the
  file; use `transparency` (0 to 100) on fills and `opacity` (0 to 1) on shadows.
- A shadow offset must not be negative. For an upward shadow use angle 270 with a positive offset.
- The library rewrites the options object you pass. Build a fresh object for each call, and a fresh
  `new pptxgen()` for each file.
- Letter spacing is `charSpacing`. `rectRadius` works only on a rounded rectangle. Gradient fills
  are not supported: use a gradient image as the background.
- A text box has internal padding: set `margin: 0` when text must line up with a shape or line.
- Bullets: `bullet: true` per item, never a typed bullet character (it doubles). Give every item
  in a text array `breakLine: true` except the last. Space paragraphs with `paraSpaceAfter`, not
  line spacing.
- On a stacked bar or column chart `dataLabelPosition` must be `ctr`, `inEnd` or `inBase`: `outEnd`
  corrupts the file. A combo chart using a secondary axis needs both `valAxes` and `catAxes`, two
  entries each.
- Default charts are bare. Set the title, data labels, `chartColors` from the palette, light
  gridlines on one axis only, and no legend for a single series.

**python-pptx**
- A new `Presentation()` is 4:3. Set `slide_width` to 13.333 in and `slide_height` to 7.5 in, use the
  blank layout (index 6) and place your own shapes; the default placeholders carry template styling.
- Assign text to `run.text`, not `text_frame.text`, which flattens formatting into one plain run.
  Set `word_wrap = True` on each text frame.
- It cannot duplicate a slide, and cannot read SVG pictures.

## 5. Changing a deck

- Do structural work first (add, delete, reorder), then edit content; editing before duplicating
  copies the edit. Reorder or drop slides through the `sldIdLst` order and drop the relationship of
  a deleted slide so it does not stay in the file.
- A design slot with no content (a fourth team member when you have three) is deleted whole, picture
  and text together; check for orphaned shapes afterwards.
- One paragraph per list item. Keep the neighbouring paragraph's properties when adding one, and bold
  titles and inline labels ("Status:") the way the deck does. Let bullets come from the layout.
- Match the deck's existing look unless the person asks to change it.

## 6. The checks (mandatory)

`validate_ooxml` confirms the package opens and counts slides and layouts; compare the slide count
with your plan. `render_pages` renders up to six slides per inspection through LibreOffice. Default
is slides 1–6; optional `render_pages: {output, first, last}` selects one output and inclusive range.
The report states total slides, exact slides shown and the next native-file read. Images judge layout, not small print.

1. **Measure fit in the program, for every slide.** Alongside the images, check text fit
   in code: with `pillow`'s `ImageFont` and the matching font file (found by globbing
   `/usr/share/fonts`), measure each text box's longest lines at its point size against the box width
   and the wrapped height against the box height, and raise an error that names the slide and box when
   anything overflows. Check also that every left edge plus width stays inside the slide minus the margin.
2. **Print an outline** from the program: slide number, title and word count per slide, and any
   leftover `TODO`, `XXX` or sample wording. Check that every title states a point, the order is
   right and nothing is missing.
3. **Look at every returned image**, one at a time, and say what is on it before judging it. Check:
   - text overflowing its box or running off the bottom or right edge (read each line to its last
     word: a title cut at the edge still looks finished at a glance);
   - a title wrapping to three lines or colliding with the body; sources or footers touching content;
   - chart labels overlapping, a table running past the slide, elements closer than 0.3 in or crowding
     the margin;
   - low contrast, a stray font, an empty placeholder, a slide dense enough to read as a report page.
4. Fix each cause in the program (cut words, split the slide, widen the box, drop categories), never by
   shrinking text below the minimums. Run again and look at the new images.
5. Follow `next_read` with `read` on the made file's `continuation_ref`, passing its `at` (the pages).
   Continue inspecting the already-made file until every slide has been shown. Never rebuild or replace
   it merely to inspect later slides. Deliver when validation passes and every claimed slide was inspected.

## 7. Pitfalls

- Text does not shrink or wrap for you in a generated file: size each box for a longer line than
  you expect, turn wrapping on, and make long titles as wide as the content area.
- Charts: a few categories (at most eight) in one unit, values sorted. A pie only for parts of one
  whole with up to five slices.
- Images keep their aspect ratio: crop to fill, never squash.
- Tables: at most about seven rows and five columns per slide, header styled, numbers right-aligned.
  A longer table goes in an appendix or a spreadsheet.
- Do not put the speaker's script on the slide.

## 8. Conventions

- **Construction and project updates:** one slide each for progress against programme, cost position,
  risks and issues, health and safety, and the next period.
- **Bid and tender presentations:** answer the client's evaluation criteria in their order, one slide
  each, with the evidence (a project, a figure, a name) and the commitment.
- **Briefings and toolbox talks:** the hazard, the control, who does what, and a question that checks
  understanding.
- `£`, `dd Month yyyy` dates, metric units.

Say in your reply what the deck contains, the slide count, how many slides you viewed, and any
placeholder to complete.
