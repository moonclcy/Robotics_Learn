# Repository Guidelines

## Project Structure & Module Organization

This repository contains a Codex skill for academic paper reading and paper-vault maintenance.

- `SKILL.md` defines the agent-facing workflow and behavioral contract.
- `README.md` is the human-facing usage guide.
- `scripts/` contains helper CLIs for metadata ingestion, figure extraction, TeX source handling, diagnostics, and vault maintenance.
- `tests/test_scripts.py` contains focused `unittest` coverage for the helper scripts.
- `references/` stores optional guidance loaded only for relevant tasks.
- `agents/openai.yaml` stores UI-facing skill metadata.

## Build, Test, and Development Commands

Run commands from the repository root.

```bash
python3 -m unittest discover -s tests
```

Runs the full test suite.

```bash
python3 -m py_compile scripts/*.py tests/*.py
```

Checks Python syntax without executing workflows.

```bash
python3 scripts/doctor.py
```

Checks local readiness and reports JSON diagnostics.

```bash
python3 scripts/ingest_paper.py /absolute/path/to/paper.pdf --out-dir /tmp/paper-work
```

Smoke-tests metadata extraction against a local PDF path.

## Coding Style & Naming Conventions

Use Python 3 with standard-library-first dependencies unless a new dependency is clearly justified. Follow the existing style: 4-space indentation, `snake_case` functions and variables, `Path` for filesystem work, `argparse` for CLIs, JSON payloads for script output, and type hints where they improve clarity. Keep Markdown concise and operational. Put reusable agent instructions in `SKILL.md`, human usage details in `README.md`, and task-specific guidance in `references/`.

## Testing Guidelines

Tests use Python `unittest`. Name new test files `test_*.py` and test methods `test_*`. Prefer temporary directories and synthetic fixtures over real user vaults, PDFs, or network-only inputs. Cover idempotence for vault/index updates and graceful fallback behavior for extraction failures. Run the unit test and syntax-check commands before opening a PR.

## Commit & Pull Request Guidelines

Recent commits use short imperative subjects such as `Add usage instructions to README`, `Fix paper-reading workflow contracts`, and occasional conventional prefixes like `feat:`. Keep subjects concise and focused on the behavior changed. PRs should explain the workflow impact, list commands run, mention any changed script flags or output schema, and include sample paths or artifacts when figure or vault behavior changes.

## Security & Configuration Tips

Do not commit personal paper vault contents, copyrighted PDFs, generated extraction artifacts, or local absolute paths unless they are intentional test fixtures. Prefer source images over PDF crops when arXiv source is available, but treat all extracted figures as candidates until reviewed.
