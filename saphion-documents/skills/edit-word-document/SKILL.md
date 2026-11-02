---
name: "edit-word-document"
description: "Change a Word (.docx) file the person supplied: a clause, comments or tracked changes, with everything else left as it was"
metadata:
  outcome: "A Word (.docx) file the person supplied, changed and returned: a clause reworded, comments added, changes tracked as a redline, with its styles, its own comments and its existing tracked changes intact."
  not-outcomes: |-
    Build a new Word document or PDF from nothing.
    Summarise, read or answer questions about a Word file without changing it.
    Edit a document that lives inside Saphion.
    Change a Word file Beacon made itself without comments or tracked changes, which is changed in place as the file it is.
---
<!-- SURFACE_REASON: procedure prompt asset for the edit_word_document skill, loaded into the model's skill instructions for faithful edits to a supplied Word file -->
# Edit a Word document

You are changing a Word file the person already has: an attachment, an Organisation or Project file, or one Beacon made.
They want a clause changed (in a file Beacon did not make) or, in any of them, comments added or the changes tracked as a redline. You do not rebuild the document and you do not
write a program for it. One helper script makes the edits and checks its own result before anything is saved. It leaves every part you do not
name exactly as it was: styles, numbering, headers and footers, pictures, and the person's own comments and tracked changes.

## 1. Read first, then decide the edits

- Read the file to find the exact words and to understand the clause. The read shows the text; it can miss words that sit inside a tracked
  insertion and it shows no comments. The script matches against the document as Word shows it now (deleted words gone, inserted words
  there), so when your quoted words are not found its refusal prints the nearest paragraphs as they really read. Quote from that.
- Make only the edits the person asked for. Do not tidy wording, fix formatting or "improve" a clause they did not mention.
- Decide **tracked** for every change that alters words. Track it when the person asks for a redline, tracked changes or suggestions, or when
  they are reviewing a document that already carries tracked changes. Make it plainly only when they ask for the change to be made without
  marks. When it is unclear, track it: a tracked change can be rejected, a plain one cannot.

## 2. Run the script

Call `run_skill_script` with this skill's name, `script_name` `scripts/word_edit.py` and two `args`: the file's reference (the one you were
shown it under) and the request as one JSON text.

```json
{"author": "Beacon", "edits": [
  {"op": "replace", "find": "within thirty (30) days of receipt", "text": "within forty-five (45) days of receipt", "tracked": true,
   "comment": "Aligned with the Customer's purchasing terms."},
  {"op": "comment", "find": "Northbridge Components Ltd", "text": "Please confirm the registered address."},
  {"op": "insert_after", "find": "Nothing in this Agreement limits liability", "text": "Each party shall maintain adequate insurance.", "tracked": true}
]}
```

| Edit | Fields | What it does |
|---|---|---|
| `replace` | `find`, `text`, `tracked`; optional `comment`, `occurrence` | The quoted words become `text` (empty `text` deletes them). Only the words that differ are changed, so a redline shows the change and not the whole clause, and unchanged words keep their own formatting. `comment` explains the change and sits on the changed words. |
| `comment` | `find`, `text`; optional `occurrence` | A comment tied to those words. No words change. |
| `insert_after` | `find`, `text`, `tracked`; optional `comment`, `occurrence` | A new paragraph after the paragraph holding `find`, in its style and list numbering (a new clause after clause 3.1). A line break in `text` makes several paragraphs. |

- `find` is a few words inside one paragraph that appear once. If they appear in more places the run is refused and lists them: quote more
  words, or give `occurrence`. Curly and straight quotes match each other.
- `author` is who the comments and changes are from. Leave it out (Beacon) unless the person says whose changes these are.
- Write a comment as a reviewer would: the reason, or the question, in a sentence or two.
- All the edits go in one run, in order. Edits are matched against the document as the earlier edits left it, so quote the new words of an earlier
  edit, never the old ones. If any edit is refused or any check fails, nothing is saved: read the message, correct the request and run again. Do not
  fall back to rebuilding the file with a program.
- A tracked edit may remove words inside someone else's tracked insertion (Word nests the deletion inside it). An untracked edit never does.

## 3. After the run

- The result lists each edit and what the script itself checked: that the file opens, that every earlier comment and tracked change is still
  there, and that every paragraph you did not edit reads as before. The edited file arrives as its own card, named after the original with
  `-edited`; the original is untouched.
- Say in your reply what you changed (each edit in plain words), how many comments and tracked changes you added and under what name, and the file
  name. Read the delivered file once if you need to confirm the new wording, and say what you did and did not look at: you have not seen the pages
  unless you did.
- What this script does not reach, and you must say when the request touches it: headers, footers, footnotes and text boxes; words that run
  across two paragraphs; replies inside a comment thread; the text of a field or content control (it can be commented on, not rewritten); and any
  file that is not an ordinary .docx (an older .doc, a template or a macro-enabled file is refused).
