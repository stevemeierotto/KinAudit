# KinAudit Architecture

## 1. Purpose

KinAudit is a source-neutral genealogy research, auditing, and analysis platform.

It is intended to help researchers investigate ancestral trees rather than simply
display them.

KinAudit should eventually be able to:

- retrieve genealogy information from multiple sources
- build and preserve ancestral paths
- identify missing parents and ancestral dead ends
- detect chronology problems and other inconsistencies
- detect convergence and pedigree collapse
- compare the ancestry of two people
- preserve evidence and provenance
- track unresolved genealogy questions as research cases
- assist researchers in locating evidence from additional sources
- preserve human review and conclusions separately from source claims

FamilySearch is expected to be the first genealogy provider integrated with
KinAudit, but FamilySearch is only a source.

The internal architecture must remain independent of any individual provider.

---

## 2. Architectural Principles

KinAudit should favor:

1. source-neutral domain models
2. deterministic analysis where practical
3. explicit provenance
4. reproducible results
5. preservation of conflicting information
6. human review of genealogical conclusions
7. clear boundaries between external sources and internal data
8. simple architecture before distributed architecture
9. testable behavior
10. preservation of historical source state when practical

KinAudit is not intended to determine genealogical truth automatically.

Its job is to organize information, analyze relationships, expose problems,
preserve evidence, and help a researcher make informed decisions.

---

## 3. Initial Technology Stack

The planned initial stack is:

### Frontend

- React
- Vite
- REST/JSON communication with the backend

### Backend

- Python
- FastAPI

### Persistence

- PostgreSQL
- SQLAlchemy
- Alembic migrations

### Development / Deployment

- Docker
- Docker Compose

The initial application should remain a small modular system.

Do not introduce microservices, message brokers, distributed queues, or other
infrastructure until a concrete requirement justifies them.

---

## 4. High-Level Architecture

The intended architecture is:

```text
┌─────────────────────────────┐
│        React / Vite         │
│          Frontend           │
└──────────────┬──────────────┘
               │
               │ REST / JSON
               ▼
┌─────────────────────────────┐
│          FastAPI            │
│           Backend           │
├─────────────────────────────┤
│ Application Services        │
│ Genealogy Domain            │
│ Analysis Engine             │
│ Research Workflow           │
└───────┬─────────────┬───────┘
        │             │
        │             │
        ▼             ▼
┌──────────────┐  ┌─────────────────┐
│ PostgreSQL   │  │ Source Adapters │
└──────────────┘  └────────┬────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        FamilySearch   Other APIs    Public Records
```

The frontend must not communicate directly with external genealogy providers.

All external data enters KinAudit through the backend.

---

## 5. Major Architectural Layers

### 5.1 Frontend

The frontend presents KinAudit data and workflows to the researcher.

Expected future interfaces include:

- ancestry dashboard
- person/profile view
- ancestral path viewer
- ancestry gap report
- research queue
- chronology findings
- convergence viewer
- two-person ancestry comparison
- evidence viewer
- research-case workspace

The frontend should consume KinAudit's internal API.

It should not need to understand FamilySearch-specific API structures.

### 5.2 API Layer

FastAPI provides the application boundary between the frontend and backend.

The API layer should be responsible for:

- request validation
- authentication/authorization when introduced
- invoking application services
- serializing KinAudit responses
- returning appropriate errors

The API layer should not contain genealogy algorithms or provider-specific
retrieval logic.

### 5.3 Application Services

Application services coordinate use cases.

Examples may eventually include:

- importing ancestry
- running an ancestry audit
- creating research cases
- comparing two people's ancestry
- retrieving a reconstructed ancestral path
- reviewing findings
- attaching evidence
- refreshing data from an external source

Application services may coordinate domain logic, persistence, analysis, and
source adapters.

They should not duplicate those responsibilities.

---

## 6. Source Adapter Layer

Every external genealogy or records provider must be isolated behind an adapter.

The first planned adapter is FamilySearch.

Future adapters may include sources such as:

- genealogy databases
- archives
- census collections
- vital-record collections
- cemetery databases
- newspaper/obituary collections
- other supported public-record services
- user-imported datasets

Provider-specific behavior belongs inside its adapter, including:

- authentication
- endpoints
- request formatting
- response parsing
- pagination
- rate-limit handling
- provider errors
- provider identifiers
- provider-specific metadata

The rest of KinAudit should operate primarily on canonical KinAudit objects.

A provider must not become the application's internal data model.

---

## 7. Normalization Boundary

External information must be normalized before entering the core genealogy
domain.

Conceptually:

```text
External response
      ↓
Provider adapter
      ↓
Normalization
      ↓
Canonical KinAudit model
      ↓
Persistence / analysis
```

Normalization must not destroy the original meaning or provenance of the
external information.

Where useful, raw or source-specific information may be retained alongside
normalized data for auditability.

Normalization is not permission to silently resolve conflicts.

---

## 8. Canonical Domain

The exact database schema will be designed separately, but KinAudit is expected
to require concepts similar to the following.

### Person

Represents a person within KinAudit.

A person may have identities in multiple external systems.

### ExternalIdentity

Associates a KinAudit person with an identity supplied by an external source.

Example:

```text
provider: FamilySearch
external_id: L66G-X33
```

External IDs must be preserved exactly.

### Relationship

Represents a genealogical relationship asserted by a source or accepted through
research.

Relationships must carry enough provenance to distinguish where the claim came
from and its review state.

### AncestralPath

Represents a specific route through relationships.

Paths are important because the same ancestor may be reached through multiple
routes.

KinAudit must not discard this information merely because the final person is
the same.

### Source

Identifies the origin of information.

### Evidence

Represents information relevant to a genealogical claim or research question.

### Finding

Represents something KinAudit detected.

Examples:

- missing parent
- chronology concern
- possible identity conflict
- convergence
- incomplete information

A finding is not automatically a genealogical conclusion.

### ResearchCase

Represents an unresolved research question.

Example:

Who were the parents of Jane Example?

### ReviewDecision

Represents a human decision regarding a finding, candidate relationship, or
piece of evidence.

### Snapshot

Represents the state of external information at a particular point in time.

This becomes important because shared genealogy trees can change.

---

## 9. Analysis Engine

KinAudit's analysis engine should initially be deterministic.

Problems that can be solved reliably with ordinary algorithms should not require
an LLM.

Expected capabilities include:

- direct-ancestor traversal
- ancestry gap detection
- chronology checks
- convergence detection
- path reconstruction
- ancestry comparison
- unresolved-relationship detection
- duplicate-candidate detection

Potential interfaces might eventually resemble:

```text
find_ancestry_gaps(...)
check_chronology(...)
find_convergences(...)
reconstruct_path(...)
compare_ancestry(...)
find_unresolved_relationships(...)
```

These names are illustrative and are not currently fixed API contracts.

---

## 10. Ancestor Gap Analysis

Ancestor Gap Analysis is planned as an early KinAudit capability.

Given a starting person and traversal depth, KinAudit should inspect direct
ancestry and identify where further research may be required.

Potential classifications include:

- `MISSING_FATHER`
- `MISSING_MOTHER`
- `BOTH_PARENTS_MISSING`
- `INCOMPLETE_PROFILE`
- `QUESTIONABLE_RELATIONSHIP`
- `DEPTH_BOUNDARY`

These classifications may evolve as the data model is designed.

A traversal boundary is not a genealogy dead end.

KinAudit must distinguish:

The source does not provide another ancestor.

from:

KinAudit stopped because the requested traversal depth was reached.

Convergence is also not a dead end.

---

## 11. Paths and Convergence

Genealogy is a graph, not merely a tree.

The same person may legitimately appear in multiple ancestral paths.

For example:

```text
                    ┌── Path A ──┐
Starting Person ────┤            ├── Ancestor X
                    └── Path B ──┘
```

KinAudit may maintain one canonical representation of Ancestor X while
preserving both routes by which Ancestor X was reached.

This is necessary for:

- pedigree collapse
- repeated ancestral connections
- path reconstruction
- relationship comparison
- Bloodlines-style route analysis

Path information must not be lost during deduplication.

---

## 12. Provenance

Provenance is a core architectural requirement.

For externally obtained information, KinAudit should eventually be capable of
answering:

- Which provider supplied this?
- Which record/profile supplied it?
- When was it retrieved?
- What did the provider claim?
- Has that claim changed?
- Which KinAudit finding used the information?
- Has a researcher reviewed it?

Provenance should not be treated as an optional feature to bolt on later.

The data model should be designed so provenance can be retained from the
beginning.

---

## 13. Snapshots and Change Tracking

External shared trees can change.

A relationship visible today may be edited tomorrow.

KinAudit should eventually support snapshots or equivalent historical records
so a researcher can determine:

What did the source say when this analysis was performed?

Refreshing external information must not silently destroy historically relevant
research state.

The precise snapshot implementation will be designed later.

---

## 14. Research Workflow

KinAudit should eventually support a workflow similar to:

```text
Source claim
     ↓
KinAudit analysis
     ↓
Finding
     ↓
Research case
     ↓
Additional evidence
     ↓
Human review
     ↓
Research decision
```

The system must preserve the distinction between every stage.

An algorithmic finding does not automatically become an accepted genealogical
relationship.

---

## 15. External Research

A later phase may allow KinAudit to investigate unresolved ancestry using
additional sources.

For example:

```text
Missing parent
     ↓
Create research case
     ↓
Search available sources
     ↓
Candidate person/relationship
     ↓
Collect evidence
     ↓
Human review
```

Candidate relationships must remain candidates until reviewed.

KinAudit must not automatically insert a candidate parent merely because names,
dates, or locations appear compatible.

---

## 16. External Writes

Initial development should assume external genealogy sources are read-only.

Any future capability to modify FamilySearch or another provider must be treated
as a separate feature.

External writes must require:

- explicit user initiation
- clear presentation of the proposed change
- human confirmation
- recorded provenance
- an auditable action record

No analysis process should automatically modify an external family tree.

---

## 17. LLM / Computer Intelligence Boundary

KinAudit does not require an LLM for its core genealogy analysis.

Initial traversal, graph analysis, chronology checking, gap detection,
convergence detection, and ID comparison should be deterministic.

Future model-assisted capabilities could include:

- summarizing evidence
- interpreting historical text
- comparing textual records
- explaining research findings
- assisting with research planning

Model output must remain distinguishable from source evidence and human
conclusions.

An LLM must not independently establish identity or parentage.

---

## 18. Initial Repository Direction

The repository may evolve toward a structure such as:

```text
KinAudit/
├── AGENTS.md
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── docs/
│   ├── ARCHITECTURE.md
│   └── GENEALOGY_RULES.md
│
├── frontend/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── analysis/
│   │   ├── database/
│   │   └── sources/
│   │       └── familysearch/
│   │
│   └── tests/
│
└── scripts/
```

This is architectural direction, not a requirement to create empty directories
or abstractions before they are needed.

---

## 19. First Vertical Slice

The first meaningful KinAudit workflow should remain small.

Target:

```text
Starting person
      ↓
Retrieve direct ancestry from source
      ↓
Normalize source data
      ↓
Persist people and relationships
      ↓
Traverse direct ancestry
      ↓
Identify ancestry gaps
      ↓
Return findings
      ↓
Display results
```

This proves the major architectural boundaries without attempting to build the
entire platform.

The exact implementation sequence will be defined before coding begins.

---

## 20. Future Capabilities

Potential later capabilities include:

- interactive ancestral path visualization
- chronology auditing
- convergence visualization
- pedigree-collapse analysis
- comparison between two people's ancestry
- common-ancestor discovery
- research queues
- evidence management
- source contradiction tracking
- historical source snapshots
- external record searches
- candidate-parent research
- research reports
- GEDCOM import/export
- user-supplied evidence
- model-assisted evidence interpretation

These are directions, not current implementation requirements.

---

## 21. Architectural Goal

KinAudit should eventually make it easy for a researcher to ask:

- What does the source claim?
- How did this ancestral path reach this person?
- Where does this line stop?
- Why did KinAudit flag this relationship?
- Are there multiple paths to this ancestor?
- Do two people share ancestry?
- Does the chronology make sense?
- What evidence supports this relationship?
- Has the source changed since I researched it?
- What remains unresolved?

The architecture should make those questions answerable without confusing
source claims, software analysis, and human genealogical judgment.
