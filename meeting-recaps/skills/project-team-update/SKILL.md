---
name: "project-team-update"
description: "Project and team update: status against plan, progress and blockers by workstream or person, risks and issues, and changes to scope, time or budget, for stand-ups, team syncs and project status meetings."
metadata:
  recap-style: "true"
  outcome: "A record of one project or team update meeting from its transcript or notes: overall status where it was said, progress and blockers by workstream or person, risks and issues with the agreed response, changes to scope, time or budget, decisions and actions."
  not-outcomes: |-
    A client meeting, formal board minutes or a one-to-one record, which have their own styles.
    A project plan, a risk register or a formal change request.
    A judgement of whether the project is on track beyond what the meeting said.
---
<!-- SURFACE_REASON: procedure prompt asset for the project and team update skill, the project and team update recap style, loaded into the recap of a Notetaker meeting and into a conversation that asks for a project or team update record -->
# Project and team update

A recap of a stand-up, team sync or project status meeting: where the work stands against the plan, who is doing what, what is in the way, and
what changed. Someone who missed it should see in a minute whether the work is on track, what is blocked and what they are asked to do.

## Sections, in this order

Leave out any section the meeting said nothing about.

1. **Overall status.** Only if the meeting said how the project or team is doing (on track, behind, at risk) and why, in its words. Never
   invent a red, amber or green rating, a percentage or a status nobody gave.
2. **Previous actions, done or carried.** Which earlier actions were reported done, and which are carried forward and why.
3. **Progress by workstream or person.** For each workstream or person as the meeting went: what is **done**, what is **next**, what is
   **blocked**. For a stand-up this is the whole recap, three lines a person at most.
4. **Blockers and help needed.** What is in the way, who asked for what, and who offered it.
5. **Risks and issues with the agreed response.** Each risk or issue raised, whether it is a risk (may happen) or an issue (has happened),
   and what was agreed to deal with it. A risk is never recorded as closed unless the meeting closed it.
6. **Changes to scope, time or budget.** Any change raised, who raised it and whether it was agreed. Record what was said; never value or
   judge it.
7. **Decisions.** One section holding every decision the meeting settled, each in one line with its reason when given. It has no text of
   its own, only the decisions.
8. **Actions.** One section holding every action agreed. It has no text of its own, only the actions.
9. **To confirm in writing.** Only when a change was agreed with a client or supplier: each such change, one line, saying what it is. Open
   the section with the line: *This record is not a confirmation of these points. Each item below should be confirmed in writing.* This
   list suggests; it never decides whether something is a formal change.
10. **Next meeting**, if said.

## How it reads

- Facts, not commentary: what was reported, agreed or asked for. No judgement of anyone's performance, and no adjectives about the work.
- Name the person or workstream for each point; a status with no one attached is not useful.
- Where people disagreed on a fact or a priority, record each position, attributed, and that it was not agreed. Questions still open stay
  visible as questions.
- Short bullets under each heading; bold a changed date, an agreed figure or a blocker.
- An action is a commitment someone made or the meeting agreed, starting with a verb; its owner only if a person was named, its date only if
  a time was said.

## Leave out

Small talk and sound checks, side conversations, speculation nobody agreed, and anything not said in the meeting. Contract clauses and
notice periods: this style does not interpret contracts. Anything said to be off the record, privileged legal advice or a private session:
note only that it was discussed, never its content. When Saphion gives the meeting's facts (title, date, times, who joined), they are shown
above the recap: never write your own attendance list.

## Example outline

```
Overall status
Behind on the data migration by about a week, on track elsewhere, as Priya put it.
Previous actions, done or carried
Two closed; the test plan is carried forward, awaiting sign-off.
Progress by workstream or person
- Migration (Priya): **done** extract and mapping; **next** load tests; **blocked** waiting for the supplier's access keys.
- Reporting (Tom): **done** the weekly pack; **next** the new filters.
Risks and issues with the agreed response
- Issue: the supplier's keys are late. Agreed to escalate to the supplier's account manager.
Changes to scope, time or budget
The go-live date moves from 12 to 19 December. Agreed by the project sponsor.
To confirm in writing
This record is not a confirmation of these points. …
- The go-live date change, agreed with the supplier.
```
