---
name: "prepare-tender-response"
description: "From a tender pack"
metadata:
  outcome: "Prepare or continue a Bid's source-grounded Tender response for human review and preparation-document export."
  not-outcomes: |-
    Answer a general procurement question or summarise a document without preparing a response.
    Submit a bid to a buyer or approve answers on the person's behalf.
    A Word or PDF document that is not a Tender response, or a document that lives in Saphion.
---
<!-- SURFACE_REASON: the shipped skill that prepares a Bid's one tender response Document from its tender pack -->
# Prepare a tender response

Work on the selected Bid's one response Document. The Bid owns the client, deadline,
status and commercial outcome. Read it through bid_response_read; open its existing
response with read. Never create a second response or copy its commercial facts
into another record.

Read every selected native file at its issued exact version with `read`.
Account for unreadable or missing material plainly. A question is something the bidder
actually answers; dates, marking, definitions and submission mechanics are guidance,
not extra questions. Preserve genuine questions in the buyer's order and retain the
source wording, numbering, limits, weighting, applicability, declarations, repeated
rows and separate required artefacts. Choose issued passage addresses; code copies
source statements. Do not retype quotes, infer quantities, turn page limits into words,
or settle conflicting source statements silently.

Create the source questionnaire through document_change with the act from_questionnaire, with an editable
Overview first. Its business context binds the Bid, Project, selected pack and one
response identity. The Document holds the questions and answers; there is no separate
questionnaire or drafting record.

Draft the Overview and narrative answers directly into the Document through read
and document_change (act edit; document_guide, topics index and editing, says how). Use relevant current Project material, the files the person can open,
feedback and guidance. Record actual citations beside claims and make missing evidence,
assumptions and contradictory evidence explicit. Keep within stated limits; supplier facts, signatures, prices and commercial figures come only from
the evidence. Typed declarations, choices,
repeated rows and supplied artefacts use the Document's native field controls. Keep source
questions fixed. Preserve the person's words; change an existing answer only when asked.

The person marks the exact current Document version Reviewed. Any edit makes it a draft
again. The skill never marks it Reviewed or treats an export as buyer submission. When
asked, export through the Document's own controls: Word and PDF of the saved response,
or the question spreadsheet, with explicit gaps and Draft marking until reviewed. Name
only files the owner actually produced. Submission and outcome remain on the Bid.
