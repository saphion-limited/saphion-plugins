---
name: "research-report"
description: "Research a question across several sources and deliver a cited report with a bundle of its sources"
metadata:
  outcome: "A question researched across several sources Beacon read, answered in a Word report in which every claim cites a source that opens its real page, with a downloadable bundle of the report and its source list; or a plain statement that the sources found were not good enough, with nothing invented."
  not-outcomes: |-
    Answer a single fact, date or figure that one search settles.
    Summarise or answer questions about a file the person supplied.
    Write a document from what the person already told you, with no research.
---
<!-- SURFACE_REASON: procedure prompt asset and helper script for the research_report skill, loaded into the model's skill instructions for researching a question across sources and delivering a cited report -->
# Research report

The person asked a question that needs more than one source: what the rules require, how options compare, what is known about a
subject. They want an answer they can rely on and check: a report in which every claim names a source you actually read, that opens the real
page, and a bundle they can keep. You do the research with your own tools; one helper script checks the citations and writes the report and its bundle. It runs
in the file sandbox, which has no network, so everything you learn comes through `web_search`, `web_read`, `legislation_search`,
`legislation_read` and Saphion's own reads. A single fact (one date, one figure) is answered with `web_search` and `depth` `lookup`, not this
skill.

## 1. Plan

Ask the person, with `ask`, only what would change the research: the jurisdiction, the period, an ambiguous name or acronym. Otherwise
proceed. Then write the plan before searching: the question restated in one sentence, and three to six sub-questions that together answer it
without overlapping (one for each facet, region, option or period). Note what would count as a good source for each: the regulator or
statute, the publisher of the standard, the organisation's own records for something about them; a trade body or an expert next; a vendor
only for what the vendor itself does. Keep the plan in `todos` when it has more than three parts.

## 2. Search broadly

For each sub-question run `web_search` with a query phrased the way the best source would phrase it, and run independent searches in one
response. Use `domains` for official sites (`gov.uk`, the regulator), `published_from` when recency matters, and `country`. UK law is
`legislation_search` then `legislation_read` of the provision itself, not a website's account of it. What the Organisation holds (its records,
files, documents) is `find` and `read`: a question about the person's own work is answered from their own material first.

Keep notes as you go, one line for each source you may use: the handle the tool result gave it (`source_id`), what it is, its date, whether
you read it in full or used the passage the search returned, and which sub-question it answers. You cite by handle; you never need, and
must never write, a title, date or address from memory.

## 3. Read the primary sources

A search result with a passage that answers the sub-question is citable as it is. One without, or one that is only a summary of someone
else's work, is read with `web_read` (up to five a call, asking it the sub-question), and a summary leads you to the original it cites: find
that and read it. Prefer the statute to the commentary, the regulator's guidance to a law firm's note on it, the standard's publisher to a
blog. Note what each source is (primary, expert, vendor, news) and its date; a source that does not say who wrote it or when carries little weight.
A source that failed to load, or loaded without the passage you needed, is not a source: leave it out of your notes.

## 4. Cross-check

Before writing, take each claim you mean to make and test it:

- A material claim (one the answer turns on, a figure, a date, an obligation) wants two independent sources, or one primary source. A claim
  from a single secondary source is written as such ("according to ..."), never as settled fact.
- Where sources disagree, keep both and say why they may differ (date, scope, jurisdiction, who is asking). Never average or pick quietly.
- Check dates: a source older than the question's period, or superseded, is marked as such or dropped. Legislation is read at its current version.
- Search once for evidence against your leading conclusion. If it is there, it goes in the report.
- One more round of searching only if a sub-question is still open and you know what to search for; then write with what you have.

## 5. If the sources are not good enough

When, after this, a sub-question has no source you read that answers it, say so: the report states under "What could not be established" what
was asked, what was searched and what was found (or not). When **nothing** you read answers the question, or only sources you would not
rely on, write **no report and no bundle**. Reply plainly: what you searched, what you found and why it does not answer the question
(old, vendor-only, off-topic, unreadable), and what would help (a document from the person, a narrower question, a named source). Never fill
the gap with what you know without a source, and never present the thin result as an answer.

## 6. Write the report

Write the report as Markdown text, in this shape (leave out a section with nothing to say):

```
# The report's title

## Question
## Answer in brief
## Findings
### One heading for each sub-question
## Where sources disagree
## What could not be established
## Method
```

- **Question**: the question, and the scope you settled (jurisdiction, period). **Method**: the searches you ran, how many pages you read in
  full and how many passages you used, and the date. **What could not be established**: anything you could not source, stated plainly.
  These three state no finding and need no citation.
- **Everything else is a finding, and every finding is cited**: each sentence, each list item, each row of a table, and every table cell
  that holds a figure. A source is cited as you cite it in a reply: `[[cite:handle]]` after the sentence it supports, with the handle the
  tool result gave for that source (`source_id`). Cite a claim with the sources that support it; a sentence no source supports does not
  go in the report.
- **Never write an address, a link or a source's details.** A web address, a Markdown link and an image are refused. The host knows what
  you read: it turns each citation into the source's number, linked to its real page, and adds the Sources list itself. Do not write a
  Sources section. A source that is a record held in Saphion is named in words in the list, with no page.
- A table is a pipe table with a header row. A figure appears once; quote briefly and mark it as a quotation, with its citation.
- A figure, name or date a source did not give is not written; it goes under what could not be established.

## 7. Make the report and the bundle

Run `scripts/build_research_report.py` with `run_skill_script` (`skill_name: "research-report"`, `script_name`) and `args`: the report's
Markdown as one text, and optionally a file name (no extension). Do not make the report with `file_make`: this script is the one door, so
a report that fails the checks never lands as a file.

It checks the report against the sources the host resolved, and writes nothing unless every check passes:

- every finding is cited, as section 6 says, and the findings cite at least one source you read;
- no address, link or image is in the text, and no Sources section.

When it refuses, it names each fault: correct the Markdown and run it again, with citations only for what you read. When it passes, the host
renders your report in the Organisation's own document design, each citation shown as its source's number linked to the page, with a Sources
list it adds, and delivers two files in the same run: the Word report, and a ZIP holding that Word file and `sources.md`, the source list.
If the checks fail, nothing is delivered. The script cannot read the web, so that the page says what you wrote is your own check
(section 4), not the script's.

## 8. Reply

Open with the answer in your own words, cited as you always cite in a reply. Say how many sources the report rests on, and which findings
rest on one source (the script prints that count). Say what could not be established and why. Offer the report and the bundle by name.
