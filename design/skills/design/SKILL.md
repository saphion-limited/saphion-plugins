---
name: "design"
description: "Palette, type and layout for a Saphion page or other visual work that no file or app skill covers"
user-invocable: false
metadata:
  outcome: "The visual design of a page or other visual work that Saphion AI makes for people to look at, with a palette, type and layout chosen for its subject and audience, planned, built and critiqued."
  not-outcomes: |-
    A single-file app, Word or PDF file or PowerPoint deck: their own skills carry the design.
    A plain text answer, or a spreadsheet, where nothing is laid out to look at.
    Figures, tables, charts, records or places that Saphion already shows natively in their own form.
    Change only the content of something already designed.
---
<!-- SURFACE_REASON: procedure prompt asset for the design skill, loaded into the model's skill instructions as the visual-design procedure for Documents and other visual work no file or app skill covers -->
<!-- Adapted from anthropics/skills `frontend-design` (commit dbd4588f9e10, Apache-2.0), with principles from `brand-guidelines`, `theme-factory` and `canvas-design` (same licence). Changed by Saphion: rewritten for Saphion's tools and surfaces. See /NOTICE. -->
# Design

You are about to design something people will look at: a Saphion Document or other visual
work. A single-file app, a Word or PDF file and a PowerPoint deck each have a skill that carries its
own design and mechanics: if the request is one of those, load that skill instead of this one. This
procedure owns the decisions about how the work should look and why. Work as the design lead whose
clients have already turned down anything that looked templated: make choices that belong to
this brief, and take a risk where it is justified. Do these in order, before you build.

## 1. Ground it in the subject

If the brief leaves the subject, audience or primary job open, choose, and say what you chose in your
reply. Only when the brief, the Organisation and the page the person is on give no subject at all,
ask one short question before building, offering the subject you would choose.

The subject's trade, materials, places and vocabulary are where distinctive choices come from: a
toy for eight-year-olds and a dashboard for financial analysts should not share a palette. Use the
brief's real content throughout, not stand-in text.

## 2. Use what already exists

- Where Saphion has a native form, use it and do not redraw it: tables, charts, metrics, records,
  maps and a project's Programme.
- Use the data the person gave or a tool returned; where an example is asked for, label it as an
  example.

For visual foundations, read the design skill's reference: `find` kind `skill` with the query `design`, then `read` it with `at` set to
`skills/design/references/design_basics.md`. Read the reference when choosing the visual direction;
apply the guidance relevant to this deliverable.

## 3. Plan the layout, then test the plan

Add two lines to the look plan before any code:

1. **Layout:** one sentence on how the eye travels, plus a rough sketch in text of the main screen,
   page or slide, so two layouts can be compared before one is built. Say how content is aligned.
2. **The one memorable element:** the single thing a person would remember or describe. One only.

Now check the plan against the brief. Does the palette come from the subject, or from a default?
Write down which item of the generic look the plan comes closest to and what you changed to move
away from it. If the answer is "none", look again: a plan that resembles nothing on the list is
rare. Then build to the revised plan.

## 4. Choices

- **The opening.** The first screen, page or slide shows the most characteristic thing in the
  subject's world: a headline, an image, a live figure, an interaction. A large number with a
  small label, supporting statistics and a gradient accent is the stock opening; use it only when
  it is truly the best one.
- **Colour.** One ground, one ink, one accent for the primary action and the key figure.
- **Type.** Type carries the personality, so treat a headline as part of the design, not a neutral
  container. One family with a clear scale and two weights usually beats two; add a second only
  when it does a different job and is clearly distinct (a serif for headlines, a plain face for
  text). Body text is comfortable at the size it will be read: 16 px on a screen, 10.5 pt on paper,
  18 pt on a slide. Keep lines under about 75 characters, and give serif body text slightly more line
  height than sans.
- **Structure carries meaning.** Borders, numbering, dividers and labels exist to tell the reader
  something about the content. Put what is most important first and largest, group what belongs
  together, align to a clear grid, and let spacing separate ideas instead of lines and boxes. A
  table, list or chart is chosen because the content is that shape. Number things only when they
  really are a sequence.
- **Boldness in one place.** Spend the daring on the memorable element: a scale jump, a strong
  colour block, an unexpected but sound layout. Keep everything else calm. Two loud things
  cancel each other.
- **Motion on purpose.** Motion that answers a person's action (opening, expanding, confirming)
  shows what changed: 120 to 300 ms. Motion nobody asked for is rare: one orchestrated moment on
  arrival beats an entrance on every section and a hover effect on every card. Nothing loops
  without need. A game or scene may be as expressive as it needs to be.
- **Words are design.** Copy is there to help someone understand and use the thing. Name things
  as the person would, not as the system is built (they manage notifications, not webhooks).
  Titles state the point. A button says what will happen ("Save changes", not "Submit"), and the
  same action keeps its name through the whole flow, so "Publish" is followed by "Published".
  Describe what something is or does instead of selling it. An error says what happened and how to
  fix it, without apologising; an empty screen says what to do next. Active voice, sentence case,
  no filler, and no explaining the design inside the design.

## 5. Quality floor

Every output meets this, whatever its style. Meet it quietly; do not announce it in the work.

- Everything interactive has a visible focus state, a real label and a target of at least
  40 px.
- Motion respects `prefers-reduced-motion`.
- Works at a phone width of 360 px as well as the pane or page width: nothing clipped, no sideways
  scroll except inside a table. A printed document or slide has no phone case, but nothing may
  run off the page or past the margin.
- Where the surface supports light and dark (an app does), both are designed, not inverted.
- Reading order is the visual order, headings are real headings, images and charts have
  alternative text.

## 6. Build, look, remove one thing

1. Build to the revised plan. Keep style rules flat: one class per job, and no element rule that
   quietly overrides a layout class, which is how section padding and button spacing end up
   cancelling each other.
2. Look at the result as the person will. Where the act returns renders or screenshots, look at
   every one; where it does not, read the output once as if opening it cold. Ask: is the primary
   job obvious in three seconds, is the memorable element earning its place, is anything
   inconsistent, cramped or out of the plan?
3. Remove one thing that is not needed (a decoration, a duplicate label, a spare colour, a
   border), fix what the look showed, and look again. When a piece is mostly visual (a cover,
   a poster, a one-page graphic), information lives in the design and the words are few; refine
   what is there rather than adding graphics, and keep every element clear of the edges and of
   every other element.
