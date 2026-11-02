---
name: "make-document"
description: "A Word (.docx) or PDF file to download or send"
metadata:
  outcome: "A new Word document (.docx) or PDF file built for the person to download or send, such as a report, letter, minutes or method statement, designed, laid out cleanly and checked page by page."
  not-outcomes: |-
    Write the text in the conversation.
    Prepare a RAMS held in the Risk and Method Statements product.
    Make a presentation or a spreadsheet.
  hand-over-edit-word-document: "Change a Word file the person supplied, or add comments or tracked changes to any Word file."
  hand-over-edit-pdf: "Fill in, join, take pages out of or turn the pages of a PDF the person supplied."
---
<!-- SURFACE_REASON: procedure prompt asset for the make_document skill, loaded into the model's skill instructions for building Word and PDF files -->
# Make a document

You are building a Word document or a PDF the person will read, print or send: a report, a
letter, a method statement, a briefing, a one-page summary. You build it by writing a program
and running it with `file_build`, then you look at the pages it renders before the person
hears it is ready. This procedure carries its own design guidance (section 2); load no other skill
for the look.

Call `file_build` with exactly these fields: `program`, `language` (`python` or `node`), `outputs` (a list of file names, ending `.docx` or `.pdf`), `title`, `checks`, optional `render_pages` (`output`, `first`, `last`), `description`, `inputs` (the person's own files the program opens) and, to change a file you already made, `replaces_file_id`. Call `file_build` directly as its own tool. Never call it from inside `execute_code`: it is not available there.

## 1. What the program can reach

- A run delivers up to **16 files**, each as its own card. Use a ZIP for a folder-preserving bundle. A replacement declares exactly one output.
- The input files are the current version of the file named by `replaces_file_id` (under its own
  name) and every file you name in `inputs`: a photograph, a drawing or a table the person attached,
  or an Organisation file, each by the reference you were shown it under (an attachment's
  `source_ref`, or `organisation-file:<id>@<hash>`). Each is placed in the working directory under
  its own name made safe (or the `name` you give) and the result lists the names: open the picture
  there (`document.add_picture("site-photo.png", width=Inches(5))`, `reportlab` `Image`), never
  write its bytes into the program. Pictures, CSV, Excel, Word, PowerPoint and PDF, at most 15 MB
  each; a file you cannot read here refuses the run, naming it.
- No network, no installs. Python has `python-docx`, `reportlab`, `pypdf`, `lxml`, `pillow` and
  `matplotlib`; Node has `docx`; LibreOffice and poppler are present. There is no OCR, so a scanned
  PDF cannot be read. A program is stopped after about a minute.

| Job | Use |
|---|---|
| Word file | Python with `python-docx` (default), or Node `docx` when you need finer numbering or table control |
| PDF from scratch (summary, certificate, form) | Python with `reportlab` `platypus` (section 5) |
| PDF of a document the person also edits | Build the `.docx` in one run. In a second run, convert it inside the program: `soffice --headless --convert-to pdf --outdir . file.docx`, with `HOME` set to a writable folder, and deliver the PDF |
| Change a file you made | Pass its `file_id` as `replaces_file_id`: same file, new version. Open it, change it, save the same kind. Never rebuild from nothing or make a second copy. |
| Stamp or read a PDF | `pypdf`: open the PDF named in `inputs` and write the stamped copy as a new output. A PDF you made is changed with `replaces_file_id`, as above. |

Give `file_build` the program, the output names, `checks: ["render_pages"]` and a one-line
`description`. Add `validate_ooxml` for a `.docx` (it does not open a PDF).

## 2. Before you build: the reader and the argument

For anything beyond a letter or a note, settle these first. Ask the person once, in one numbered
list, only for facts the document cannot work without (client, site, dates, figures, who signs);
otherwise proceed and mark gaps as placeholders.

- Who reads it, what should they decide or do after it, and what do they already know?
- State the conclusion or the request in the first lines, then give the support. Draft the
  outline as one sentence per section in the program's comments, and cut any section that does not
  serve the reader's decision.
- Keep what the person gave you. A missing name, date, reference, regulation or figure is a visible
  placeholder in square brackets, listed in your reply. No placeholder survives by accident: scan
  the finished text in the program for stray `TODO`, `XXX` and sample wording.
- A figure appears once in the data and everywhere else is computed from it, so a summary can never
  disagree with its table.
- Read the finished text once as a stranger would: is every term explained, does any section
  contradict another, does every sentence carry weight?

For visual foundations, use `read_skill_resource` with `skill_name: "design"` and
`resource_name: "references/design_basics.md"`. Read the reference when choosing the visual direction;
apply the guidance relevant to this deliverable.

For a document, define the theme once, on the styles.

## 3. Rules for every Word document

- **Real headings.** Use the built-in Heading 1, 2 and 3 styles, never bold body text, so
  navigation, contents and accessibility work. One title, no skipped levels.
- **Type set on the styles, once.** The look plan's faces and scale on `Normal` and the heading
  styles: body 10.5 to 11 pt, line spacing about 1.15, 6 pt after paragraphs. Set the Latin and
  East Asian font attributes together, or Word falls back to another face. Set the language tag to
  `en-GB` on the styles so spell-check agrees with the text.
- **Page:** set the size explicitly (A4 portrait, 210 x 297 mm, unless asked otherwise) and margins of
  2.0 to 2.5 cm; never rely on a library default. A wide table gets its own landscape section: set
  the orientation and swap width and height yourself in python-docx; in Node pass portrait values
  and the orientation.
- **Tables are real.** A header row with a fill and bold text, flagged to repeat on each page
  (`w:tblHeader`), light grey borders, padded cells, numbers right-aligned. Set each cell's width and
  switch autofit off; in Node give the table `columnWidths` and every cell a `width`, all in DXA, with
  widths summing to the text width (percentages break in some viewers). Shade with `w:shd` value
  `clear` and a fill; `solid` renders black. Never use a table to lay out the page or to draw a rule:
  use a paragraph border.
- **Real lists.** The List Bullet and List Number styles (a `numbering` config in Node), never typed
  `-`, `1.` or a literal bullet character. Align a figure on the same line as a label with a tab
  stop, never runs of spaces.
- **Line and page breaks.** Separate paragraphs, not `\n`. `keep_with_next` on headings and
  `keep_together` on short blocks; a page break before a section is a paragraph property, not empty
  paragraphs. In Node a page break lives inside a paragraph.
- **Furniture.** Page numbers as "Page X of Y" fields in the footer, the title or reference in the
  header of a multi-page report, and the document title and author in the file properties.
- **Contents.** python-docx cannot calculate one and a field shows blank until Word updates it, so
  above about five pages write a plain contents list of the headings (no page numbers).
- **Images** (a logo, a chart saved as PNG by `matplotlib`) are placed at a set width and carry alt
  text. In Node an image run needs its `type`.
- **Special characters.** Use real subscript and superscript formatting, not Unicode digits.

## 4. The checks (mandatory)

A document that is correct in code can still look wrong. `render_pages` converts the file to PDF
and returns up to six page images per inspection, with the total page count and exact pages shown.
Default is pages 1–6. An optional `render_pages: {output, first, last}` selects the first inspection
of one declared output. Ranges are inclusive and contain at most six pages. Images judge layout, not small print.
`validate_ooxml` opens a `.docx` with its own library and counts paragraphs, tables and sections.

1. Pass `checks: ["render_pages", "validate_ooxml"]` for a `.docx`; `["render_pages"]` for a PDF.
2. Print a short outline from the program (headings, table count, placeholders found). The output
   comes back with the result; compare it with what you meant to build. A passing validation says
   the file opens, not that it is right.
3. Look at every returned page image, one at a time, and say to yourself what is on it before
   judging it. After writing the program you tend to see what you expect. Look for:
   - a heading stranded at the foot of a page, or a table cut to one orphan row;
   - words broken mid-word in narrow columns; text past the margin; an image over text; an empty
     last page;
   - inconsistent fonts, sizes or spacing; a heading that looks like body text;
   - a placeholder or blank left in by mistake.
4. Fix the cause in the program and run again. Look at the new images. Stop when the pages are
   clean; re-check only what you changed.
5. Follow each check result's `next_read` with `read` on the made file's `continuation_ref`, passing its `at` (the pages). This reads the already-made file at its exact version. Never rebuild or replace a file
   to inspect later pages. Continue until every page has actually been shown; report any unread pages.

## 5. PDFs with reportlab

- Use `platypus`: `SimpleDocTemplate`, `Paragraph`, `Table`, `Spacer`, `KeepTogether`, `Image`. Text
  wraps and pages break by themselves. Raw canvas drawing starts at the bottom left and nothing
  wraps; keep it for a certificate or a stamp.
- Style with `ParagraphStyle` from the look plan: leading about 1.3 times the size. A `Table`
  takes `repeatRows=1`, `colWidths` that fill the frame, and a `TableStyle` for the header fill,
  grid and alignment.
- Header and footer, with "Page X of Y", come from `onFirstPage` and `onLaterPages` callbacks. The
  total needs a second pass: build once to count, then build again.
- Set the title and author on the document, and add bookmarks to the headings of a long PDF.
- A `Paragraph` reads a small markup: escape `&`, `<` and `>`. Use its `<sub>` and `<super>` tags;
  the built-in fonts have no glyphs for Unicode sub or superscript digits and print black boxes.
- The built-in fonts (Helvetica, Times, Courier) cover `£` and Latin text only. For other characters
  or to match the Word faces, register a TrueType font found by globbing `/usr/share/fonts` (Liberation
  for Arial and Times, Carlito for Calibri, Caladea for Cambria, DejaVu for wide coverage).
- Reading or stamping with `pypdf`: pages iterate, and a stamp is a one-page PDF merged onto each page
  (`PdfWriter.add_page`).

## 6. Changing a file you made

- Open the current version and change it in place, as the same kind of file. Change what was asked and
  leave the rest, including styles.
- This is a plain re-make or edit of a file Beacon made, with no comments or tracked changes asked. Comments
  or tracked changes on any Word file, one Beacon made included, are not made here.

## 7. Conventions

- Dates as `21 October 2026` in prose and `21/10/2026` in tables, currency as `£12,450.00`, metric
  units, and a non-breaking space between a number and its unit. The Organisation's name as the
  person gives it.
- **Report:** title block (title, reference, date, author, revision), a short summary of the
  conclusion or decision needed, numbered sections, recommendations or actions in a table with
  owner and date, appendices last.
- **Letter:** sender, date, recipient, subject line, the point in the first paragraph, a clear
  request or next step, a sign-off with the sender's name.
- **Method statement or RAMS as a Word file:** document control (project, site, revision, date,
  author, approver), scope, the sequence of operations in numbered steps, a risk table (hazard, who
  is at risk, risk before, controls, residual risk, owner), plant, materials and people, emergency
  arrangements and a signature table. A RAMS the person wants to keep and edit in Saphion belongs
  in the RAMS product, not in a loose file.
- **Minutes and notes:** attendees, apologies, decisions, then actions with owner and due date.

Say in your reply what the document contains, its page count, how many pages you could view, and
each placeholder the person must complete.
