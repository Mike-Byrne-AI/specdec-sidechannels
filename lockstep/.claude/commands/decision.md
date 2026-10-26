Record an architectural decision in `trellis-docs/trellis-decisions.md`, using context from the current session to propose a draft.

This is more than a form — it's an interview that produces a properly formatted decision entry.

## What to do

**1. Read the existing trellis-docs/trellis-decisions.md** to find the next D-N number (highest + 1) and absorb the format conventions.

**2. Propose a draft from session context.** Look at what the user has been working on this session. Often the decision is implicit in the conversation — they just chose between two options, or they specified a constraint that affects future work. Propose a draft entry with:

- **Title** (5-10 words, captures the choice)
- **Context** (what was being decided)
- **Choice** (what was picked)
- **Why** (the argument that won)
- **Alternatives considered** (with brief reasons they lost)
- **Reversibility** (cheap / medium / expensive)
- **Confidence**: default to `[imagined]` unless you have hard evidence it's been verified

Show the draft and ask: "Does this capture it, or want to adjust any fields?"

**3. Confidence is user-only.** If you think the decision is `[probable]` or `[verified]`, say so as a proposal but do NOT set it to anything other than `[imagined]` in the draft. The confidence-promotion hook will block higher confidence levels without justification anyway.

**4. Once confirmed, append the entry** to trellis-docs/trellis-decisions.md. Show the user the diff so they can spot any drift. Update any related references (e.g., if the decision invalidates a section of CLAUDE.md, mention it — don't fix it automatically).

**5. If you don't have enough session context** to propose a meaningful draft, ask the user the 6 fields directly. Skip the proposal step.

## What not to do

- Don't promote confidence above `[imagined]` on your own initiative. The hook will block it; the convention is also documented in CLAUDE.md and trellis-docs/trellis-decisions.md.
- Don't append to trellis-docs/trellis-decisions.md without showing the user the diff first.
- Don't include `USER-CONFIRMED` or `trellis_verify_finding.py` justification text unless those things are actually true. These are bypass markers, not template filler.
- Don't generate decisions speculatively. If the user hasn't decided anything yet, this command isn't the tool for that conversation.

## Output format

The draft proposal should look exactly like the format in `trellis-docs/trellis-decisions.md` so the user can read it as a preview:

```markdown
## D-N — <title>                                                    [imagined]

**Context**: ...
**Choice**: ...
**Why**: ...
**Alternatives considered**: ...
**Reversibility**: ...
**Source**: <link to relevant task pack, finding, or run>
```

Then ask one clear question: "Append this as D-N?"
