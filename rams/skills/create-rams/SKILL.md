---
name: "create-rams"
description: "Risk assessment and method statement"
metadata:
  outcome: "One Risk Assessment and Method Statement for one specific job the person wants produced: the RAMS record with its hazards and method steps, and its Word document from the Organisation's RAMS template."
  not-outcomes: |-
    Provide an ordinary safety briefing, checklist, explanation or guidance.
    Draft ordinary chat content merely because its subject overlaps workplace safety.
---
<!-- SURFACE_REASON: procedure prompt asset for the create_rams skill, loaded into the model's skill instructions for making a RAMS record and its Word document from the Organisation's own template -->
# Create a RAMS

You are making a risk assessment and method statement (RAMS) for one real job, for people who will
read it, sign it and work to it on site. A RAMS is a record on the RAMS board: the job's facts, its
hazards with their controls and ratings, and its method steps in order. The Organisation's published
RAMS template turns that record into a Word document with a PDF. You make the record with the record
tools, write the template's written sections yourself, then call `document_generate`. No other tool
makes this document, and you never build a RAMS file from scratch with `file_build`.

## 1. Gather what is known

Take everything from the request, the files and the conversation before asking anything: the
project and site, the activity, where on site, start and end dates, who prepares it and who does
the work. In a Project conversation the RAMS is filed in that Project by Saphion; never name the
Project yourself. Elsewhere, if the person named a Project, find it with `find` (kind `any`) and file the
RAMS under it. The site address belongs to the Project, so do not copy it into the RAMS.

Ask only for what you cannot responsibly do without: which job, and the facts that make the hazards
differ (height, location, who else is on site, what is being worked on). Ask once, in one short
message, and offer a stated assumption for each gap so a one-word answer is enough. A fact that is
still unknown goes into your reply as something to confirm, not into the document as if it were true.

## 2. Create the RAMS record

Call `record_fields` for `rams` to see its fields, its Status choices and
how a linked field is written. Find the RAMS board's record set with `find`
(kind `record`, `record_class` `rams`), then call `record_change` with that record set's `record_set_continuation_ref`
and a `change` of `act` `create`, `resource_class: rams` and `values`: name (a concise title for the job, such as "Roof edge protection,
Unit 4"), project (leave it out in a Project conversation), activity, location (where on site), start_date, end_date, prepared_by, people and
ppe. Leave status alone: it begins as Draft. Change a record you already made with
`record_change` and a `change` of `act` `update`, using the reference its read issued. Change only what you were asked
to change.

## 3. Choose the hazards

Read the Hazard library: `find` with kind `record` and `record_class` `hazard`, paging until
you have all of it. Choose the hazards that genuinely apply to this activity and site, and say in
your reply which you chose and why. Do not add a library hazard merely because it exists.

For each hazard, create the RAMS's own copy: `record_change`, `act` `create`, with
`resource_class: rams_hazard` and the library hazard's hazard, harmed, controls, likelihood,
severity, residual_likelihood and residual_severity, and `library_hazard` set to the library
record. It is a copy, never a live link, so a later edit to the library cannot change a signed
RAMS. Then change the RAMS's `hazards` field to hold the new rows, written as the class read
showed.

Where the library lacks a hazard the job really has, create a new `rams_hazard` row with
`library_hazard` empty and a complete assessment of its own. Do not add it to the Hazard library;
that is the Organisation's to curate. Adjust a copied row to the job when the job differs (a
specific control, a lower likelihood once a control is in place), and keep the library's wording
where it already fits.

For every row:
- **Who might be harmed**, from the choices the class offers.
- **Controls** that are specific and doable on this site: what is done, by whom, with what.
  "Exclusion zone of 2 m marked with barriers and signed" is a control; "work safely" is not.
- **Likelihood and severity** as whole stars in the library's own scale (the field's rating, one
  to five unless the class read says otherwise), judged before controls. Then the **residual**
  likelihood and severity once the controls are in place. Risk and residual ratings are
  calculated; never write them. A residual rating is never higher than the rating before controls.

## 4. Write the method steps

Create one `rams_step` row per step with `record_change` (`act` `create`): `step` (a short imperative
title) and `details` (who does what, in what order, with which equipment, and the hold points where
work stops until something is checked). Create them in working order, then set the RAMS's `steps`
field to the rows in that order. A method runs from access and set-up, through the work and its
checks, to clear-up and handover; keep each step to one stage of the job. Set the RAMS's `ppe`
from the controls your steps and hazards actually rely on.

## 5. Write the document's sections

The template may declare written sections, each with an instruction. You already know them: the
Organisation map at the start of the turn lists the `rams` record type's published `templates`, each
with its `ai_sections` (the section's name and its instruction). Do not call `document_generate` to
find them out. If the `rams` record type has no `templates`, none is published: go straight to
step 6 and say so there. If it has a template with no `ai_sections`, there is nothing to write. If
it has more than one, use the one the person named.

Write each section as the instruction asks, from the record and the request, to the standard a
competent health and safety professional would sign:
- **Specific to this site and activity.** A reader should be able to tell which job it is without
  the title. No boilerplate paragraphs that would fit any RAMS.
- **Only what you know.** Where a site fact, name, date, item of plant, emergency arrangement or
  training is unconfirmed, write "To be confirmed before work starts" and
  list it in your reply.
- **Law only when certain and relevant.** Cite UK legislation only where it applies to this work
  and you are sure of the reference: the Health and Safety at Work etc. Act 1974, the Management of
  Health and Safety at Work Regulations 1999, the Construction (Design and Management) Regulations
  2015, the Work at Height Regulations 2005, COSHH, and so on. If you are unsure, state the duty in
  plain words and leave the citation out.
- **Consistent with the rows.** A section must not contradict the hazards, controls or steps.
- **Plain text**, blank lines between paragraphs, in the Organisation's voice.

## 6. Make the document

Call `document_generate` with `resource_class: rams`, the `record_id`, the `record_set_id` and
`sections`, keyed by the names in that template's `ai_sections`, and its `template` (`template_id`).
When the board has several published templates (a risk assessment and a method statement), make each
one, unless the person asked for only one. The Word file and its PDF are kept on the record; making it
again replaces them and keeps the one before.

If the map shows no published RAMS template, say so plainly: "Upload a RAMS template in Templates
first." Do not offer a substitute document, and do not build one with another tool. If the call is
refused for a missing section, value or right, say what it named and fix what is yours to fix.

## 7. Tell the person

Say what was made, briefly: the RAMS by its name, the hazards you chose and any you added, the
number of steps, and what needs confirming before work starts. Make clear the document is a draft
for their review. Reviewed and Signed off are the person's to set in the RAMS's Status, and the
signing itself happens in the Word document; you set neither and never describe the RAMS as signed
off or approved.

If you were asked for an example, label it as an example and make its details credible but
unmistakably not a real job. Never present example facts as real.
