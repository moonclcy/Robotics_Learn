# Vault Organization

Use this reference only when the user explicitly asks to organize, tidy, rebuild indexes, audit, check, repair, or manage an existing paper note library or paper vault.

Do not run full-vault organization during ordinary reading, paper search, or single-note creation. For single-paper writes, use `scripts/maintain_library.py`; for full-library management, use `scripts/organize_library.py`.

## Scope

Allowed by default:

- Rebuild managed navigation pages under `papers/navigation/`.
- Scan `papers/metadata/*.json` and `papers/notes/*.md`.
- Report duplicate dedupe keys and missing metadata, notes, PDFs, assets, or organization fields.
- Create or update `papers/navigation/Library Health.md`.

Not allowed unless the user explicitly asks:

- Delete notes, PDFs, metadata, or assets.
- Move existing user files.
- Rewrite note bodies.
- Infer detailed paper content by rereading PDFs.

## Vault Resolution

Resolve the vault in this order:

1. Explicit user-provided path or `--vault`.
2. `PAPER_READING_VAULT`.
3. `PAPER_NOTE_VAULT`.
4. Existing vault marker in the current directory or parents: `papers/notes/`, `papers/navigation/`, root `Papers Index.md`, or `.obsidian/`.
5. `paper-vault/` under the current workspace.

If multiple plausible vaults are visible and the requested operation would affect many files, ask before proceeding.

## Managed Layout

Use the broad folder layout:

```text
paper-vault/
└── papers/
    ├── notes/
    ├── metadata/
    ├── pdfs/
    ├── assets/
    └── navigation/
```

Managed navigation pages:

- `Papers Index.md`
- `By Topic.md`
- `By Method.md`
- `By Year.md`
- `By Venue.md`
- `By Status.md`
- `By Project.md`
- `By Priority.md`
- `Library Health.md`

## Metadata Rules

Prefer metadata JSON over note-derived fields. For note-only entries, use Markdown frontmatter first, then the first `# Heading`, then the note filename.

Use stable dedupe keys:

- `arxiv:<id-without-version>` when `arxiv_id` is available.
- `doi:<lowercase-doi>` when DOI is available.
- Existing `dedupe_key` when present.
- `local:<note-slug>` as fallback.

Missing organization fields should be reported, not invented. Navigation buckets should use `unknown` for missing topic, method, year, venue, status, project, or priority.

## Navigation Rules

Navigation pages must be pure Markdown and idempotent. Use one entry per dedupe key per page. Re-running organization should not duplicate entries.

Use Obsidian wiki links to notes:

```markdown
[[papers/notes/<slug>|<title>]]
```

Each entry should keep a dedupe marker:

```markdown
<!-- dedupe: <dedupe-key> -->
```

## Health Report

The health report should summarize:

- Entry count.
- Metadata count.
- Note-only count.
- Duplicate dedupe groups.
- Invalid metadata JSON files.
- Entries missing metadata, note, PDF, or assets.
- Entries missing organization fields.

Keep the report diagnostic and non-destructive. It should tell the user what needs attention without changing paper content.
