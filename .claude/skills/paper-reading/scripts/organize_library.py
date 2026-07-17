#!/usr/bin/env python3
"""Organize an existing paper vault without moving or deleting user files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import maintain_library


FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)


def parse_scalar(value: str) -> object:
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("\"'") for item in inner.split(",") if item.strip()]
    return value.strip("\"'")


def parse_frontmatter(text: str) -> dict[str, object]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    metadata: dict[str, object] = {}
    for raw_line in match.group("body").splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        if key:
            metadata[key] = parse_scalar(value)
    return metadata


def first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def metadata_from_note(note_path: Path) -> dict[str, object]:
    text = note_path.read_text(encoding="utf-8")
    metadata = parse_frontmatter(text)
    title = str(metadata.get("title") or first_heading(text) or note_path.stem).strip()
    slug = str(metadata.get("slug") or note_path.stem).strip()
    dedupe = str(metadata.get("dedupe_key") or metadata.get("arxiv_id") or "").strip()
    if dedupe and not dedupe.startswith(("arxiv:", "doi:", "title-year:", "local:")):
        dedupe = f"arxiv:{dedupe}"
    metadata.setdefault("title", title)
    metadata["slug"] = slug
    metadata["dedupe_key"] = dedupe or f"local:{slug}"
    metadata["note_path"] = str(note_path)
    metadata["source"] = "note"
    return metadata


def normalize_metadata(metadata: dict[str, object], metadata_path: Path | None = None) -> dict[str, object]:
    normalized = dict(metadata)
    slug = str(normalized.get("slug") or normalized.get("note_slug") or "").strip()
    if not slug and metadata_path is not None:
        slug = metadata_path.stem
    if not slug:
        slug = maintain_library.slugify(str(normalized.get("title") or "paper"))
    dedupe = str(normalized.get("dedupe_key") or "").strip()
    if not dedupe:
        arxiv_id = str(normalized.get("arxiv_id") or "").strip()
        doi = str(normalized.get("doi") or "").strip().lower()
        if arxiv_id:
            dedupe = f"arxiv:{re.sub(r'v\\d+$', '', arxiv_id)}"
        elif doi:
            dedupe = f"doi:{doi}"
        else:
            dedupe = f"local:{slug}"
    normalized["slug"] = slug
    normalized["dedupe_key"] = dedupe
    normalized.setdefault("title", slug)
    normalized.setdefault("source", "metadata")
    return normalized


def load_metadata_files(vault: Path) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    entries: list[dict[str, object]] = []
    invalid: list[dict[str, str]] = []
    metadata_dir = vault / "papers" / "metadata"
    for path in sorted(metadata_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            invalid.append({"path": str(path), "error": str(exc)})
            continue
        if not isinstance(payload, dict):
            invalid.append({"path": str(path), "error": "metadata JSON must contain an object"})
            continue
        entry = normalize_metadata(payload, path)
        entry["metadata_path"] = str(path)
        entries.append(entry)
    return entries, invalid


def load_note_entries(vault: Path, existing_slugs: set[str]) -> list[dict[str, object]]:
    notes_dir = vault / "papers" / "notes"
    entries = []
    for path in sorted(notes_dir.glob("*.md")):
        if path.stem in existing_slugs:
            continue
        entries.append(metadata_from_note(path))
    return entries


def merge_entries(entries: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[list[dict[str, object]]]]:
    by_key: dict[str, dict[str, object]] = {}
    duplicates: dict[str, list[dict[str, object]]] = {}
    for entry in entries:
        key = str(entry.get("dedupe_key") or f"local:{entry.get('slug')}")
        if key in by_key:
            duplicates.setdefault(key, [by_key[key]]).append(entry)
            merged = dict(by_key[key])
            for field, value in entry.items():
                if field not in merged or merged[field] in ("", [], None, "unknown"):
                    merged[field] = value
            by_key[key] = merged
        else:
            by_key[key] = entry
    return list(by_key.values()), list(duplicates.values())


def expected_note_path(vault: Path, entry: dict[str, object]) -> Path:
    note_path = entry.get("note_path")
    if note_path:
        path = Path(str(note_path)).expanduser()
        if path.is_absolute():
            return path
        return vault / path
    return vault / "papers" / "notes" / f"{entry['slug']}.md"


def check_entry_assets(vault: Path, entry: dict[str, object]) -> dict[str, object]:
    slug = str(entry["slug"])
    metadata_path = vault / "papers" / "metadata" / f"{slug}.json"
    note_path = expected_note_path(vault, entry)
    pdf_path = vault / "papers" / "pdfs" / f"{slug}.pdf"
    asset_dir = vault / "papers" / "assets" / slug
    missing = []
    if not metadata_path.exists() and entry.get("source") == "note":
        missing.append("metadata")
    if not note_path.exists():
        missing.append("note")
    if not pdf_path.exists() and not entry.get("pdf_path") and not entry.get("pdf_url"):
        missing.append("pdf")
    if not asset_dir.exists():
        missing.append("assets")
    missing_fields = [
        field
        for field in ["title", "year", "venue", "topic", "method", "status", "project", "priority"]
        if not str(entry.get(field) or "").strip()
    ]
    return {
        "slug": slug,
        "dedupe_key": entry["dedupe_key"],
        "missing": missing,
        "missing_fields": missing_fields,
    }


def render_navigation(vault: Path, entries: list[dict[str, object]]) -> list[str]:
    paths = maintain_library.ensure_layout(vault)
    navigation_paths = []
    for filename, heading, _key in maintain_library.NAVIGATION_PAGES:
        path = paths["navigation"] / filename
        path.write_text(f"# {heading}\n", encoding="utf-8")
        navigation_paths.append(str(path))
    for entry in sorted(entries, key=lambda item: (str(item.get("year") or "unknown"), str(item.get("title") or "")), reverse=True):
        slug = str(entry["slug"])
        dedupe = str(entry["dedupe_key"])
        line = maintain_library.render_entry(entry, slug)
        for filename, heading, key in maintain_library.NAVIGATION_PAGES:
            bucket = maintain_library.bucket_value(entry, key)
            maintain_library.upsert_navigation_entry(paths["navigation"] / filename, heading, line, dedupe, bucket)
    return navigation_paths


def organize_vault(vault: str | Path | None = None) -> dict[str, object]:
    vault_path = maintain_library.resolve_vault(str(vault) if vault else None)
    metadata_entries, invalid_metadata = load_metadata_files(vault_path)
    note_entries = load_note_entries(vault_path, {str(item["slug"]) for item in metadata_entries})
    entries, duplicate_groups = merge_entries([*metadata_entries, *note_entries])
    navigation = render_navigation(vault_path, entries)
    checks = [check_entry_assets(vault_path, entry) for entry in entries]
    result = {
        "ok": True,
        "vault": str(vault_path),
        "entry_count": len(entries),
        "metadata_count": len(metadata_entries),
        "note_only_count": len(note_entries),
        "navigation": navigation,
        "duplicates": [
            [{"slug": str(item.get("slug")), "dedupe_key": str(item.get("dedupe_key"))} for item in group]
            for group in duplicate_groups
        ],
        "invalid_metadata": invalid_metadata,
        "checks": checks,
    }
    report_path = vault_path / "papers" / "navigation" / "Library Health.md"
    report_path.write_text(render_health_report(result), encoding="utf-8")
    result["health_report"] = str(report_path)
    return result


def render_health_report(result: dict[str, object]) -> str:
    lines = [
        "# Library Health",
        "",
        f"- **Vault**: {result['vault']}",
        f"- **Entries**: {result['entry_count']}",
        f"- **Metadata entries**: {result['metadata_count']}",
        f"- **Note-only entries**: {result['note_only_count']}",
        "",
        "## Missing Assets Or Fields",
        "",
    ]
    checks = result.get("checks") or []
    any_missing = False
    for check in checks:
        missing = check.get("missing") or []
        missing_fields = check.get("missing_fields") or []
        if not missing and not missing_fields:
            continue
        any_missing = True
        lines.append(f"- `{check['slug']}`: assets={', '.join(missing) or 'none'}; fields={', '.join(missing_fields) or 'none'}")
    if not any_missing:
        lines.append("- No missing assets or required organization fields detected.")
    lines.extend(["", "## Duplicates", ""])
    duplicates = result.get("duplicates") or []
    if not duplicates:
        lines.append("- No duplicate dedupe keys detected.")
    else:
        for group in duplicates:
            lines.append("- " + ", ".join(f"{item['slug']} ({item['dedupe_key']})" for item in group))
    invalid = result.get("invalid_metadata") or []
    lines.extend(["", "## Invalid Metadata", ""])
    if not invalid:
        lines.append("- No invalid metadata JSON files detected.")
    else:
        for item in invalid:
            lines.append(f"- `{item['path']}`: {item['error']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", help="Optional paper-vault root. Defaults to PAPER_READING_VAULT, PAPER_NOTE_VAULT, an existing vault marker, or ./paper-vault.")
    args = parser.parse_args()
    print(json.dumps(organize_vault(args.vault), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
