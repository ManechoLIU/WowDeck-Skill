from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skill" / "wowdeck" / "scripts"
INIT_DECK = SCRIPTS / "init_deck.py"
VALIDATE_DECK = SCRIPTS / "validate_deck.py"
PREPARE_MEDIA = SCRIPTS / "prepare_media.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_cli(
    script: Path,
    *arguments: object,
    timeout: int = 30,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *(str(argument) for argument in arguments)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env=env,
    )


def output_of(completed: subprocess.CompletedProcess[str]) -> str:
    return f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"


def deck_config_payload(index_path: Path) -> str:
    text = index_path.read_text(encoding="utf-8")
    match = re.search(
        r'<script\b(?=[^>]*\bid=["\']deck-config["\'])[^>]*>(.*?)</script\s*>',
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if not match:
        raise AssertionError("generated index.html has no #deck-config block")
    return match.group(1).strip()


def deck_config(index_path: Path) -> dict:
    return json.loads(deck_config_payload(index_path))


def replace_deck_config(index_path: Path, config: dict) -> None:
    text = index_path.read_text(encoding="utf-8")
    old_payload = deck_config_payload(index_path)
    new_payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    index_path.write_text(text.replace(old_payload, new_payload, 1), encoding="utf-8")


class WowDeckCliTests(unittest.TestCase):
    def init_deck(self, deck_dir: Path, *features: str) -> Path:
        arguments: list[object] = [deck_dir, "--title", "Unit Test Deck"]
        if features:
            arguments.extend(["--features", *features])
        completed = run_cli(INIT_DECK, *arguments)
        self.assertEqual(completed.returncode, 0, output_of(completed))
        return deck_dir / "index.html"

    def complete_starter(self, index_path: Path, *, remove_inline_notes: bool = True) -> None:
        text = index_path.read_text(encoding="utf-8").replace(
            "WOWDECK_PLACEHOLDER", "Unit test content"
        )
        if remove_inline_notes:
            text = re.sub(
                r"<aside\b(?=[^>]*\bdata-notes\b)[^>]*>.*?</aside\s*>",
                "",
                text,
                flags=re.DOTALL | re.IGNORECASE,
            )
        index_path.write_text(text, encoding="utf-8")

    def add_notes(self, index_path: Path, notes: list[str]) -> None:
        text = index_path.read_text(encoding="utf-8")
        payload = json.dumps(notes, ensure_ascii=False)
        block = f'<script id="deck-notes" type="application/json">{payload}</script>'
        self.assertIn("</body>", text)
        index_path.write_text(text.replace("</body>", f"{block}\n</body>", 1), encoding="utf-8")

    def set_inline_note(
        self,
        index_path: Path,
        text_value: str,
        *,
        duration: str = "30",
    ) -> None:
        text = index_path.read_text(encoding="utf-8")
        pattern = re.compile(
            r'(<aside\b(?=[^>]*\bdata-notes\b)[^>]*\bdata-duration=["\'])[^"\']*'
            r'(["\'][^>]*>).*?(</aside\s*>)',
            re.DOTALL | re.IGNORECASE,
        )
        self.assertRegex(text, pattern)
        replacement = rf"\g<1>{duration}\g<2>{text_value}\g<3>"
        index_path.write_text(pattern.sub(replacement, text, count=1), encoding="utf-8")

    def add_hidden_slide(self, index_path: Path, *, with_note: bool = False) -> None:
        text = index_path.read_text(encoding="utf-8")
        note = (
            '<aside data-notes data-duration="20" hidden>Second slide note.</aside>'
            if with_note else ""
        )
        slide = (
            '<section class="slide" id="slide-2" data-title="Second slide" '
            'aria-hidden="true" inert>'
            '<h2>Second slide</h2>'
            f'{note}'
            '</section>'
        )
        self.assertIn("</main>", text)
        index_path.write_text(text.replace("</main>", f"{slide}\n</main>", 1), encoding="utf-8")

    def add_media_element(self, index_path: Path, element: str) -> None:
        text = index_path.read_text(encoding="utf-8")
        marker = '<footer class="slide-footer">'
        self.assertIn(marker, text)
        index_path.write_text(text.replace(marker, f"{element}\n          {marker}", 1), encoding="utf-8")

    def validate_json(
        self,
        index_path: Path,
        *,
        receipt: Path | None = None,
        check_receipt: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict]:
        arguments: list[object] = [index_path, "--json"]
        if receipt is not None:
            arguments.extend(["--receipt", receipt])
        if check_receipt is not None:
            arguments.extend(["--check-receipt", check_receipt])
        completed = run_cli(VALIDATE_DECK, *arguments, env=env)
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            self.fail(f"validator did not emit JSON: {error}\n{output_of(completed)}")
        return completed, result

    def assert_validation_passes(self, index_path: Path) -> dict:
        completed, result = self.validate_json(index_path)
        self.assertEqual(completed.returncode, 0, output_of(completed))
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["errors"], [], result)
        return result

    def assert_validation_fails(self, index_path: Path, expected: str) -> dict:
        completed, result = self.validate_json(index_path)
        self.assertNotEqual(completed.returncode, 0, output_of(completed))
        self.assertFalse(result["ok"], result)
        self.assertIn(expected, "\n".join(result["errors"]), result)
        return result

    def write_manifest(self, deck_dir: Path, items: list[dict]) -> Path:
        path = deck_dir / "media" / "manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "items": items,
                    "truth_states": ["VERIFIED", "PROPOSED", "SIMULATED", "UNKNOWN"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def write_dependencies(
        self,
        deck_dir: Path,
        files: list[tuple[str, str]],
        *,
        variant: str = "unit-test",
        source_revision: str = "source-r1",
        builder_revision: str = "builder-r1",
    ) -> Path:
        records = []
        for relative, role in files:
            candidate = deck_dir / relative
            self.assertTrue(candidate.is_file(), candidate)
            records.append(
                {"path": relative, "role": role, "sha256": sha256(candidate)}
            )
        path = deck_dir / "deck-dependencies.json"
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "variant": variant,
                    "source_revision": source_revision,
                    "builder_revision": builder_revision,
                    "files": records,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def create_audio_fixture(self, path: Path) -> None:
        completed = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=0.2",
                "-c:a", "aac", "-b:a", "64k", str(path),
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, output_of(completed))

    def test_init_escapes_untrusted_text_in_deck_config_and_html(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            malicious_title = '</script><img src=x onerror="window.pwned=1">&\u2028\u2029'
            malicious_subtitle = '</p><script>window.pwned=2</script><p>'

            completed = run_cli(
                INIT_DECK,
                deck_dir,
                "--title", malicious_title,
                "--subtitle", malicious_subtitle,
                "--features", "none",
            )

            self.assertEqual(completed.returncode, 0, output_of(completed))
            payload = deck_config_payload(deck_dir / "index.html")
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError as error:
                self.fail(f"untrusted title broke #deck-config JSON: {error}")
            self.assertEqual(parsed["title"], malicious_title)
            for unsafe in ("<", ">", "&", "\u2028", "\u2029"):
                self.assertNotIn(unsafe, payload)
            self.assertIn(r"\u003c/script\u003e", payload)
            text = (deck_dir / "index.html").read_text(encoding="utf-8")
            self.assertNotRegex(text.lower(), r"<img\b")
            self.assertNotIn("<script>window.pwned", text.lower())
            self.assertEqual(len(re.findall(r"<script\b", text, re.IGNORECASE)), 2)

    def test_quick_init_refuses_to_overwrite_existing_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            index_path = self.init_deck(deck_dir)
            index_path.write_text("owned existing content\n", encoding="utf-8")

            completed = run_cli(INIT_DECK, deck_dir, "--title", "Replacement")

            self.assertNotEqual(completed.returncode, 0, output_of(completed))
            self.assertIn("refusing to overwrite", completed.stderr + completed.stdout)
            self.assertEqual(index_path.read_text(encoding="utf-8"), "owned existing content\n")

    def test_init_declares_and_validates_one_deck_wide_background_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            completed = run_cli(
                INIT_DECK,
                deck_dir,
                "--title", "Dark canvas deck",
                "--background-mode", "dark",
                "--features", "none",
            )
            self.assertEqual(completed.returncode, 0, output_of(completed))
            index_path = deck_dir / "index.html"
            self.complete_starter(index_path)

            result = self.assert_validation_passes(index_path)

            self.assertEqual(deck_config(index_path)["background_mode"], "dark")
            self.assertEqual(result["facts"]["background_mode"], "dark")

    def test_validator_rejects_root_or_slide_background_mode_conflicts(self) -> None:
        cases = (
            (
                "root",
                lambda text: text.replace(
                    'data-background-mode="light"',
                    'data-background-mode="dark"',
                    1,
                ),
                "must match #deck-config background_mode",
            ),
            (
                "slide-attribute",
                lambda text: text.replace(
                    'class="slide" id="slide-2"',
                    'class="slide" data-background-mode="dark" id="slide-2"',
                    1,
                ),
                "declares opposite background mode",
            ),
            (
                "slide-invalid-attribute",
                lambda text: text.replace(
                    'class="slide" id="slide-2"',
                    'class="slide" data-background-mode="sepia" id="slide-2"',
                    1,
                ),
                "data-background-mode must be 'light' or 'dark'",
            ),
            (
                "slide-empty-attribute",
                lambda text: text.replace(
                    'class="slide" id="slide-2"',
                    'class="slide" data-background-mode="  " id="slide-2"',
                    1,
                ),
                "data-background-mode must be 'light' or 'dark'",
            ),
        )
        for label, mutate, expected in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                index_path = self.init_deck(Path(temporary) / "deck")
                self.complete_starter(index_path)
                self.add_hidden_slide(index_path)
                original = index_path.read_text(encoding="utf-8")
                changed = mutate(original)
                self.assertNotEqual(changed, original)
                index_path.write_text(changed, encoding="utf-8")
                self.assert_validation_fails(index_path, expected)

    def test_validator_enforces_v2_background_mode_and_handles_invalid_json_types(self) -> None:
        cases = (
            ("missing", None, "background_mode is required in version 2"),
            ("array", [], "background_mode must be 'light' or 'dark'"),
            ("object", {}, "background_mode must be 'light' or 'dark'"),
            ("invalid-string", "sepia", "background_mode must be 'light' or 'dark'"),
        )
        for label, value, expected in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                index_path = self.init_deck(Path(temporary) / "deck")
                self.complete_starter(index_path)
                config = deck_config(index_path)
                if value is None:
                    config.pop("background_mode")
                else:
                    config["background_mode"] = value
                replace_deck_config(index_path, config)
                self.assert_validation_fails(index_path, expected)

    def test_validator_rejects_invalid_config_versions_without_crashing(self) -> None:
        cases = (None, [], {}, True, "2", 3)
        for value in cases:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temporary:
                index_path = self.init_deck(Path(temporary) / "deck")
                self.complete_starter(index_path)
                config = deck_config(index_path)
                config["version"] = value
                replace_deck_config(index_path, config)
                self.assert_validation_fails(
                    index_path,
                    "#deck-config version must be 1 or 2",
                )

    def test_v1_background_mode_compatibility_and_explicit_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            index_path = self.init_deck(Path(temporary) / "deck")
            self.complete_starter(index_path)
            config = deck_config(index_path)
            config["version"] = 1
            replace_deck_config(index_path, config)
            self.assert_validation_passes(index_path)

            config.pop("background_mode")
            replace_deck_config(index_path, config)

            result = self.assert_validation_passes(index_path)
            self.assertIn("compatibility input", "\n".join(result["warnings"]))

            text = index_path.read_text(encoding="utf-8")
            text = text.replace(
                'class="slide is-active"',
                'class="slide is-active" data-background-mode="dark"',
                1,
            )
            index_path.write_text(text, encoding="utf-8")
            self.assert_validation_fails(
                index_path,
                "declares opposite background mode",
            )

            text = index_path.read_text(encoding="utf-8").replace(
                ' data-background-mode="dark"',
                "",
                1,
            )
            index_path.write_text(text, encoding="utf-8")
            config["background_mode"] = "dark"
            replace_deck_config(index_path, config)
            self.assert_validation_fails(
                index_path,
                "must match #deck-config background_mode",
            )

    def test_local_surface_classes_do_not_count_as_slide_background_switches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            index_path = self.init_deck(Path(temporary) / "deck")
            self.complete_starter(index_path)
            text = index_path.read_text(encoding="utf-8")
            marker = '<footer class="slide-footer">'
            local_surfaces = (
                '<article class="card bg-dark">Local dark card</article>'
                '<figure class="media theme-dark">Local media surface</figure>'
                '<dialog class="background-dark">Local dialog surface</dialog>'
            )
            self.assertIn(marker, text)
            index_path.write_text(
                text.replace(marker, f"{local_surfaces}\n          {marker}", 1),
                encoding="utf-8",
            )

            self.assert_validation_passes(index_path)

    def test_forward_browser_evidence_matches_the_current_artifact(self) -> None:
        fixture = REPO_ROOT / "tests" / "forward" / "non-pitch-teaching"
        receipt = json.loads(
            (fixture / "validation-receipt.json").read_text(encoding="utf-8")
        )
        browser_check = json.loads(
            (fixture / "browser-check.json").read_text(encoding="utf-8")
        )
        contact_sheet = fixture / browser_check["contact_sheet"]["path"]
        index_path = fixture / "index.html"
        receipt_path = fixture / "validation-receipt.json"

        self.assertEqual(browser_check["status"], "PASS")
        self.assertEqual(receipt["index_sha256"], sha256(index_path))
        completed, validation = self.validate_json(
            index_path,
            check_receipt=receipt_path,
        )
        self.assertEqual(completed.returncode, 0, output_of(completed))
        self.assertTrue(validation["ok"], validation)
        self.assertEqual(validation["facts"]["receipt_status"], "current")
        self.assertEqual(
            browser_check["artifact"]["index_sha256"],
            receipt["index_sha256"],
        )
        self.assertEqual(
            browser_check["artifact"]["artifact_sha256"],
            receipt["artifact_sha256"],
        )
        for field in (
            "source_revision",
            "builder_revision",
            "source_sha256",
            "variant",
            "background_mode",
        ):
            self.assertEqual(browser_check["artifact"][field], receipt[field])
        self.assertTrue(browser_check["assertions"]["artifact_matches_receipt"])
        self.assertTrue(browser_check["assertions"]["background_mode_consistent"])
        self.assertTrue(browser_check["assertions"]["contact_sheet_generated"])
        self.assertTrue(all(browser_check["assertions"].values()))
        self.assertEqual(browser_check["console_errors"], [])
        self.assertEqual(
            [
                (check["profile"], len(check["pages"]), check["pass"])
                for check in browser_check["checks"]
            ],
            [
                ("standard", 7, True),
                ("small", 7, True),
                ("reduced-motion", 7, True),
            ],
        )
        self.assertTrue(
            all(
                page["pass"]
                for check in browser_check["checks"]
                for page in check["pages"]
            )
        )
        self.assertEqual(browser_check["contact_sheet"]["slide_count"], 7)
        runner = fixture / browser_check["runner"]["path"]
        self.assertTrue(runner.is_file())
        self.assertEqual(browser_check["runner"]["sha256"], sha256(runner))
        self.assertTrue(contact_sheet.is_file())
        self.assertEqual(browser_check["contact_sheet"]["sha256"], sha256(contact_sheet))
        png = contact_sheet.read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", png[16:24])
        self.assertEqual(width, 1600)
        self.assertGreater(height, 900)

    def test_core_only_init_resolves_template_tokens_but_keeps_completion_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            index_path = self.init_deck(deck_dir, "none")
            text = index_path.read_text(encoding="utf-8")

            self.assertEqual(deck_config(index_path)["features"], [])
            self.assertNotRegex(text, r"\{\{[A-Z0-9_]+\}\}")
            self.assertIn("WOWDECK_PLACEHOLDER", text)
            self.assertFalse((deck_dir / "media" / "manifest.json").exists())

    def test_placeholder_blocks_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            index_path = self.init_deck(Path(temporary) / "deck", "none")
            self.assert_validation_fails(index_path, "starter placeholders remain")

    def test_core_only_deck_without_notes_or_media_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            index_path = self.init_deck(Path(temporary) / "deck", "none")
            self.complete_starter(index_path)

            result = self.assert_validation_passes(index_path)

            self.assertEqual(result["facts"]["features"], [])
            self.assertIsNone(result["facts"]["notes"])
            self.assertEqual(result["facts"]["media"], [])
            self.assertEqual(result["facts"]["status"], "PASS_RENDERED_ARTIFACT")
            self.assertEqual(result["facts"]["validation_level"], "rendered_artifact")

    def test_core_only_deck_rejects_a_second_hidden_slide(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            index_path = self.init_deck(Path(temporary) / "deck", "none")
            self.complete_starter(index_path)
            self.add_hidden_slide(index_path)

            self.assert_validation_fails(
                index_path,
                "core-only deck cannot contain multiple hidden slides",
            )

    def test_presenter_requires_one_nonempty_note_per_slide(self) -> None:
        cases = (
            ("missing", "remove", "requires one inline data-notes element per slide"),
            ("legacy-only", "legacy", "requires one inline data-notes element per slide"),
            ("empty", "empty", "requires non-empty inline speaker notes"),
        )
        for label, mode, expected in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                index_path = self.init_deck(Path(temporary) / "deck", "presenter")
                self.complete_starter(index_path, remove_inline_notes=mode != "empty")
                if mode == "legacy":
                    self.add_notes(index_path, ["Legacy-only note."])
                self.assert_validation_fails(index_path, expected)

        with tempfile.TemporaryDirectory() as temporary:
            index_path = self.init_deck(Path(temporary) / "deck", "presenter")
            self.complete_starter(index_path, remove_inline_notes=False)
            self.set_inline_note(index_path, "Talk through this slide.", duration="45")

            result = self.assert_validation_passes(index_path)

            self.assertEqual(result["facts"]["notes"], 1)

    def test_legacy_deck_uses_explicit_artifact_only_status(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            deck_dir.mkdir()
            index_path = deck_dir / "index.html"
            index_path.write_text(
                '<!doctype html><html lang="en"><head><style>@media print {}</style></head>'
                '<body><main id="stage"><section class="slide" id="slide-1" '
                'data-title="Legacy"><h1>Legacy</h1></section></main></body></html>',
                encoding="utf-8",
            )
            receipt_path = deck_dir / "validation-receipt.json"

            completed, result = self.validate_json(index_path, receipt=receipt_path)

            self.assertEqual(completed.returncode, 0, output_of(completed))
            self.assertEqual(result["facts"].get("status"), "PASS_LEGACY_ARTIFACT_ONLY")
            self.assertEqual(
                result["facts"].get("validation_level"), "legacy_artifact_only"
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "PASS_LEGACY_ARTIFACT_ONLY")
            self.assertEqual(receipt["validation_level"], "legacy_artifact_only")

    def test_video_requires_poster_and_manifest(self) -> None:
        with self.subTest("missing poster"), tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            index_path = self.init_deck(deck_dir, "media")
            self.complete_starter(index_path)
            (deck_dir / "media" / "clip.mp4").write_bytes(b"not-empty")
            self.add_media_element(index_path, '<video src="media/clip.mp4" controls></video>')
            self.write_manifest(
                deck_dir,
                [
                    {
                        "key": "clip",
                        "kind": "video",
                        "src": "media/clip.mp4",
                        "truth": "SIMULATED",
                        "source": "Synthetic unittest fixture",
                    }
                ],
            )
            self.assert_validation_fails(index_path, "has no poster")

        with self.subTest("missing manifest"), tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            index_path = self.init_deck(deck_dir, "media")
            self.complete_starter(index_path)
            (deck_dir / "media" / "manifest.json").unlink()
            (deck_dir / "media" / "clip.mp4").write_bytes(b"not-empty")
            (deck_dir / "media" / "clip.jpg").write_bytes(b"not-empty")
            self.add_media_element(
                index_path,
                '<video src="media/clip.mp4" poster="media/clip.jpg" controls></video>',
            )
            self.assert_validation_fails(index_path, "media/manifest.json is required")

    @unittest.skipUnless(
        shutil.which("ffmpeg") and shutil.which("ffprobe"),
        "ffmpeg and ffprobe are required for valid media coverage",
    )
    def test_audio_needs_no_poster_and_receipt_detects_index_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            index_path = self.init_deck(deck_dir, "media")
            self.complete_starter(index_path)
            audio_path = deck_dir / "media" / "tone.m4a"
            self.create_audio_fixture(audio_path)
            self.add_media_element(index_path, '<audio src="media/tone.m4a" controls></audio>')
            manifest_path = self.write_manifest(
                deck_dir,
                [
                    {
                        "key": "tone",
                        "kind": "audio",
                        "src": "media/tone.m4a",
                        "truth": "SIMULATED",
                        "source": "Synthetic unittest fixture",
                        "duration_seconds": 0.2,
                        "audio_codec": "aac",
                        "preparation": "transcoded",
                    }
                ],
            )
            dependency_path = self.write_dependencies(
                deck_dir,
                [
                    ("media/manifest.json", "runtime"),
                    ("media/tone.m4a", "asset"),
                ],
            )
            receipt_path = deck_dir / "validation-receipt.json"

            completed, result = self.validate_json(index_path, receipt=receipt_path)

            self.assertEqual(completed.returncode, 0, output_of(completed))
            self.assertTrue(result["ok"], result)
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["index_sha256"], sha256(index_path))
            self.assertEqual(receipt["slide_count"], 1)
            self.assertEqual(receipt["manifest_sha256"], sha256(manifest_path))
            self.assertEqual(receipt["features"], ["media"])
            self.assertEqual(receipt["status"], "PASS_SOURCE_BOUND")
            self.assertEqual(
                receipt["dependency_manifest_sha256"], sha256(dependency_path)
            )

            current, current_result = self.validate_json(index_path, check_receipt=receipt_path)
            self.assertEqual(current.returncode, 0, output_of(current))
            self.assertEqual(current_result["facts"]["receipt_status"], "current")

            index_path.write_text(
                index_path.read_text(encoding="utf-8").replace(
                    "Unit test content", "Changed unit test content", 1
                ),
                encoding="utf-8",
            )
            stale, stale_result = self.validate_json(index_path, check_receipt=receipt_path)
            self.assertNotEqual(stale.returncode, 0, output_of(stale))
            self.assertFalse(stale_result["ok"], stale_result)
            self.assertEqual(stale_result["facts"]["receipt_status"], "stale")
            self.assertIn("validation receipt is stale", "\n".join(stale_result["errors"]))

    @unittest.skipUnless(shutil.which("ffprobe"), "ffprobe is required for corrupt media coverage")
    def test_corrupt_manifest_media_is_a_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            index_path = self.init_deck(deck_dir, "media")
            self.complete_starter(index_path)
            audio_path = deck_dir / "media" / "broken.m4a"
            audio_path.write_bytes(b"not an audio container")
            self.add_media_element(index_path, '<audio src="media/broken.m4a" controls></audio>')
            self.write_manifest(
                deck_dir,
                [{
                    "key": "broken",
                    "kind": "audio",
                    "src": "media/broken.m4a",
                    "truth": "SIMULATED",
                    "source": "Synthetic corrupt unittest fixture",
                    "duration_seconds": 0.2,
                    "audio_codec": "aac",
                    "preparation": "intentionally corrupt",
                }],
            )
            self.write_dependencies(
                deck_dir,
                [
                    ("media/manifest.json", "runtime"),
                    ("media/broken.m4a", "asset"),
                ],
            )

            self.assert_validation_fails(index_path, "ffprobe failed for broken.m4a")

    def test_v1_media_cannot_pass_or_write_receipt_without_ffprobe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            index_path = self.init_deck(deck_dir, "media")
            self.complete_starter(index_path)
            audio_path = deck_dir / "media" / "tone.m4a"
            audio_path.write_bytes(b"probe is deliberately unavailable")
            self.add_media_element(index_path, '<audio src="media/tone.m4a" controls></audio>')
            self.write_manifest(
                deck_dir,
                [{
                    "key": "tone",
                    "kind": "audio",
                    "src": "media/tone.m4a",
                    "truth": "SIMULATED",
                    "source": "Synthetic unittest fixture",
                    "duration_seconds": 0.2,
                    "audio_codec": "aac",
                    "preparation": "test fixture",
                }],
            )
            self.write_dependencies(
                deck_dir,
                [
                    ("media/manifest.json", "runtime"),
                    ("media/tone.m4a", "asset"),
                ],
            )
            receipt_path = deck_dir / "validation-receipt.json"
            empty_path = deck_dir / "empty-path"
            empty_path.mkdir()
            environment = os.environ.copy()
            environment["PATH"] = str(empty_path)

            completed, result = self.validate_json(
                index_path,
                receipt=receipt_path,
                env=environment,
            )

            self.assertNotEqual(completed.returncode, 0, output_of(completed))
            self.assertIn("ffprobe unavailable", "\n".join(result["errors"]))
            self.assertFalse(receipt_path.exists())

    def test_dependency_manifest_binds_source_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            index_path = self.init_deck(deck_dir, "none")
            self.complete_starter(index_path)
            (deck_dir / "content.json").write_text('{"title":"Bound"}\n', encoding="utf-8")
            (deck_dir / "build.py").write_text("print('build')\n", encoding="utf-8")
            dependency_path = self.write_dependencies(
                deck_dir,
                [("content.json", "authoring"), ("build.py", "runtime")],
                variant="bound-fixture",
            )
            receipt_path = deck_dir / "validation-receipt.json"

            completed, result = self.validate_json(index_path, receipt=receipt_path)

            self.assertEqual(completed.returncode, 0, output_of(completed))
            facts = result["facts"]
            self.assertEqual(facts.get("status"), "PASS_SOURCE_BOUND")
            self.assertEqual(facts.get("validation_level"), "source_bound")
            self.assertEqual(facts.get("variant"), "bound-fixture")
            self.assertEqual(facts.get("dependency_manifest_sha256"), sha256(dependency_path))
            self.assertRegex(facts.get("source_sha256", ""), r"^[0-9a-f]{64}$")
            self.assertEqual(
                facts["artifact_identity"]["source_sha256"], facts["source_sha256"]
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "PASS_SOURCE_BOUND")
            self.assertEqual(receipt["source_sha256"], facts["source_sha256"])
            self.assertEqual(receipt["variant"], "bound-fixture")
            self.assertEqual(len(receipt["dependency_files"]), 2)

    def test_dependency_change_invalidates_manifest_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            index_path = self.init_deck(deck_dir, "none")
            self.complete_starter(index_path)
            source_path = deck_dir / "content.json"
            source_path.write_text('{"revision":1}\n', encoding="utf-8")
            self.write_dependencies(deck_dir, [("content.json", "authoring")])
            receipt_path = deck_dir / "validation-receipt.json"
            first, first_result = self.validate_json(index_path, receipt=receipt_path)
            self.assertEqual(first.returncode, 0, output_of(first))
            self.assertEqual(first_result["facts"].get("status"), "PASS_SOURCE_BOUND")

            source_path.write_text('{"revision":2}\n', encoding="utf-8")
            stale, result = self.validate_json(index_path, check_receipt=receipt_path)

            self.assertNotEqual(stale.returncode, 0, output_of(stale))
            joined = "\n".join(result["errors"])
            self.assertIn("dependency hash mismatch: content.json", joined)
            self.assertIn("validation receipt is stale", joined)
            self.assertEqual(result["facts"]["receipt_status"], "stale")

    def test_fetch_dependency_must_be_declared(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            index_path = self.init_deck(deck_dir, "none")
            self.complete_starter(index_path)
            (deck_dir / "content.txt").write_text("canonical source\n", encoding="utf-8")
            (deck_dir / "data.json").write_text('{"value":1}\n', encoding="utf-8")
            self.write_dependencies(deck_dir, [("content.txt", "authoring")])
            text = index_path.read_text(encoding="utf-8")
            index_path.write_text(
                text.replace("</body>", '<script>fetch("data.json")</script></body>', 1),
                encoding="utf-8",
            )

            self.assert_validation_fails(
                index_path,
                "undeclared local runtime dependencies: data.json",
            )

    def test_external_scripts_recursively_declare_import_worker_and_fetch_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            index_path = self.init_deck(deck_dir, "none")
            self.complete_starter(index_path)
            (deck_dir / "scripts").mkdir()
            (deck_dir / "scripts" / "app.js").write_text(
                'import("./module.mjs"); new Worker("./worker.js");\n',
                encoding="utf-8",
            )
            (deck_dir / "scripts" / "module.mjs").write_text(
                'fetch("../data.json");\n',
                encoding="utf-8",
            )
            (deck_dir / "scripts" / "worker.js").write_text(
                'self.addEventListener("message", () => {});\n',
                encoding="utf-8",
            )
            (deck_dir / "data.json").write_text('{"value":1}\n', encoding="utf-8")
            text = index_path.read_text(encoding="utf-8")
            index_path.write_text(
                text.replace(
                    "</body>",
                    '<script type="module" src="scripts/app.js"></script></body>',
                    1,
                ),
                encoding="utf-8",
            )
            script_files = [
                ("scripts/app.js", "runtime"),
                ("scripts/module.mjs", "runtime"),
                ("scripts/worker.js", "runtime"),
            ]
            self.write_dependencies(deck_dir, script_files)

            self.assert_validation_fails(
                index_path,
                "undeclared local runtime dependencies: data.json",
            )

            self.write_dependencies(deck_dir, [*script_files, ("data.json", "runtime")])
            result = self.assert_validation_passes(index_path)
            self.assertEqual(
                result["facts"]["asset_sha256"]["data.json"],
                sha256(deck_dir / "data.json"),
            )

    def test_recursive_css_dependencies_are_hashed_and_must_be_declared(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            deck_dir = Path(temporary) / "deck"
            index_path = self.init_deck(deck_dir, "none")
            self.complete_starter(index_path)
            (deck_dir / "styles").mkdir()
            (deck_dir / "images").mkdir()
            (deck_dir / "styles" / "main.css").write_text(
                '@import "theme.css"; .hero { background: url("../images/bg.png"); }\n',
                encoding="utf-8",
            )
            (deck_dir / "styles" / "theme.css").write_text(
                '.icon { mask-image: url("../images/icon.svg"); }\n',
                encoding="utf-8",
            )
            (deck_dir / "images" / "bg.png").write_bytes(b"background fixture")
            (deck_dir / "images" / "icon.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>\n',
                encoding="utf-8",
            )
            text = index_path.read_text(encoding="utf-8")
            index_path.write_text(
                text.replace(
                    "</head>",
                    '<link rel="stylesheet" href="styles/main.css">\n</head>',
                    1,
                ),
                encoding="utf-8",
            )
            all_files = [
                ("styles/main.css", "runtime"),
                ("styles/theme.css", "runtime"),
                ("images/bg.png", "asset"),
                ("images/icon.svg", "asset"),
            ]
            self.write_dependencies(deck_dir, all_files)

            result = self.assert_validation_passes(index_path)

            self.assertIn("dependency_files", result["facts"])
            dependency_files = {
                item["path"]: item["sha256"]
                for item in result["facts"]["dependency_files"]
            }
            self.assertEqual(dependency_files["images/icon.svg"], sha256(deck_dir / "images/icon.svg"))
            self.assertEqual(
                result["facts"]["asset_sha256"]["images/icon.svg"],
                sha256(deck_dir / "images/icon.svg"),
            )

            self.write_dependencies(deck_dir, all_files[:-1])
            self.assert_validation_fails(
                index_path,
                "undeclared local runtime dependencies: images/icon.svg",
            )

    @unittest.skipUnless(
        shutil.which("ffmpeg") and shutil.which("ffprobe"),
        "ffmpeg and ffprobe are required for media preparation coverage",
    )
    def test_prepare_media_emits_audio_without_poster_and_video_with_poster(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            media_dir = root / "deck" / "media"
            audio_input = root / "tone.wav"
            video_input = root / "clip.avi"

            audio_fixture = subprocess.run(
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=0.2",
                    "-c:a", "pcm_s16le", str(audio_input),
                ],
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(audio_fixture.returncode, 0, output_of(audio_fixture))
            video_fixture = subprocess.run(
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "color=c=blue:s=32x32:d=0.4:r=5",
                    "-an", "-c:v", "mpeg4", "-q:v", "5", str(video_input),
                ],
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(video_fixture.returncode, 0, output_of(video_fixture))

            audio = run_cli(
                PREPARE_MEDIA,
                audio_input,
                media_dir,
                "--kind", "auto",
                "--name", "tone",
                "--truth", "SIMULATED",
                "--source", "Synthetic unittest tone",
                timeout=60,
            )
            self.assertEqual(audio.returncode, 0, output_of(audio))
            self.assertTrue((media_dir / "tone.m4a").is_file())
            self.assertFalse((media_dir / "tone.jpg").exists())

            video = run_cli(
                PREPARE_MEDIA,
                video_input,
                media_dir,
                "--kind", "auto",
                "--name", "clip",
                "--truth", "SIMULATED",
                "--source", "Synthetic unittest video",
                timeout=60,
            )
            self.assertEqual(video.returncode, 0, output_of(video))
            self.assertTrue((media_dir / "clip.mp4").is_file())
            self.assertTrue((media_dir / "clip.jpg").is_file())

            manifest = json.loads((media_dir / "manifest.json").read_text(encoding="utf-8"))
            items = {item["key"]: item for item in manifest["items"]}
            self.assertEqual(items["tone"]["kind"], "audio")
            self.assertNotIn("poster", items["tone"])
            self.assertEqual(items["clip"]["kind"], "video")
            self.assertEqual(items["clip"]["poster"], "media/clip.jpg")


if __name__ == "__main__":
    unittest.main()
