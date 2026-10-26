Run a glass-castle protocol audit on the current session. Surface claims you made that should have been marked verified / probable / imagined but weren't.

This is a self-audit. Honest output is the goal — finding zero issues is fine; finding three issues is also fine. What's not fine is performative completeness.

## What to do

**1. Scan your prior turns in this session.** Identify the substantive claims you made — factual statements about the codebase, the data, the model's behavior, design proposals, conclusions from observed results.

**2. Classify each claim:**

- **Verified**: you ran code, viewed a file, or observed a result in this session that supports the claim. The claim cites that evidence (or could).
- **Probable**: the claim is plausible given context (memory, prior conversation, common patterns), but you didn't actually check.
- **Imagined**: the claim describes a design, hypothesis, or behavior that doesn't exist in the repo yet.

**3. Flag the misses.** For each claim that's `probable` or `imagined` but was phrased as if verified, report it in this format:

```
[probable, presented as verified] "<exact phrase or close paraphrase>"
  Source: <which turn>
  What would verify it: <concrete check, like "view src/X.py" or "run verify_finding F2">
```

**4. Be specific about WHAT would change.** Don't just say "this was unverified." Say what check would verify it. The audit is only useful if it generates next-action items.

## What not to do

- Don't list every claim. Filter to the ones that *would have been wrong if false*. A claim like "Mike is the project owner" is technically unverified in this session but harmless if wrong.
- Don't include claims that explicitly noted their confidence level (e.g., "I'd guess..." or "probably..."). Those are already marked.
- Don't perform humility. "I should be more careful" is not useful output. "Here are 3 specific claims I should have verified" is useful output.
- Don't audit the USER's claims. Only your own.

## Output format

Two sections, both mandatory:

```
## Glass-castle audit

### Findings
1. [probable, presented as verified] "..."
   Source: turn N
   Verify with: <check>

2. [imagined, presented as verified] "..."
   Source: turn N  
   Verify with: <check>

### Honest summary
<one line: "Found N issues" or "No issues observed">
```

If there are zero findings, the audit is one line: "No glass-castle issues observed in this session." Don't pad it.
