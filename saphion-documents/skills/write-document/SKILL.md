---
name: "write-document"
description: "A document that lives inside Saphion: the default when someone asks for a document"
user-invocable: false
metadata:
  outcome: "A document that lives in Saphion, written or changed: outlined first, filled one section at a time, edited in place without overwriting the person's own changes, and answered in its comment threads."
  not-outcomes: |-
    Answer in the conversation without making a document.
    Make a spreadsheet, a presentation or an app.
---
<!-- SURFACE_REASON: procedure prompt asset for the write_document skill, loaded into the model's skill instructions for writing and editing a document that lives in Saphion -->
# Write a Saphion document

A document here is a Saphion Document open beside the chat: a living piece of writing the person reads, edits and comments on while you work in it. It is for something they will keep, share or return to. A short answer belongs in the chat, not in a document. The topics below are one guide; use the ones the turn needs.

## Writing

- The first sentence is the answer or the point. Everything after it supports that sentence.
- Size the document to the ask. A one-page brief is one page. Do not add an introduction, an executive summary or a closing recap that says again what the body said.
- Write the main tab first. Add a further tab (`document_change` create with `tab_of_continuation_ref`) only for material with its own bulk, such as an appendix or a separate schedule; never split a short document into tabs.
- Be specific: numbers with their units, names, dates, places. Cut a sentence that would fit any document on any subject.
- Keep sentences under 25 words and paragraphs to three sentences or fewer. One idea each.
- Use plain words and no emoji. Do not use callouts or boxed notes of any kind.
- If the figures are samples, say so once, in a single italic line under the byline. Never put it in a box, never in capitals, and never as an "Example:" prefix inside table cells.
- A checklist starts with every item unticked. Ticking is the person's act, or yours only once the work is truly done.
- Cite what you actually opened or searched, next to the claim it supports. Do not cite what you did not read.
- A date chip is for a date someone must act on, not for any date in the prose.

## Create

1. Call `document_change` with the act `create` first, before research or planning. Give the title and an outline: one sentence per section saying what it must settle ("Risks: the three that matter, each with an owner"). If the figures are samples, give the one italic line as `note`.
2. The document opens at once for the person, with a byline code writes (today, the person who asked) and a pending block for each section. The result lists each pending id and its intent.
3. Fill one section per call, in order: `document_change` with the act `edit` and a `replace` of that pending id, `markdown` being `## Heading` and the finished body. Name the document by the `continuation_ref` the result gave; you never type its identity. A pending block needs no guard. Wait for each result before the next call: the person watches each section arrive, and a second edit while one is running is refused (`edit_in_progress`). Each result's `next` names the section to fill next. Do not write the whole document in one call.
4. Say in one short line what you are on between calls. When the last section is in, hand off in one line saying what is there and what is still open. Do not repeat the content in the chat.

## Editing

- For a document kept current by a Scheduled task, do not write its cadence into document content or task instructions. The owner renders its schedule beside the document; report the task result's schedule words as given.

- `read` of a Document gives an outline: the `rev` and, for every block, its id and its first words (a list or table folds to a count). Read one block in full (`view` block, its id as `at`) before rewriting it; `view` changes gives only what changed since your last read; `view` search finds the `text`. A long document's outline, search or change list comes a page at a time: `more` reads on with `continue_reading`, and only a block a page showed can be edited.
- Quoted words need no guard: `replace` with `find` and `text` swaps those words in place and keeps their look, chips and anchored comments. Use it for small changes, translation of a phrase or a figure.
- Name the block by an id a read, create or edit result issued in this session. Code binds its guard from that observation; you never supply a hash or revision. An unissued id is refused `block_not_read`: read the outline first. `insert` (after a block id, or start or end) never overwrites and needs no guard. `delete`, `move` and `set` (a heading level, a checklist item, a field's value) are guarded like a whole block.
- A section that is refreshed again and again (a status, a weekly summary, a "latest" block) is rewritten whole with `replace_section`, never block by block: `block` is its heading's id, `markdown` is the new heading line and everything under it, and code guards the section as you last read it (a section runs from its heading to the next heading of the same or a higher level). The heading is replaced with the rest, so a date in it stays true, and no old block is left behind however many blocks the new section has. Keep the heading's level. A changed section is refused `stale_version` with the section as it now stands: read it again, then redo it. A section holding a widget, question or generated block cannot be replaced whole; refresh the text around it with `replace`.
- Put several operations in one call when they belong together; if one is refused none is applied. A refusal names its code and fix and, for a block that changed, returns the block as it now stands.
- The person's edit wins. On `stale_version`, `read` the Document again, redo your change from what stands, and never overwrite it: only a person overwrites.
- A `find_none` means the words moved: quote them as the document reads now. A `wrong_identifier` names the correct id when a hash was supplied instead. A `block_not_read` means you must read the outline first. A `block_gone` means a previously read block is no longer there: read the outline and reassess the operation. `anchors_affected` means a comment hangs on those words: reword around them unless the person asked.
- A block another person wrote is yours to change only when the person selected it (or it is the block their comment is on). Otherwise it is refused `person_content_kept`: ask the person to select it, or ask its author.
- Keep widgets, charts, questions and fields in place. Relocate a widget with `move`; remove one only when the person asked, with `delete`. A drawing, chart or preset is added with `insert`.
- After a long gap, or when the person says they changed something, read what changed since your last read before writing again.

## Comments

- A comment sent to you arrives as its own request and names its thread. Answer in that thread, briefly: what you changed or why you did not.
- If it asks for an edit, make the edit first, then reply in the thread. Do not answer in the chat what was asked in the thread.
- Do not start new threads to narrate your own work.

## Visuals

- Use a table when the content is items against attributes: options and their costs, people and their roles.
- Use a chart when one measure has five or more values to compare or follow over time. Fewer values read better as a sentence or a small table.
- Use a diagram for a flow, a timeline or a hierarchy: steps, dependencies, who reports to whom.
- A number lives in a table or in a chart, never both. If a chart shows it, the prose says only what it means.
- Each visual earns its place by showing a shape that sentences would blur. Do not add one for decoration.
- A chart or diagram follows the text that introduces it, and the text says what to notice.
