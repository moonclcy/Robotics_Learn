from __future__ import annotations

import importlib.util
import tarfile
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_script(name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / f"{name}.py"), *args],
        check=False,
        capture_output=True,
        text=True,
    )


class PaperReadingScriptTests(unittest.TestCase):
    def test_arxiv_id_normalization(self) -> None:
        ingest = load_module("ingest_paper")
        self.assertEqual(ingest.normalize_arxiv_id("https://arxiv.org/abs/2402.10329v2"), "2402.10329")
        self.assertEqual(ingest.normalize_arxiv_id("arXiv:cs/0301012v1"), "cs/0301012")
        self.assertIsNone(ingest.normalize_arxiv_id("not-a-paper"))

    def test_doctor_outputs_json(self) -> None:
        result = run_script("doctor")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("ok", payload)
        self.assertIn("local_ok", payload)
        self.assertIn("network_ok", payload)
        self.assertIn("tools", payload)

    def test_ingest_local_pdf_writes_metadata_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "Example Paper.pdf"
            pdf.write_text("placeholder PDF bytes for metadata fallback", encoding="utf-8")
            out_dir = root / "out"

            result = run_script("ingest_paper", str(pdf), "--out-dir", str(out_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            metadata_path = Path(payload["metadata_path"])
            self.assertTrue(metadata_path.exists())
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["title"], "Example Paper")
            self.assertIn("dedupe_key", metadata)
            self.assertIn("slug", metadata)

    def test_maintain_library_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = {
                "title": "Example Paper",
                "year": "2026",
                "venue": "arXiv",
                "status": "reading",
                "slug": "example-paper",
                "dedupe_key": "arxiv:2601.00001",
            }
            metadata_path = root / "metadata.json"
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            note_path = root / "note.md"
            note_path.write_text("# Example Paper\n", encoding="utf-8")
            vault = root / "paper-vault"

            for _ in range(2):
                result = run_script(
                    "maintain_library",
                    "--vault",
                    str(vault),
                    "--metadata",
                    str(metadata_path),
                    "--note",
                    str(note_path),
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            index = vault / "papers" / "navigation" / "Papers Index.md"
            by_year = vault / "papers" / "navigation" / "By Year.md"
            by_topic = vault / "papers" / "navigation" / "By Topic.md"
            by_method = vault / "papers" / "navigation" / "By Method.md"
            by_venue = vault / "papers" / "navigation" / "By Venue.md"
            self.assertEqual(index.read_text(encoding="utf-8").count("<!-- dedupe: arxiv:2601.00001 -->"), 1)
            self.assertEqual(by_year.read_text(encoding="utf-8").count("<!-- dedupe: arxiv:2601.00001 -->"), 1)
            self.assertEqual(by_topic.read_text(encoding="utf-8").count("<!-- dedupe: arxiv:2601.00001 -->"), 1)
            self.assertEqual(by_method.read_text(encoding="utf-8").count("<!-- dedupe: arxiv:2601.00001 -->"), 1)
            self.assertEqual(by_venue.read_text(encoding="utf-8").count("<!-- dedupe: arxiv:2601.00001 -->"), 1)
            self.assertIn("## unknown", by_topic.read_text(encoding="utf-8"))
            self.assertTrue((vault / "papers" / "notes" / "example-paper.md").exists())
            self.assertTrue((vault / "papers" / "metadata" / "example-paper.json").exists())

    def test_maintain_library_resolves_vault_from_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "env-vault"
            metadata = {
                "title": "Env Paper",
                "year": "2026",
                "slug": "env-paper",
                "dedupe_key": "arxiv:2601.00005",
            }
            metadata_path = root / "metadata.json"
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            note_path = root / "note.md"
            note_path.write_text("# Env Paper\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "maintain_library.py"), "--metadata", str(metadata_path), "--note", str(note_path)],
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "PAPER_READING_VAULT": str(vault)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["vault"], str(vault))
            self.assertTrue((vault / "papers" / "navigation" / "By Priority.md").exists())

    def test_manifest_figure_insertion_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = {
                "title": "Figure Paper",
                "year": "2026",
                "slug": "figure-paper",
                "dedupe_key": "arxiv:2601.00002",
            }
            metadata_path = root / "metadata.json"
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            note_path = root / "note.md"
            note_path.write_text("# Figure Paper\n", encoding="utf-8")
            image_path = root / "pipeline.png"
            image_path.write_bytes(b"fake-image")
            figures_path = root / "figures.json"
            figures_path.write_text(
                json.dumps({"assets": [{"path": str(image_path), "label": "pipeline", "caption": "Pipeline"}]}),
                encoding="utf-8",
            )
            vault = root / "paper-vault"

            for _ in range(2):
                result = run_script(
                    "maintain_library",
                    "--vault",
                    str(vault),
                    "--metadata",
                    str(metadata_path),
                    "--note",
                    str(note_path),
                    "--figures",
                    str(figures_path),
                    "--insert-figures",
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            note = (vault / "papers" / "notes" / "figure-paper.md").read_text(encoding="utf-8")
            self.assertEqual(note.count("<!-- figures: arxiv:2601.00002 begin -->"), 1)
            self.assertEqual(note.count("![Pipeline]"), 1)

    def test_source_image_manifest_insertion_preserves_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = {
                "title": "Source Figure Paper",
                "year": "2026",
                "slug": "source-figure-paper",
                "dedupe_key": "arxiv:2601.00003",
            }
            metadata_path = root / "metadata.json"
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            note_path = root / "note.md"
            note_path.write_text("# Source Figure Paper\n", encoding="utf-8")
            image_path = root / "pipeline.png"
            image_path.write_bytes(b"fake-image")
            figures_path = root / "source-images.json"
            figures_path.write_text(
                json.dumps(
                    {
                        "source_image_assets": [
                            {
                                "path": str(image_path),
                                "label": "pipeline",
                                "caption": "Pipeline",
                                "source": "tex-source",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            vault = root / "paper-vault"

            for _ in range(2):
                result = run_script(
                    "maintain_library",
                    "--vault",
                    str(vault),
                    "--metadata",
                    str(metadata_path),
                    "--note",
                    str(note_path),
                    "--figures",
                    str(figures_path),
                    "--insert-figures",
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            payload = json.loads(result.stdout)
            self.assertEqual(payload["figures"][0]["source"], "tex-source")
            note = (vault / "papers" / "notes" / "source-figure-paper.md").read_text(encoding="utf-8")
            self.assertEqual(note.count("<!-- figures: arxiv:2601.00003 begin -->"), 1)
            self.assertEqual(note.count("![Pipeline]"), 1)

    def test_extract_tex_source_indexes_images_and_graphics_refs(self) -> None:
        extract_tex = load_module("extract_tex_source")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "source"
            (source_dir / "figs").mkdir(parents=True)
            (source_dir / "main.tex").write_text(
                "\\includegraphics[width=0.9\\linewidth]{figs/pipeline}\n"
                "\\includegraphics{figs/result.png}\n",
                encoding="utf-8",
            )
            (source_dir / "figs" / "pipeline.pdf").write_bytes(b"%PDF-1.4 fake")
            (source_dir / "figs" / "result.png").write_bytes(b"fake-image")
            archive = root / "source.tar"
            with tarfile.open(archive, "w") as tf:
                for path in source_dir.rglob("*"):
                    tf.add(path, arcname=path.relative_to(source_dir))

            payload = extract_tex.unpack_archive(archive, root / "out", "2601.00004")

            self.assertEqual(payload["kind"], "tar")
            self.assertEqual({Path(path).name for path in payload["image_files"]}, {"pipeline.pdf", "result.png"})
            refs = {item["reference"]: item for item in payload["graphics_refs"]}
            self.assertIn("figs/pipeline", refs)
            self.assertIn("figs/result.png", refs)
            self.assertEqual(Path(refs["figs/pipeline"]["matches"][0]).name, "pipeline.pdf")
            self.assertEqual(Path(refs["figs/result.png"]["matches"][0]).name, "result.png")
            self.assertEqual(len(payload["source_image_assets"]), 2)
            self.assertTrue(all(item["source"] == "tex-source" for item in payload["source_image_assets"]))

    def test_extract_tex_source_pdf_image_conversion_fails_gracefully(self) -> None:
        extract_tex = load_module("extract_tex_source")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "figure.pdf"
            image.write_bytes(b"%PDF-1.4 fake")

            converted, diagnostics = extract_tex.convert_source_images([str(image)], root / "converted")

            self.assertEqual(converted[0]["original_path"], str(image))
            self.assertEqual(converted[0]["path"], str(image))
            self.assertFalse(converted[0]["converted"])
            self.assertTrue(diagnostics)

    def test_extract_figures_missing_pdf_returns_json_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script("extract_figures", str(Path(tmp) / "missing.pdf"), "--out-dir", tmp)
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertIn("diagnostics", payload)

    def test_extract_tex_bad_source_is_graceful_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script("extract_tex_source", "not-a-paper", "--out-dir", tmp)
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertFalse(payload["source_available"])

    def test_organize_library_rebuilds_navigation_and_health_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "paper-vault"
            metadata_dir = vault / "papers" / "metadata"
            notes_dir = vault / "papers" / "notes"
            metadata_dir.mkdir(parents=True)
            notes_dir.mkdir(parents=True)
            (vault / "papers" / "pdfs").mkdir(parents=True)
            (vault / "papers" / "assets").mkdir(parents=True)

            first = {
                "title": "Policy Learning Paper",
                "year": "2026",
                "venue": "CoRL",
                "topic": "robotics",
                "method": "policy learning",
                "status": "reading",
                "project": "recap-vla",
                "priority": "high",
                "slug": "policy-learning-paper",
                "dedupe_key": "arxiv:2601.00006",
            }
            (metadata_dir / "policy-learning-paper.json").write_text(json.dumps(first), encoding="utf-8")
            (notes_dir / "policy-learning-paper.md").write_text("# Policy Learning Paper\n", encoding="utf-8")
            (vault / "papers" / "pdfs" / "policy-learning-paper.pdf").write_bytes(b"%PDF")
            (vault / "papers" / "assets" / "policy-learning-paper").mkdir()

            (notes_dir / "note-only.md").write_text(
                "---\n"
                "title: Note Only Paper\n"
                "year: 2025\n"
                "topic: manipulation\n"
                "method: dataset\n"
                "status: unread\n"
                "---\n"
                "# Note Only Paper\n",
                encoding="utf-8",
            )

            for _ in range(2):
                result = run_script("organize_library", "--vault", str(vault))
                self.assertEqual(result.returncode, 0, result.stderr)

            payload = json.loads(result.stdout)
            self.assertEqual(payload["entry_count"], 2)
            self.assertEqual(payload["note_only_count"], 1)
            by_topic = vault / "papers" / "navigation" / "By Topic.md"
            by_method = vault / "papers" / "navigation" / "By Method.md"
            health = vault / "papers" / "navigation" / "Library Health.md"
            self.assertEqual(by_topic.read_text(encoding="utf-8").count("<!-- dedupe: arxiv:2601.00006 -->"), 1)
            self.assertEqual(by_method.read_text(encoding="utf-8").count("Note Only Paper"), 1)
            self.assertIn("note-only", health.read_text(encoding="utf-8"))
            self.assertIn("metadata", health.read_text(encoding="utf-8"))

    def test_organize_library_reports_duplicate_dedupe_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "paper-vault"
            metadata_dir = vault / "papers" / "metadata"
            metadata_dir.mkdir(parents=True)
            for slug in ["a", "b"]:
                payload = {
                    "title": f"Paper {slug}",
                    "slug": slug,
                    "dedupe_key": "doi:10.0000/example",
                }
                (metadata_dir / f"{slug}.json").write_text(json.dumps(payload), encoding="utf-8")

            result = run_script("organize_library", "--vault", str(vault))

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(len(payload["duplicates"]), 1)
            health = vault / "papers" / "navigation" / "Library Health.md"
            self.assertIn("doi:10.0000/example", health.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
