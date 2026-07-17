# paper-reading

Codex skill for discovering, reading, explaining, summarizing, and organizing academic papers.

The skill is optimized for research-direction-aware paper discovery, Chinese Markdown notes, slow paper walkthroughs, robotics/VLA papers, figure-aware reading, arXiv/PDF source handling, and Obsidian-style paper vault maintenance.

## What This Skill Covers

- Build a reading map before deep explanation.
- Recommend paper candidates from the user's research direction, current question, and paper-vault history.
- Keep paper facts, verified results, inference, and engineering advice separate.
- Produce durable Markdown notes in Simplified Chinese by default.
- Use paper figures conservatively, prioritizing framework diagrams, architecture diagrams, and key result figures.
- Prefer source images for paper figures and Markdown tables for result tables.
- Maintain paper vault notes, metadata, PDFs, assets, and navigation files when requested.
- Organize an existing paper vault only when explicitly asked, rebuilding navigation pages and writing a non-destructive health report.

## Usage

### In Codex

Use this skill when the task is about understanding or organizing an academic paper. Reference it directly when you want to force the workflow:

```text
Use $paper-reading to read this paper slowly: https://arxiv.org/abs/<arxiv-id>
```

Useful prompt shapes:

```text
Use $paper-reading to read this local PDF slowly. Start with a reading map, then explain each section in Chinese.
```

```text
Use $paper-reading to turn this paper into a detailed Chinese Markdown note with the key framework and result figures placed near the relevant explanations.
```

```text
Use $paper-reading to recommend papers worth reading for this VLA post-training question. Use my paper vault as reading history and explain why each candidate matters instead of giving a raw link list.
```

```text
Use $paper-reading to find recent papers related to my current robotics direction. Separate top-venue work, mature arXiv work, and early preprints, then suggest which ones deserve slow reading.
```

```text
Use $paper-reading to maintain my paper vault for this paper: extract metadata, save the note, keep the PDF/assets, and update navigation.
```

```text
Use $paper-reading to organize my paper vault. Rebuild the navigation pages, check missing metadata/PDF/assets, and report duplicate entries without moving or deleting files.
```

Do not use this skill for pure presentation formatting when the paper content is already understood. Keep Markdown as the canonical output and apply presentation enhancement only as a separate optional step.

### Running Helper Scripts

Run scripts from the repository root. Replace the placeholder variables with real local paths or paper IDs before running commands.

```bash
PAPER=/absolute/path/to/paper.pdf
WORK=/absolute/path/to/work-dir
VAULT=/absolute/path/to/paper-vault
ARXIV_ID=replace-with-arxiv-id
```

Check local readiness:

```bash
python3 scripts/doctor.py --vault "$VAULT"
```

Extract metadata from an arXiv URL/ID, PDF URL, or local PDF:

```bash
python3 scripts/ingest_paper.py "$PAPER" --out-dir "$WORK"
```

Fetch arXiv source and prepare source image assets when available:

```bash
python3 scripts/extract_tex_source.py "$ARXIV_ID" --out-dir "$WORK/source" --convert-images
```

Generate conservative figure candidates from a local PDF:

```bash
python3 scripts/extract_figures.py "$PAPER" --out-dir "$WORK/figures" --pages 1-5
```

For important PDF-only figures, provide a reviewed manual crop manifest instead of using full-page screenshots:

```json
{
  "figures": [
    {
      "page": 3,
      "label": "framework",
      "caption": "Framework overview",
      "bbox": {"x": 120, "y": 180, "width": 1200, "height": 760}
    }
  ]
}
```

```bash
python3 scripts/extract_figures.py "$PAPER" --out-dir "$WORK/figures" --pages 3 --dpi 240 --manifest "$WORK/figures/manifest.json"
```

For result tables, ablations, benchmark comparisons, or small-font PDF tables, transcribe the key values into Markdown by default. Use cropped screenshots only as supporting evidence after checking that labels and numbers are readable.

Maintain a paper vault after metadata and note files are ready:

```bash
python3 scripts/maintain_library.py \
  --vault "$VAULT" \
  --metadata "$WORK/metadata.json" \
  --note "$WORK/note.md" \
  --pdf "$PAPER"
```

Organize an existing paper vault only when you explicitly want library management:

```bash
python3 scripts/organize_library.py --vault "$VAULT"
```

Treat extracted figures as candidates. Prefer source assets from `extract_tex_source.py --convert-images` when available, review rendered/cropped figures before inserting them, and use a manual crop manifest when automatic extraction is weak.

## Repository Layout

```text
.
|-- SKILL.md                  # Skill trigger metadata and core workflow
|-- agents/openai.yaml        # UI-facing skill metadata
|-- references/               # Optional guidance loaded only when needed
|-- scripts/                  # Helper scripts for metadata, figures, TeX source, and vault maintenance
`-- tests/test_scripts.py     # Focused regression tests for helper scripts
```

## Helper Scripts

- `scripts/doctor.py` checks local tooling, vault writability, and optional network readiness.
- `scripts/ingest_paper.py` extracts or normalizes paper metadata.
- `scripts/extract_tex_source.py` fetches and indexes arXiv source assets when available.
- `scripts/extract_figures.py` generates candidate figure assets from PDFs.
- `scripts/maintain_library.py` updates vault notes, metadata, PDFs, assets, index, and navigation files.
- `scripts/organize_library.py` rebuilds vault navigation pages and writes a non-destructive library health report for explicit organization requests.

## Validation

Run the focused test suite from the repository root:

```bash
python3 -m unittest tests/test_scripts.py
```

Run the local readiness check:

```bash
python3 scripts/doctor.py
```

## Maintenance Notes

- Keep `SKILL.md` concise and focused on agent instructions.
- Put detailed style guidance or failure-mode notes under `references/`.
- Prefer deterministic helper scripts for fragile or repeatable operations.
- Keep Markdown as the canonical note format; presentation enhancement should remain optional and capability-driven.
