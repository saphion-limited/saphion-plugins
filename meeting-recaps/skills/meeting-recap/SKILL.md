---
name: "meeting-recap"
description: "Meeting recap: a short summary, decisions, actions and notes by topic, for any meeting without a more specific style."
metadata:
  recap-style: "true"
  outcome: "A recap of one meeting from its transcript or notes: what it was for and what came of it, its decisions and agreed actions, and what was discussed under each topic."
  not-outcomes: |-
    Formal board or committee minutes for approval and signature.
    A one-to-one, project update, client meeting, sales call or interview record, which have their own styles.
    A verbatim transcript, or a summary of a document that is not a meeting.
---
<!-- SURFACE_REASON: procedure prompt asset for the meeting_recap skill, Saphion's default meeting recap style, loaded into the recap of a Notetaker meeting and into a conversation that asks for a meeting recap -->
# Meeting recap

The default recap for any meeting without a more specific style: an internal meeting, a call, a catch-up. Someone who missed the meeting should know in one minute
what it was for, what was decided and who is doing what, and be able to find what was said on any topic.

## Sections, in this order

1. **Summary.** Two to five sentences: what the meeting was for and what came of it. Lead with the outcome, not the chronology.
2. **One section per topic**, in the order the topics came up, each headed with the topic's name (the agenda item's name where there was an
   agenda). Under each: what was discussed and where it landed, in a short paragraph or a few bullets; its decisions; its agreed actions.
3. **Open questions.** Anything raised and not settled, one line each, said as the question that is still open. Leave the section out when
   there are none.

## How it reads

- Plain, neutral third person, past tense. Names where they help the reader follow who said or agreed what; never a turn-by-turn account.
- Short. A topic gets the words its substance needs: one line for a quick update, a paragraph for a real discussion. Merge a topic that
  came up twice into one section; leave out a topic with nothing of substance.
- Bold the few words a reader scanning the page must not miss (a changed date, a figure agreed). Numbered lists for steps or options in
  order, bullets for everything else.
- A decision is what the meeting settled, in one line, with its reason when one was given.
- An action is a commitment someone made or the meeting agreed, starting with a verb; its owner only if a person was named, its date only if
  a time was said.
- Keep disagreement visible: if people disagreed and nothing was settled, say so under the topic and list it under Open questions.

## Leave out

Small talk, joining and sound checks, side conversations, jokes, and anything not said in the meeting. Anything said to be off the record, a
private session or legal advice: note only that it was discussed, never its content. When Saphion gives the meeting's facts (title, date,
times, who joined), they are shown above the recap: never write your own attendance list.

## Example outline

```
Summary
The weekly marketing meeting reviewed the website relaunch and the October budget. The relaunch moves to **17 November**; the freelance
designer's contract is still open.

Website relaunch
The agency's final pages arrived a week late, so the launch moves with them. Decision: launch on 17 November.

Freelance designer
The contract terms are still with finance. Action: chase finance for the contract.

Open questions
- Whether the October budget covers the extra week of agency time.
```
