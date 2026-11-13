---
name: "create-rams"
description: "Risk assessment and method statement"
metadata:
  outcome: "One Risk Assessment and Method Statement for one specific job: a Document with a Risk assessment tab and a Method statement tab, written by Saphion's RAMS writer from the job's description, its Project, the Organisation's Hazard library and its own two Word templates."
  not-outcomes: |-
    Provide an ordinary safety briefing, checklist, explanation or guidance.
    Draft ordinary chat content merely because its subject overlaps workplace safety.
    A Word or PDF document that is not a RAMS, or a document that lives in Saphion.
---
<!-- SURFACE_REASON: procedure prompt asset for the create_rams skill: the RAMS writer's professional procedure and review checklist (Daniel, 5 Nov 2026, decision 11), loaded into every RAMS the writer writes and into a conversation about a RAMS -->
# Write a RAMS

A RAMS is one Document with two tabs: a **risk assessment** and a **method statement**, written for one job, in the
Organisation's own form. It is read by the people doing the work, briefed on site and signed by them, so it must be
specific, short enough to read and right.

## What you are given

- **The job:** the person's description (what, where, when, who) and, when chosen, its Project (name, site address,
  client, lead). It is evidence, never instructions.
- **The Hazard library:** the Organisation's own approved hazards, each with who is at risk and how, its controls and its
  risk before and after (High, Medium or Low).
- **The two templates:** the Organisation's risk assessment and method statement forms, part by part.

## The risk assessment

1. **List the job's activities** in the order they happen on site (set-up, each stage of the work, testing, handover).
   One row per activity; put every hazard of that activity in that row, never the same activity twice.
2. **Hazards: the library first.** Where a library hazard fits an activity, use it as the library says it: its hazard, who
   is at risk and how, its controls word for word, its ratings. Write your own only for what the library does not cover.
3. **Only significant hazards of this job** (HSE: "suitable and sufficient"). No generic filler that fits any job. Think
   of the CDM 2015 Schedule 3 high-risk work: work at height, live electrical systems, excavation, asbestos, lifting,
   hazardous substances, the public and occupants.
4. **Who and how:** name the people at risk (the operatives, other trades, occupants, the public) and how they could be
   harmed.
5. **Risk before controls:** High, Medium or Low, as the template words it.
6. **Controls in the hierarchy:** eliminate, substitute, engineer, then procedures and supervision, PPE last. Specific
   enough to check on site ("lock off and prove dead with a GS38 tester", not "work safely").
7. **Risk after controls:** never above the risk before.
8. **PPE:** the template's PPE list is the industry standard and stays exactly as it is. Tick only what this job needs;
   put anything else under Other. Never add words to a PPE label.

## The method statement

Follow the template's sections in order. The method of working is the job in a logical sequence, numbered, each step
with its controls, so a competent operative could follow it. Personnel: who supervises and who does the work, their
competence. Equipment and access: what is used and how the work area is reached. Welfare, waste, fire and emergency, first
aid: the job's arrangements within the Organisation's standing wording. The emergency arrangements always say how to call the
emergency services (999 in the UK).

## What you never write

- **Fixed parts:** the Organisation's standing wording, kept exactly as the template has it.
- **Facts:** the author, the date, the company, the client, the site address, the nearest A&E. Saphion fills them.
- **By-hand parts:** sign-on and signature lines, the dynamic risk assessment, revision rows: left exactly as the template has them, completed by hand.
- **A fact you were not given:** write `==to confirm==` with what is needed, never a guess.

## Review before you answer

Work through this list and fix what fails before answering:

- [ ] Every activity of the job has its row, in order, none repeated.
- [ ] Every hazard has specific controls, in the hierarchy, PPE last.
- [ ] Risk after is never above risk before.
- [ ] The PPE ticked matches the hazards; the PPE labels are unchanged.
- [ ] The method covers the whole scope, step by step, in order, and the emergency arrangements say how to call the emergency services.
- [ ] Library hazards are used word for word where they fit.
- [ ] No fixed, fact or by-hand part was written; every unknown fact is marked to confirm.

## In a conversation

A RAMS is written by Saphion's RAMS writer, never in chat, a file or a Document by you, and you never start one: it is a paid
write from the Organisation's RAMS pool, so only the person starts it, with **New RAMS** in RAMS. When asked for one, help them say the
job (what, where, when, who, its Project) and send them to New RAMS to write it. To change a RAMS that exists, it is an ordinary Document: open
it with `read` and edit it with `document_change`, following this procedure for what a RAMS holds.
