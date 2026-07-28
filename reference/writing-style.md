# Writing style

Binding for all generated prose: manual sections, glossary summaries,
preview bodies, ticket text, "What's new" entries, and tracker issue
descriptions. The product's own brand voice layers on top of these
rules; it never overrides them.

The catalogue under "Words to cut" and "Patterns to cut" is adapted
from the `no-ai-slop` skill by Peter Yang, used and modified under the
MIT License. The notice is at the end of this file.

## The register

A manual is reference documentation. It is scanned, re-read, and
consulted, usually by someone in the middle of a task. That is a
different job from an article, and it takes a different voice.

Reference prose explains how the thing works. It does not argue that
the thing is good, walk the reader through the writer's reasoning, or
build to a point.

Borrow nothing from persuasive writing. Specifically, none of these
belong in a manual:

- a personal journey, or any first-person account of how something came
  to be built
- a thesis the section argues toward
- a metaphor carrying the explanation
- a call to engagement, or any closing line that reaches for
  significance
- emotional vocabulary about the software

Write the operational fact. Let the reader decide what it is worth.

## Knowledge and instruction

The manual does two jobs. It explains how something works, and it tells
the reader how to do something. Those take different postures, and
writing an instruction in the explaining posture is what makes
documentation feel mysterious.

**Explaining takes the declarative.** The system is the subject and the
reader is absent. "The guard compares the manual's base marker against
the commits since it."

**Instructing takes the imperative.** The reader is the subject,
understood. Name the control, then the outcome, in that order.

Wrong: "Enter keeps the change and steps back out. Shift+Enter breaks
a line inside the block. Escape abandons the block and restores what it
said."
Right: "Press Enter to save your edit. Press Shift+Enter to start a new
line. Press Escape to discard your changes."

The rules that produce the second:

- **Never make a key, button, or control the subject of a verb.** Keys
  do not keep, abandon, or break anything. The reader presses them and
  something happens. "Enter keeps the change" reads as a fact about
  Enter; "Press Enter to save your edit" reads as something to do.
- **Lead with the action, follow with the result.** "Press X to Y", not
  "Y happens on X".
- **Name the outcome in the reader's words.** "Discard your changes",
  not "abandon the block". The reader knows what their changes are.
  They have never heard of the block.
- **Address the reader as you, and only for their own actions.** The
  system stays in the third person for what it does on its own.
- **One action per sentence.** An action worth documenting is worth its
  own sentence, and a list of three keys is three sentences.
- **Say what it does, not what it is for.** "Press Escape to discard
  your changes", not "Escape is available if you want to discard".

Keep the declarative where the reader is not acting: constraints,
behaviour they do not trigger, and anything the system decides on its
own. A paragraph often needs both, the instruction first and the
mechanism behind it second.

## The prose never narrates

This is the rule most often broken, so it gets its own section.

**No audience narration.** The prose never says who is reading, why
they are here, what they want, or what state of mind they are in.
"Someone opens the manual mid-task, looking for one answer" is about
the reader. Delete it and explain the feature.

**No meta-commentary.** The prose never describes the document, its
own structure, or what a section is about to do. Delete "this section
covers", "as described above", "from there it sets two obligations",
"what follows is". Explain the thing; the explanation is the orienting.

**Content does the orienting.** A section opens by naming what it
contains, stated mechanically. Not what it is for, not who it serves,
not why it exists.

Wrong: "This section will help you understand how the guard works."
Right: "The guard compares the manual's base marker against the
commits since it."

**Cross-references are concrete.** Name the specific thing the reader
will find, not its direction. "The base marker, described under The
staleness guard" beats "see above" or "as described elsewhere".

## How a sentence earns the next one

By adding the next layer of operational detail, in order. Not by
advancing an argument.

- **Depth accumulates.** Each sentence adds a concrete layer: what it
  does, then under what condition, then what happens when the condition
  fails.
- **State the mechanism.** Say what the thing does, concretely and
  once. "The guard compares the manual's base marker against the
  commits since it" beats "the guard checks whether the manual is
  current".
- **State the consequence.** Whenever getting it wrong costs anything,
  say what breaks, how they will know, and what undoing it takes.
- **Explain why only when the why changes what they do.** Reasoning
  earns its space when it tells the reader how to handle the case this
  page does not cover. It does not earn its space as background.
- **One idea per sentence, one job per paragraph.**
- **Prefer the instance to the rule.** Name the file, the command, the
  number, the error text.
- **One term for one thing.** Define it once and reuse that exact term.
  Never rotate synonyms for variety. In documentation a new word means
  a new thing.
- **Name things as the reader would.** Use the ordinary term for the
  thing on screen: the desktop layout, the table of contents, the menu.
  Describing how it looks ("three flat lines in the upper left") makes
  the reader translate before they can act.
- **Headings are plain nouns.** "Distribution", not "Handing it out".
  A heading is a label in a list someone is scanning, not an opening
  line.
- **Describe only what has shipped.** Planned work lives in previews,
  labelled as planned. Never blend the two.

## Respect the reader

Not by addressing them. By what the prose refuses to do.

- **Assume competence.** Explain this system, not the general concept
  it belongs to. Do not define what a branch is.
- **Never flatter.** No "great question", no "you're all set!", no
  congratulating anyone for reading.
- **Never condescend.** Cut "simply", "just", "easy", "obviously", "of
  course". A step that was easy for the writer is not always easy for
  the reader, and calling it easy makes failure feel like their fault.
- **Do not hedge to protect yourself.** "May potentially cause issues
  in some cases" informs nobody. Say what happens, or find out and then
  say it.
- **Name the sharp edges.** When something is awkward, slow, or
  destructive, say so and say what to do about it.
- **Own the product's failures.** "You entered it wrong" becomes "The
  field takes a short SHA and rejects a full one."

## Hard rules

1. No em-dashes. Use a period, a comma, a colon, or parentheses.
   Restructure the sentence if none fit; it usually reads better after.
2. Honesty is assumed. Delete "honestly", "to be honest", "frankly",
   "truthfully", "candidly". If a message carries weight, carry it with
   grounded, specific language, not an intensity marker.
3. "Actually" must be materially required, meaning the sentence is
   wrong or misleading without it. Same standard for "basically",
   "essentially", "simply", "just".
4. Minimize verbosity. Cut a word if the sentence survives without it.
   One idea per sentence. Short sentences carry urgent facts best.
5. Active voice with human subjects. "The script refuses the edit"
   beats "the edit is refused".
6. Direct verbs. "Decided", not "made a decision". "Can", not "has the
   ability to".
7. Every claim is checkable against the code. If you cannot point at
   what makes it true, do not write it.

## Words to cut

- "It's worth noting", "It's important to note", "Note that"
- "delve", "dive into", "deep dive", "unpack", "explore"
- "seamless", "comprehensive", "powerful", "cutting-edge"
- "leverage", "utilize", "facilitate", "streamline", "empower",
  "optimize", "align", "synergy", "paradigm", "closed loop"
- "stakeholder". Name the people or the role.
- "robust". Say what holds: "survives a rebase", "refuses a bad SHA".
- "not just X, but Y" constructions
- Rule-of-three lists used for rhythm rather than content
- Hedging stacks: "may potentially", "can help to", "could possibly"
- A colon in every heading; a summary sentence restating the paragraph
- Exclamation points in body prose

Any word that could appear in a corporate mission statement without
anyone noticing.

## Patterns to cut

**Binary contrasts.** "It's not X, it's Y." Also "X alone isn't enough,
what's needed is Y" and "requires Y, not just X". State Y directly. If
the reader needs to know why the alternative falls short, the specifics
will show them. Never perform the contrast.

**Throat-clearing.** "Here's the thing", "Let me be clear". Cut it and
state the point.

**Faux-insight setups.** "What most people get wrong", "the part
everyone misses". Let the claim stand on its own.

**Colon reveals.** A noun phrase, a colon, a small dramatic noun: "The
detail that makes it work: a separate agent grades it." Write it as a
sentence. Colons are for lists, labels, and quotes.

**Superficial analysis.** Trailing `-ing` clauses that pretend to
explain. "Adds file search, highlighting our commitment to workflow"
becomes "adds file search, so a draft can be found without leaving the
editor".

**Importance puffery.** "Marks a pivotal moment", "plays a vital role".
State the fact and let the reader judge.

**Weasel attribution.** "Experts agree", "studies show". Name the
source or cut the claim.

**Synonym cycling.** If the clear word is right, repeat it.

**Dramatic fragmentation.** "That's it. That's the whole thing."

**Rhetorical setups.** "What if I told you", "Think about it:".

**Fake-profound kickers.** The closing line that turns a concrete point
into an aphorism. Delete it and end on the last concrete sentence.

**Summary-recap endings.** "In conclusion", "Overall", or a last
paragraph restating the section.

**Formatting slop.** Emoji in headings, bold sprinkled mid-sentence,
bullets where two sentences read better, a header over two sentences.
Format follows content; it does not decorate it.

## Weight without theater

Wrong: "Warning! It's critically important that you never unplug the
drive during verification!"
Right: "Don't unplug the drive while it verifies. An interrupted
verification restarts from zero."

The second is urgent because it is concrete: it names the action, the
consequence, and nothing else.

## Attribution

The catalogue in this file is adapted from the `no-ai-slop` skill by
Peter Yang, modified for documentation and reused under the terms
below.

```
MIT License

Copyright (c) 2026 Peter Yang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
