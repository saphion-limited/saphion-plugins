---
name: "deep-research"
description: "Research a topic across many sources (rules, markets, options, trends, what has been published) and deliver a cited report that takes a position"
metadata:
  outcome: "A question researched properly: broken into parts, each worked through several searches and the pages behind them, and answered in a Word report that opens with the answer, takes a position, cites a source that opens its real page for every finding and comes with a downloadable bundle of the report and its source list; or a plain statement that the sources found were not good enough, with nothing invented."
  not-outcomes: |-
    Answer a single fact, date or figure that one search settles.
    Summarise or answer questions about a file the person supplied.
    Write a document from what the person already told you, with no research.
    A Word document that is not the report of researched sources.
---
<!-- SURFACE_REASON: procedure prompt asset and helper script for the research_report skill, loaded into the model's skill instructions for researching a question across sources and delivering a cited report -->
# Deep research

The person wants a question properly researched: what the rules require, how options compare, where a market or a subject stands. They want
what a good analyst would hand them: the answer first, a position they can act on, and every claim traceable to a source you actually read.
Depth comes from working each part of the question in turn, and from reading pages rather than search passages. One helper script checks the
citations and writes the report and its bundle. It runs in the file sandbox, which has no network, so everything you learn comes through
`web_search`, `web_read` and Saphion's own reads. A single fact (one date, one figure) is answered
with `web_search` and `depth` `lookup`, not this skill.

## 1. Ask only what would change the research

Ask, with `ask`, when the answer would differ by something unsaid: the jurisdiction, the period, a name or an acronym that could mean two
things. Otherwise carry on and state the scope you assumed in the report. If this chat already holds research on the subject, research only
what this request adds or what may have changed, and write a report that stands on its own.

## 2. Break the question down

Restate the question in one sentence, then split it into parts that do not overlap and together answer it. How many follows from its shape:

| The question | Parts | For example |
|---|---|---|
| A focused subject with a few angles | 3 | a rule: what it requires, who it binds, how it is enforced |
| Several criteria to weigh | 4 | comparing products: price, features, what they connect to, what customers say |
| Several places, bodies or periods | 5 | a regulation across the UK, the EU and the US, and what industry does about it |
| A long list to cover in full | 6 or more | a measure region by region, grouped |

Three is a sound default. For each part write the questions it must answer and what would count as a good source: the regulator or statute,
the publisher of the standard, the Organisation's own records for something about it; a trade body or a recognised expert next; a vendor only
for what the vendor itself does. Keep the parts in `todos`, and say what you are researching as you go, naming the part, not your method.

## 3. Work each part until it is answered

Take the parts one after another, finishing each before the next, and repeat this loop within each:

1. Say to yourself what is still unknown for this part.
2. Search for it. Run every search you can in one response, side by side. Short queries find more than long ones: a few words, as the best
   source would put them. Never repeat a query: reword it, and if results are thin, widen it. Use `domains` for official sites (`gov.uk`, the
   regulator), `published_from` when recency matters, and `country`. UK law is searched with `domains` `legislation.gov.uk`, then the provision itself is read
   with `web_read`, not a website's account of it. What the Organisation holds (its records, files, documents) is `find` and `read`: a question about the
   person's own work is answered from their own material first.
3. Read the pages behind the best results with `web_read`, up to five a call, asking it this part's question. A search passage is easily
   taken out of context, so one is enough only for a plain fact that it states in full. A summary leads you to the original it cites: find that and read it.
4. Stop this part when its questions are answered, or when new results only repeat what you have.

**Your allowance.** A turn holds about 40 rounds of tool calls, shared by the whole report. Spend about four to six on each part, more when a
part is the crux, and always keep five for writing and for correcting the report. When rounds run short, stop researching and write
with what you have, saying what stayed open. An unfinished search delivers nothing; a report with a stated gap is still useful.

**Keep notes after each part**, so that nothing has to be searched for twice and the report writes itself. For each question:

- the takeaway, in one or two sentences;
- the findings, each with the handle the tool result gave its source (`source_id`), what that source is, its date, and whether you read the page or only its passage;
- what you infer from them, marked as yours;
- what you could not find, and why.

You cite by handle: you never need, and must never write, a title, date or address from memory.

## 4. Judge what you read

Do not take a result at face value. For each finding, ask:

- Is it established, or a forecast or a guess ("could", "may", "is expected to")? Say which.
- Is this the original, or something repeating it? Prefer the statute to the commentary, the regulator's guidance to a law firm's note on it, the standard's publisher to a blog.
- Does the source earn trust? Nameless sources, passive voice with no one behind it, broad claims with no specifics and repeats of unconfirmed reports carry little weight, as does a page that does not say who wrote it or when.
- Is it current? Trust what you found today over what you remember. A source older than the question's period, or superseded, is marked as such or dropped. Legislation is read at its current version.

A source that failed to load, or loaded without what you needed, is not a source: leave it out of your notes.

## 5. Test the answer before you write it

- A material claim (one the answer turns on, a figure, a date, an obligation) wants two independent sources, or one primary source. A claim
  from a single secondary source is written as such ("according to ..."), never as settled fact.
- Where sources disagree, keep both and say why they may differ (date, scope, jurisdiction, who is asking). Never average or pick quietly.
- Search once for evidence against your leading conclusion. If it is there, it goes in the report.
- One further round of research only if a gap would leave the answer incomplete and you know what to search for. Only one: then write.

## 6. If the sources are not good enough

When a part has no source you read that answers it, the report says so under "What could not be established": what was asked, what was
searched, what was found or not. When **nothing** you read answers the question, or only sources you would not rely on, write **no report and no bundle**. Reply plainly: what you searched, what you found and why it does not answer the question (old, vendor-only, off-topic,
unreadable), and what would help (a document from the person, a narrower question, a named source). Never fill a gap with what you know
without a source, and never present a thin result as an answer.

## 7. Write the report

Write it as Markdown text, as an analyst writes for someone who will act on it, in this shape (leave out a section with nothing to say):

```
# A title of about six words that says what was found

The answer, in one paragraph.

## A heading that states a finding
## A heading that states another finding
## Where sources disagree
## What this means
## What could not be established
## Method
```

- **The opening paragraph** says the answer in its first sentence, then why it matters and what the reader needs for context: five to eight
  sentences. Someone who stops here is informed.
- **Headings say what you found, not the topic**, in sentence case, with the number where there is one: "Fines reach 4% of turnover", not
  "Penalties". Someone reading only the headings gets the argument. Three to five is usual: as long as the question needs, and no longer. A focused
  report that makes its point beats one that holds everything.
- **Write connected paragraphs, not lists.** Each section moves the argument on rather than listing what you found. Say what the numbers
  mean and how the findings bear on each other. Bold the few facts someone scanning must not miss. Be direct and concrete, in the active voice; hedge only where
  the evidence is uncertain, and then say what is uncertain. A table is for what really is a table: a pipe table with a header row.
- **Take a position.** Come to a conclusion about what is true and what the person should make of it, having given the strongest opposing view its due.
- **"What this means"** is your own reasoning: what follows, what it changes, what to do next. No repeat of what came before, and no new facts: a fact belongs in a finding, with its source. One or two paragraphs.
- **"Method"**: the scope you settled (jurisdiction, period), the searches you ran, how many pages you opened and how many search passages you used, and the date. **"What could not be established"**: anything you could not source, plainly.
  These last three need no citation.
- **Every other sentence is a finding, and every finding is cited**: the opening paragraph, each sentence, each list item, each row of a table, and every table cell that holds a figure. A source is cited as you cite it in a reply: `[[cite:handle]]` after the sentence it supports, with the handle the
  tool result gave for that source (`source_id`). Cite a claim with the sources that support it; a sentence no source supports does not
  go in the findings.
- **Never write an address, a link or a source's details.** A web address, a Markdown link and an image are refused. The host knows what
  you read: it turns each citation into the source's number, linked to its real page, and adds the Sources list itself. Do not write a
  Sources section. A source that is a record held in Saphion is named in words in the list, with no page.
- A figure appears once; quote briefly and mark it as a quotation, with its citation. A figure, name or date a source did not give is not written: it goes under what could not be established.

## 8. Make the report and the bundle

From `execute_code`, run `scripts/build_research_report.py` with `skill_script(skill="deep-research", script="scripts/build_research_report.py", args=[...])`:
the args are the report's Markdown as one text, and optionally a file name (no extension). Do not make the report with `build_files`: this script is the one door, so
a report that fails the checks never lands as a file.

It checks the report against the sources the host resolved, and writes nothing unless every check passes:

- every finding is cited, as section 7 says, and the findings cite at least one source you read;
- no address, link or image is in the text, and no Sources section.

When it refuses, it names each fault: correct the Markdown and run it again, with citations only for what you read. When it passes, the host
renders your report in the Organisation's own document design, each citation shown as its source's number linked to the page, with a Sources
list it adds, and delivers two files in the same run: the Word report, and a ZIP holding that Word file and `sources.md`, the source list.
If the checks fail, nothing is delivered. The script cannot read the web, so that the page says what you wrote is your own check
(section 5), not the script's.

## 9. Reply

Say the answer and your position in a few sentences of your own, cited as you always cite in a reply. Say how many sources the report rests on, and which findings
rest on one source (the script prints that count). Say what could not be established and why. Offer the report and the bundle by name.
