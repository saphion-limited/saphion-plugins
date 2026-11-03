---
name: "edit-pdf"
description: "Fill in a PDF form, join PDFs into one, take pages out of a PDF or turn its pages"
user-invocable: false
metadata:
  outcome: "A PDF the person supplied, changed and returned: a form's fields filled in, several PDFs joined in the order asked, chosen pages taken out as their own files, or chosen pages turned, every output read back and looked at."
  not-outcomes: |-
    Build a new PDF or Word document from nothing.
    Read, summarise or answer questions about a PDF without changing it.
    Edit the text or pictures on a PDF page, sign it, or open a password-protected or scanned one.
---
<!-- SURFACE_REASON: procedure prompt asset and helper scripts for the edit_pdf skill, loaded into the model's skill instructions for filling, merging, splitting and rotating PDFs the person supplied -->
# Work with PDFs

The person gave you one or more PDFs and wants a form filled in, files joined into one, some pages taken out, or pages turned the right
way up. The result must still be their PDF: the same pages, only what was asked changed, and you look at it before saying it is ready. Five
helper scripts do the file work with `pypdf` inside the file sandbox; you decide what goes in each field and which pages, and you look at the
pages. Building a PDF from nothing is not this skill's job.

Run a script from `execute_code` with `skill_script(skill="edit-pdf", script="scripts/<name>.py", args=[...], input_continuation_refs=[...])`. A file is named in `input_continuation_refs` by the `reference` you were shown it under; in `args` its path is `{input_1}` (the first file), `{input_2}` and so on. The sandbox has no network and no installs. Each script checks its own result by reading the written file back, and writes nothing if the check fails: the
refusal names what is wrong, so correct the request and run it again. A file changed arrives as a new version of the same file, under its own name (a file the person uploaded is never changed: the first edit makes one working copy beside it, and every later edit updates that copy); a joined or extracted file is a new file.

## 1. Know the file

Run `scripts/inspect_pdf.py` with `args: ["{input_1}", ...]`: one or several PDFs. It prints each file's page count, size and any page that is
already turned, and for a form each field as `name [type, page]` with what it accepts and the value it holds now. It writes no file. The run
shows you the last 2,000 characters of what the script printed; a form with many fields says where the list stopped: run it again with
`--from N` as the last two `args` to list the rest. Then `read` the PDF itself with `at` `1-6` and say what you see: a field's label is on the page, not in its name.

## 2. Fill a form

Only a fillable form can be filled (the fields inspect listed). A PDF with no fields is a plain page: tell the person it has nothing to fill,
and do not draw text onto it with a program.

1. Read the form's pages and decide, for each field, what the person's facts say belongs in it. A fact you do not have leaves its field empty and
   goes in your reply as a question, as does a tick you cannot support. A field the person did not mention stays as it is.
2. Run `scripts/fill_pdf_form.py` with `args: ["{input_1}", <values>]` and optionally a third, the output name (ending `.pdf`; leave it out and the form is saved under its own name,
   as a new version of itself). `values` is one JSON object of the field name exactly as inspect printed it to the value:

```json
{"Full name": "Ada Lovelace", "Date of birth": "10/12/1815", "Agree to terms": true, "Role": "Contractor", "Site": "South"}
```

- A text field takes a string written as it should read (a date in the form's own style; a number in quotes). A line break needs a multi-line field.
- A check box takes `true` or `false`. A group of radio buttons takes one of the states inspect showed. A choice takes the text of one option.
- A field that does not exist, a value a field does not accept, a read-only field, a value longer than the field allows: the run stops and
  names each one, with the nearest real field names. Fix them all and run again. A form that is also an XFA form is refused.
- It reads the written file back: each field you gave holds its value and every other field holds what it held. It then prints each value.

## 3. Join PDFs

Run `scripts/merge_pdf.py` with `args: [<output name>, "{input_1}", "{input_2}", ...]`: the files are joined whole, in the order
you list them. Decide the order from the person's words and from the files' contents, not from their names. Choosing only some pages of a file
is a split first and a merge after. Form fields come with their pages; fields with the same name in two forms become one field, which the
script says. The run prints which pages of the result came from which file.

## 4. Take pages out

Run `scripts/split_pdf.py` with `args: ["{input_1}", <groups>]`. Pages are numbered from 1 as the viewer counts them, whatever the page itself
prints (a roman-numbered preface still counts as page 1).

- `"3-5"` is one file of pages 3 to 5. `"2,5,9"` is one file of those pages in that order. `"7-"` runs to the last page.
- `"1-3;4-6;7-"` is three files, one for each group between the semicolons. `"each"` is one file per page.
- Files are named `<name>-pages-<pages>.pdf`. One run delivers at most 16 files: for a longer split ask for larger groups.
- A page that does not exist, a range that runs backwards or page 0 is refused, naming it and the file's page count.

## 5. Turn pages

Run `scripts/rotate_pdf.py` with `args: ["{input_1}", <degrees>, <pages>]` and optionally a fourth, the output name. Degrees are `90`, `180` or
`270` clockwise (`-90` is a quarter turn back). Pages are `"all"` or a list such as `"2"` or `"1-3,6"`. Look at the pages first to see which
way each needs to turn: a landscape scan shown sideways needs 90 or 270, and the render shows which. A turn adds to the page's rotation now,
so a page already turned 90 and given 90 is at 180. The pages' content is not changed: only how a viewer turns them.

## 6. Look at every output (mandatory)

The script's read-back proves the file holds the right values and pages; the render proves it looks right. `read` each delivered file by its
`continuation_ref` with `at` `1-6` (then `7-12`), say what is on each page and judge it:

- a filled form: every value sits in its box, readable, not cut off or on the wrong line, and a ticked box looks ticked;
- a merge: the pages come in the order you meant and none is missing or upside down;
- a split: the first and last page of each file are the ones asked for;
- a rotation: every page you turned is the right way up and the rest were not touched.

Fix the cause in the request, run again from the **original** file and look at the new output. Say what you did not look at.

## 7. Reply

Say which file is the result and what was done to it: the fields filled and with what (and the ones left empty because you were not given the
fact), the order of a merge, the pages in each file of a split, the pages turned and by how much. State how many pages you viewed. Say what the
skill did not do: a PDF with no fillable fields, a password-protected PDF, a scanned page it cannot read, flattening a form so it cannot be
edited, signing, and removing or adding text on a page.
