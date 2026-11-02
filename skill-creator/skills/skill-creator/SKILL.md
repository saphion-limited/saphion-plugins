---
name: "skill-creator"
description: "Make or change one of your own skills by talking it through"
metadata:
  outcome: "A skill of the person's own, made or changed with them: what the job is, a draft they try on a real example, revised until it is right, then saved to their own skills."
  not-outcomes: |-
    Use a skill the person already has to do its job.
    Share a skill, give it to the Organisation or remove it (sharing is not offered yet).
    Make a file, a document or an app.
---
<!-- SURFACE_REASON: procedure prompt asset for the skill_creator skill, loaded into the model's skill instructions when a person makes or changes a skill of their own with Beacon -->
# Skill creator

A skill is a procedure the person teaches Beacon once and then asks for by name or lets Beacon choose: "summarise a site diary", "check a subcontractor's insurance pack". You make one with them in this chat: find out the job, draft it, let them see it work on a real example, change it until it is right, and save it. A skill you save is theirs and private to them. You cannot remove it: that is theirs to do in Settings, under Skills, and you say so when it comes up. Sharing a skill and giving it to the Organisation are not offered yet, so say so if they ask.

## 1. A new skill, or a change to one they have

If the request names a skill they already have (the composer names it, with the name it is kept under), read it first with `plugin_read`, using that name, then each other file you will change by its path from the listing. Work from what they hold: keep its shape and its wording where they are not the problem. Saving then makes a new version of that same skill, and the person can put an earlier version back in Settings. A skill you cannot read this way is not theirs to change here (a Saphion skill, their Organisation's, one a colleague shared). Say so, and offer to make a skill of their own on the same lines under another name.

If they have no skill like it, make a new one.

## 2. Find out the job

Ask what you need and no more, one or two questions at a time, in their words. Stop asking as soon as you could write the first draft, and skip this step when they have already told you enough.

What you need:
- The job, from the moment they start it to the moment it is done. Ask for a real instance: what they had, what they did with it, what they ended up with.
- What a good result looks like to them: its shape, its length, the order of its parts, the words they would use.
- What goes wrong or must never happen: the corner they always cut, the figure that must be checked, the thing nobody should be told.
- What the skill should always have to hand: a checklist, a template, a list of codes, a standard wording. These become files the skill reads, not text pasted into its procedure.

Do not ask them what to name it, how to lay it out or how it will be stored. Those are yours to decide.

## 3. Draft it

Show the draft in the chat before anything is saved, in plain words they can judge: what you will name it, what it is for, and the procedure.

**The name** is a few lowercase words joined by hyphens, for the job and not the person (`site-diary-summary`). It is what they type after `/` to ask for the skill, so make it one they would say.

**The description** says what the skill does and when to use it, in a sentence or two. Beacon reads only this to decide whether the skill fits a request, so name the jobs and the wording people use for them. Do not use it to hold the procedure.

**The procedure** is the body of the skill's `SKILL.md`: what to do, in order, written as you would brief a capable colleague who has never seen the job.
- Say why a step matters when it is not obvious. A reason lets the skill cope with a case the steps did not foresee; a bare order does not.
- Say what to produce and how it should read. Give a short example of a good result when the shape matters.
- Say what to ask the person for when something is missing, and what to leave alone.
- Keep it short enough to read in one go. Material that is long or only sometimes needed goes in its own file beside it, and the procedure says when to read it.
- Name a tool only if you are certain Beacon has it; otherwise say what is wanted and let Beacon choose how.
- Never put a password, a key or a private address in a skill.

**The files** are laid out as the skill is stored. A skill named `site-diary-summary` is:

- `skills/site-diary-summary/SKILL.md`: starts with `---`, then `name:` (exactly the folder name) and `description:`, then `---`, then the procedure;
- `skills/site-diary-summary/references/<topic>.md`: each file the procedure reads, one topic each.

Most skills are one `SKILL.md`. A package of several related skills has a folder for each.

## 4. Let them try it

Before you save, run the draft once. Ask for a real example (they paste a diary, or attach a file) and do the job exactly as the draft says, no better and no worse, so they see what the skill will really do. Then ask what is wrong with it.

When something is wrong, change the draft rather than patching the result, so the next run is right too. Say what you changed in a line. If the first example was an easy one, offer to try a harder one. Stop when they say it is right.

## 5. Save it

When they have said it is ready, or asked you to save it, call `plugin_save`:
- `name`, `description` and, if they want a nicer title in Settings, `display_name`;
- `files`: each file's whole text at its path. For a change, list only the files that change; a file you do not list stays as it was, and `text: null` removes one;
- `invocation` only when they ask for it: a new skill starts `automatic`, so Beacon may choose it when a request fits, and `explicit_only` means only when they ask for it by name with `/`.

Then tell them it is saved, where it is (Settings, under Skills, in Yours), and how to use it: start a new chat and ask for the job in plain words, or type `/` and its name. A new chat matters: the skill runs from what is saved, which is not what this conversation still has in mind. Say that it is private to them.

## 6. If a save is refused

Read the reason, and act on it.
- It does not meet the skill format (a missing field, a name that is not lowercase words with hyphens, a file where none is allowed): correct that and save again.
- The skill changed since you read it (the person edited it in Settings, or another chat did): read it again with `plugin_read` (and the files you are changing, by path), make your change on what they hold now, and save again. Do not overwrite what you did not see.
- The name already belongs to something that is not theirs, or to a skill of theirs you have not read: choose another name, or read the one they have.

## 7. Changing a saved skill later

Whenever they come back to change a skill, start again at step 1. Every save is a new version, so changing a skill is safe, and you never need to ask whether to keep the old one.
