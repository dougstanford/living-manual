# Writing style

Binding for all generated prose: manual sections, glossary summaries,
preview bodies, ticket text, "What's new" entries, and tracker issue
descriptions. The product's own brand voice layers on top of these
rules; it never overrides them.

The pattern catalogue under "Words to cut" and "Patterns to cut" is
adapted from the `no-ai-slop` skill by Peter Yang, used and modified
under the MIT License. The notice is at the end of this file.

## Who is reading, and when

A manual is not read for pleasure and rarely read in order. Someone
opens it mid-task, often mid-problem, looking for one answer. That
fact decides most of what follows.

- They arrive in the middle. Every section has to work for someone who
  did not read the one above it.
- They scan before they read. The first sentence of a paragraph carries
  the answer; the rest supports it.
- They stop as soon as they have what they came for. Prose after the
  answer is prose nobody reads.
- They are already a little annoyed. Something did not work, or they
  would not be here.

## Respect the reader

The reader is competent and busy. Both halves matter.

- **Assume competence.** They know their own job. Explain this system,
  not the general concept it belongs to. Do not define what a branch
  is.
- **Never flatter.** No "great question", no "you're all set!", no
  congratulating someone for reading. Praise sits between them and the
  answer.
- **Never condescend.** Cut "simply", "just", "easy", "obviously", "of
  course". A step that was easy for the writer is not always easy for
  the reader, and calling it easy makes failure feel like their fault.
- **Do not hedge to cover yourself.** "May potentially cause issues in
  some cases" tells the reader nothing and protects only the writer.
  Say what happens, or find out and then say it.
- **Name the sharp edges.** When something is genuinely awkward, slow,
  or destructive, say so and say what to do about it. A manual that
  only ever sounds pleased is one nobody trusts twice.
- **Own the product's failures.** "You entered it wrong" becomes "The
  field takes a short SHA and rejects a full one."

## Make them understand, not just comply

A reader who has only followed steps cannot recover when a step fails.
A reader who understands the mechanism can.

- **Name the mechanism.** Say what the thing does, once, concretely.
  "The guard compares the manual's base marker against the commits
  since it" beats "the guard checks whether the manual is current".
- **State the consequence.** Every instruction implies an "or else".
  Make it explicit whenever getting it wrong costs something: what
  breaks, how they will know, and what undoing it takes.
- **Explain why when the why changes what they do.** Reasoning earns
  its space when it tells the reader how to handle the case this page
  does not cover. It does not earn its space as background colour.
- **One idea per sentence, one job per paragraph.** A paragraph doing
  two jobs gets skimmed and half understood.
- **Prefer the instance to the rule.** Name the file, the command, the
  number, the error text.
- **Define a term once, then reuse that exact term.** Never rotate
  synonyms for variety. In documentation a new word means a new thing.
- **Describe only what has shipped.** Planned work lives in previews,
  labelled as planned. Never blend the two.

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
- "seamless", "robust", "comprehensive", "powerful", "leverage",
  "utilize", "facilitate", "streamline", "empower"
- "not just X, but Y" constructions
- Rule-of-three lists used for rhythm rather than content
- Hedging stacks: "may potentially", "can help to", "could possibly"
- A colon in every heading; a summary sentence restating the paragraph
- Exclamation points in body prose

## Patterns to cut

**Binary contrasts.** "It's not X, it's Y." State Y directly.

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
into an aphorism. Delete it and end on the clearest concrete sentence
already there.

**Summary-recap endings.** "In conclusion", "Overall", or a last
paragraph restating the section. The reader was just there.

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

The pattern catalogue in this file is adapted from the `no-ai-slop`
skill by Peter Yang, modified for documentation and reused under the
terms below.

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
