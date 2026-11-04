---
name: "write-document"
description: "A document that lives inside Saphion: the default when someone asks for a document and names no file format. For a document: call document_change create first, alone, before any search; then read document_guide."
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

For a document that lives in Saphion beside the chat, something the person will keep, share or return to; a short answer belongs in the chat. The first call of the turn is `document_change` with the act `create`, alone, before any search or planning: it opens the document at once.

Then read `document_guide` (its index first; editing, comments and diagram are its other topics) and fill one section per call.
