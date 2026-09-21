# Paper Discovery

Use this reference when recommending papers for a research direction, current project question, or paper-vault gap. The goal is a curated candidate set, not a broad search dump.

## Discovery Inputs

Collect the smallest useful context before searching:

- Current question or research direction.
- Existing notes, vault metadata, navigation pages, or user-provided reading history.
- Scope constraints: field, method family, venue tier, year range, arXiv freshness, and whether the user wants deep reading candidates or lightweight awareness.
- Papers already read or explicitly out of scope.

If the user has a vault, scan notes and metadata for recurring terms, venues, methods, datasets, and unread/read status. Treat this as preference evidence, not as a hard filter.

## Source Quality

Prefer sources in this order when practical:

1. Official conference, journal, publisher, arXiv, OpenReview, ACL Anthology, PMLR, IEEE, ACM, NeurIPS, ICLR, ICML, CVPR, RSS, CoRL, ICRA, IROS, RA-L, or project pages.
2. Author pages, lab pages, released code, datasets, and benchmark pages that confirm paper identity or artifacts.
3. Aggregators only as search aids. Do not treat them as authoritative for venue, claims, or recency.

Separate source types in the recommendation:

- Peer-reviewed or accepted top venue.
- Workshop or non-archival venue.
- arXiv preprint with strong evidence.
- Early arXiv preprint with limited validation.
- Low-confidence or weakly evidenced candidate.

## Filtering Heuristics

Score candidates qualitatively instead of pretending to produce a precise numeric ranking.

- Field relevance: Does it directly match the user's direction, or only share keywords?
- Problem match: Does it answer the user's current question or provide a missing background step?
- Method value: Does it introduce a mechanism, dataset, benchmark, or ablation pattern worth studying?
- Experimental depth: Are tasks, baselines, ablations, datasets, and failure cases sufficient for the paper type?
- Source authority: Is the venue, author group, artifact, or citation trail credible?
- Novelty versus redundancy: Does the user already have a similar paper in the vault?
- Reading value: Choose 精读, 略读, 收藏待看, or 暂不优先.

Demote candidates when they only match keywords, lack experimental evidence for strong claims, duplicate an already-read paper without adding a new angle, or require unverifiable assumptions.

## Output Shape

Return a short candidate list grouped by direction. For each candidate, include:

- Recommendation level: 精读 / 略读 / 收藏待看 / 暂不优先.
- Paper identity: title, year, venue or source, and stable link.
- Direction: the research bucket it belongs to.
- Why recommended: the specific value for this user.
- Current-question link: how it helps the active problem.
- Evidence and caveats: what is verified, what is only inferred, and what still needs checking.
- Next action: read fully, inspect experiments, compare with a known paper, add to vault, or skip.

Keep the prose concise and decision-oriented. Avoid large tables unless the user asks for a table or many candidates.

## Fact Boundaries

Do not invent venue status, code availability, dataset usage, benchmark results, citation counts, or acceptance details. If a source does not show the detail, say it needs verification.

When using web search for recent work, cite the sources used and prefer current official pages over memory. If recency is not essential but sources are unavailable, clearly mark the result as a preliminary candidate.
