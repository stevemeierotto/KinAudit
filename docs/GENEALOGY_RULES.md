# KinAudit Genealogy Rules

## 1. Purpose

This document defines genealogy-domain rules that KinAudit implementations must
preserve.

These rules exist to prevent software convenience from changing the meaning of
genealogical information.

They apply regardless of which genealogy provider or record source supplied the
data.

If an implementation conflicts with these rules, the implementation should be
changed rather than silently weakening the rule.

---

## 2. Fundamental Principle

KinAudit assists genealogical research.

KinAudit does not automatically determine genealogical truth.

The system must distinguish between:

1. what a source claims
2. what KinAudit detects
3. what a researcher concludes

These are separate layers of information.

---

## 3. The Three-Layer Rule

### Source Says

This represents information obtained from an external source.

Example:

```text
FamilySearch profile ABCD-123 identifies John Example
as the father of William Example.
```

KinAudit records that as a source claim.

It does not automatically mean the relationship has been independently proven.

### KinAudit Detects

KinAudit may analyze source information.

Example:

```text
John Example's recorded birth date would make him
approximately 12 years old when William Example was born.
```

That is a KinAudit finding.

KinAudit should preserve the original source information while flagging the
chronology concern.

### Human Concludes

After reviewing evidence, a researcher may decide:

```text
The relationship is probably incorrect.
```

or:

```text
The birth date appears incorrect, but the relationship is supported.
```

That decision is a human research conclusion.

KinAudit must not collapse these three layers into one field or status.

---

## 4. Person Identity

Names do not establish identity.

Two people must not be merged solely because they have:

- identical names
- similar names
- identical birth years
- similar dates
- matching locations
- matching spouses
- apparently compatible family relationships

Historical genealogy contains repeated names frequently.

Examples such as multiple people named:

- Gerald Fitzgerald
- James Stewart
- John Morgan

must be assumed to represent distinct people until evidence establishes
otherwise.

---

## 5. External Identifiers

External provider IDs must be preserved exactly.

For example:

```text
L66G-X33
```

must not be:

- regenerated
- reformatted
- normalized into another value
- assigned to another person because names appear similar

The combination of provider and provider ID identifies an external profile.

Example:

```text
provider = FamilySearch
external_id = L66G-X33
```

The same textual ID from another provider is not automatically the same external
identity.

---

## 6. Canonical Identity vs External Identity

KinAudit may eventually associate several external records with one canonical
person.

That association must remain traceable.

Conceptually:

```text
KinAudit Person
    |
    +-- FamilySearch identity
    +-- Archive record
    +-- Census record
    +-- Cemetery record
```

The existence of similar external records does not itself prove that they
represent the same person.

Potential matches should remain candidates until resolved according to the
research workflow.

---

## 7. Relationships Are Claims

A parent-child relationship obtained from an external tree is initially a claim
from that source.

KinAudit should preserve:

- who the relationship connects
- relationship type
- provider/source
- external identifiers where available
- retrieval information
- review state
- supporting or conflicting evidence when available

A displayed relationship must not automatically be represented as independently
verified genealogy.

---

## 8. Never Infer Parentage From Compatibility Alone

KinAudit must never establish a parent merely because:

- surname matches
- names are similar
- dates appear possible
- people lived in the same location
- another tree contains the relationship
- spouses appear compatible
- the candidate appears to be the most likely person

These facts may contribute evidence to a research case.

They do not independently establish parentage.

---

## 9. Preserve Source Data

KinAudit should not silently "fix" external data.

If a source reports:

```text
Parent born: 1805
Child born: 1817
```

KinAudit may flag the relationship as chronologically questionable.

It must not silently change:

```text
1805
```

to a date that makes the relationship more plausible.

Source claims and KinAudit findings must remain separately recoverable.

---

## 10. Missing Data Is Not Conflicting Data

KinAudit must distinguish absence from contradiction.

These are different:

```text
Birth date unknown
```

and:

```text
Source A says 1812
Source B says 1821
```

Likewise:

```text
Father unknown
```

is different from:

```text
Source A identifies John
Source B identifies William
```

Missing information should not automatically generate a contradiction.

---

## 11. Direct-Ancestor Traversal

When performing direct-ancestor analysis, KinAudit follows parent relationships
upward from the selected starting person.

Conceptually:

```text
person
├── mother
│   ├── mother
│   └── father
└── father
    ├── mother
    └── father
```

Descendants of siblings are not part of direct-ancestor traversal unless a
different research mode explicitly requests them.

The traversal algorithm must not silently expand into collateral descendant
lines.

---

## 12. Traversal Depth

Users may restrict ancestor traversal to a selected number of generations.

When traversal stops because that configured depth has been reached, KinAudit
must record that condition as a traversal boundary.

It must not call the person a genealogical dead end merely because KinAudit was
instructed to stop there.

Example:

```text
DEPTH_BOUNDARY
```

is different from:

```text
BOTH_PARENTS_MISSING
```

---

## 13. Ancestry Gaps

An ancestry gap occurs when available information does not continue an expected
direct ancestral relationship.

Potential classifications may include:

- `MISSING_FATHER`
- `MISSING_MOTHER`
- `BOTH_PARENTS_MISSING`
- `INCOMPLETE_PROFILE`
- `QUESTIONABLE_RELATIONSHIP`

The classification system may evolve.

KinAudit should retain enough information to explain why a branch received its
classification.

---

## 14. Brick Walls

"Brick wall" should not be used merely because a traversal stopped.

A research brick wall generally implies that ancestry cannot currently be
continued despite investigation.

KinAudit may initially detect an ancestry gap.

A researcher may later classify that gap as a genuine research brick wall.

This distinction prevents software from overstating what has been established.

---

## 15. Convergence

If two ancestral routes reach the same established identity, KinAudit should
treat this as convergence.

Example:

```text
        ┌── route A ──┐
Person ─┤             ├── Ancestor X
        └── route B ──┘
```

Ancestor X should not be duplicated merely because there are two routes.

However, both routes must remain independently reconstructable.

---

## 16. Pedigree Collapse

Pedigree collapse occurs when the same ancestor occupies multiple positions in a
person's ancestry.

KinAudit's data structures and algorithms must allow this naturally.

Do not assume that:

```text
2^generation
```

equals the number of unique ancestors.

Tree position and unique person identity are different concepts.

---

## 17. Path Preservation

An ancestral path is meaningful information.

If KinAudit discovers:

```text
Person
→ A
→ B
→ C
→ Ancestor X
```

and separately:

```text
Person
→ D
→ E
→ F
→ Ancestor X
```

both routes must remain recoverable.

Deduplicating Ancestor X must not destroy either path.

---

## 18. Possible Duplicates

KinAudit may identify possible duplicate people.

Example reasons:

- similar names
- overlapping dates
- same spouse
- same parents
- same locations
- similar external records

The result should be represented as a finding or candidate match.

It must not trigger an automatic merge unless a separately approved rule or
human review establishes identity.

---

## 19. Chronology Analysis

KinAudit may perform deterministic chronology checks.

Possible findings include:

- parent apparently too young at child's birth
- parent apparently implausibly old at child's birth
- child born after recorded death of parent
- marriage after recorded death
- inconsistent event ordering
- overlapping incompatible dates

Chronology thresholds should eventually be configurable and documented.

A chronology warning means:

```text
Review this relationship or its dates.
```

It does not necessarily mean:

```text
This relationship is false.
```

Historical records frequently contain uncertain, estimated, or incorrect dates.

---

## 20. Approximate Dates

Genealogy data frequently contains dates such as:

- about 1810
- before 1700
- after 1750
- between 1800 and 1810

KinAudit should eventually model uncertainty rather than pretending all dates
are exact.

Approximate dates should not be silently converted into exact dates for
analysis.

Analysis should account for known uncertainty where practical.

---

## 21. Evidence

Evidence should remain connected to the claim or research question it supports
or challenges.

KinAudit should eventually distinguish concepts such as:

- supporting evidence
- conflicting evidence
- contextual evidence
- unresolved evidence

The presence of one source does not automatically make a claim proven.

---

## 22. Provenance

Genealogical information should retain provenance whenever available.

Useful provenance includes:

- provider
- record/profile identifier
- source URL or locator when available
- retrieval timestamp
- source type
- original claim
- related people
- related relationship
- analysis derived from the information

A researcher should be able to determine where a KinAudit claim or finding came
from.

---

## 23. Source Changes

External genealogy trees are mutable.

If KinAudit previously observed:

```text
A -> parent -> B
```

and a later retrieval reports:

```text
A -> parent -> C
```

KinAudit should not silently erase the fact that B was previously reported.

The system should eventually preserve enough history to identify that the
external source changed.

---

## 24. Research Cases

An unresolved genealogy question should be representable as a research case.

Examples:

- Who was this person's father?
- Are these two John Smith profiles the same person?
- Which birth date is supported by stronger evidence?
- Is this parent-child relationship chronologically possible?

Research cases should have explicit states.

Possible future states include:

- `OPEN`
- `IN_RESEARCH`
- `NEEDS_REVIEW`
- `RESOLVED`
- `REJECTED`

Exact workflow names may change later.

---

## 25. Candidate Relationships

External research may identify a candidate parent or other relationship.

Candidate relationships must remain distinct from accepted relationships.

For example:

```text
Candidate father:
John Example

Reason:
Same county
Compatible age
Matching surname
Referenced by obituary
```

KinAudit may present the evidence.

KinAudit must not automatically convert that candidate into established
parentage.

---

## 26. Human Review

Human review is a first-class part of KinAudit.

Researchers should eventually be able to record decisions such as:

- `ACCEPTED`
- `REJECTED`
- `NEEDS_MORE_RESEARCH`

A decision should preserve:

- what was reviewed
- relevant evidence
- reviewer
- timestamp
- optional notes/reasoning

Review history should not be silently destroyed when new evidence arrives.

---

## 27. External Tree Modification

KinAudit must not automatically modify an external genealogy tree.

If write support is introduced later, every proposed change must remain
deliberate and reviewable.

At minimum:

```text
KinAudit detects issue
        ↓
Researcher reviews issue
        ↓
Researcher reviews proposed change
        ↓
Researcher explicitly authorizes write
        ↓
External change occurs
        ↓
Action is recorded
```

Background analysis must never directly trigger an external genealogy edit.

---

## 28. Source Independence

Genealogy rules apply regardless of provider.

Do not encode rules such as:

```text
FamilySearch says this, therefore it is true.
```

Instead:

```text
FamilySearch claims X.
Another provider may claim Y.
```

KinAudit's responsibility is to preserve those claims, analyze them, organize
evidence, and support human review.

---

## 29. Deterministic Analysis

When genealogy analysis can be performed deterministically, use deterministic
logic.

Examples:

- graph traversal
- exact external-ID comparison
- generation calculation
- missing-parent detection
- path reconstruction
- convergence detection
- chronology arithmetic

These operations should produce reproducible results.

---

## 30. Model-Assisted Research

Future language-model or computer-intelligence assistance may help interpret
unstructured evidence.

Possible uses include:

- obituary interpretation
- historical-record summaries
- evidence comparison
- research summaries
- research suggestions

Model-generated interpretations must be labeled as analysis.

They are not primary-source evidence.

A model must not independently promote a candidate person or relationship to
accepted genealogical fact.

---

## 31. Known Acceptance Scenarios

KinAudit should eventually maintain test fixtures representing difficult real
genealogy situations.

### Repeated names

Several generations may contain people with the same or nearly identical name.

Expected behavior:

Do not collapse them based on name similarity.

### Multiple routes to one ancestor

A person may reach the same ancestor through separate lines.

Expected behavior:

One established identity may be represented canonically while every ancestral
route remains reconstructable.

### Missing parent

One or both parents may be absent.

Expected behavior:

Record an ancestry gap without inventing a relationship.

### Chronology concern

Dates may make a displayed relationship questionable.

Expected behavior:

Preserve source data and create a finding.

### Conflicting sources

Two sources may provide incompatible claims.

Expected behavior:

Preserve both claims and expose the conflict for review.

### Generation boundary

Traversal may stop because the researcher requested a limited depth.

Expected behavior:

Record a traversal boundary, not a genealogical dead end.

---

## 32. Core Rule

When uncertainty exists, preserve it.

Do not make the database cleaner by making the genealogy less truthful.

KinAudit should prefer:

```text
We do not know yet.
```

over:

```text
The software selected the most likely answer.
```

The purpose of KinAudit is to help researchers discover and evaluate evidence,
not to hide uncertainty from them.
