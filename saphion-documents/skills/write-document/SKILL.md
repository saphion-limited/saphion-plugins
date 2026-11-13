---
name: "write-document"
description: "A document that lives inside Saphion: the default when someone asks for a document and names no file format. For a document: give document_change create the whole content when you have it, else an outline, alone, before any search."
user-invocable: false
metadata:
  outcome: "A document that lives in Saphion, written or changed: outlined first, filled one section at a time, edited in place without overwriting the person's own changes, and answered in its comment threads."
  not-outcomes: |-
    Answer in the conversation without making a document.
    Make a spreadsheet, a presentation or an app.
  hand-over-make-document: "A Word or PDF file named, tracked changes wanted, or a .docx to change or use as a template: the make-document skill builds the file. Needing to send, attach or print a document is no reason to pick Word."
---
<!-- SURFACE_REASON: procedure prompt asset for the write_document skill, loaded into the model's skill instructions for writing and editing a document that lives in Saphion -->
# Write a Saphion document

For a document that lives in Saphion beside the chat, something the person will keep, share or return to; a short answer belongs in the chat. Its `title` is the Document's name and is required; the owner and dates under it are drawn by the app, so never write them or the title into the body.

When you already have the content (a short document, or one the person dictated), make it in one call: `document_change` with the act `create` and the whole content as `markdown`, in the blocks the tool lists. When the content needs research or is long, the first call of the turn is `create` with an `outline`, alone, before any search or planning: it opens the document at once. Then fill one section per call.

`document_guide` (its index first; editing, comments and diagram are its other topics) holds what the tool's list does not: images, widgets, mentions and links, dates, dropdowns, colours, diagrams and the craft of which block fits which content. Read it before using one of those.