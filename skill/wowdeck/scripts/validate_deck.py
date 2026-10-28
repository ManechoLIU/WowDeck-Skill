#!/usr/bin/env python3
"""Validate a portable WowDeck using its declared runtime features."""

from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ALLOWED_FEATURES = ("navigation", "presenter", "media", "dialog")
ALLOWED_ASPECTS = {"16:9", "4:3"}
NON_FILE_SCHEMES = {"data", "blob", "mailto", "tel"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm"}
AUDIO_SUFFIXES = {".m4a", ".mp3", ".wav", ".aac", ".ogg"}
SHA256_HEX = re.compile(r"^[0-9a-fA-F]{64}$")
VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
PRIVATE_NAMES = {
    ".env", ".git", "transcript", "chat-export", "chat_export", "chat-log",
    "chat_log", "原文", "聊天记录", "讲解提示", "使用说明",
}
LEGACY_STARTER_MARKERS = {
    "WOWDECK_STARTER_PLACEHOLDER",
    "Replace with truth boundary",
    "Audience: define one",
    "Decision: define one",
    "Replace with the audience's actual work surface",
    "Replace this with a real quote",
    "Replace with real or labeled media",
    "Replace with requested decision",
}


class DeckParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.slides: list[dict] = []
        self.assets: list[tuple[str, str]] = []
        self.media: list[dict] = []
        self._slide: dict | None = None
        self._media_stack: list[dict] = []
        self._note_contexts: list[dict] = []
        self.notes: list[dict] = []
        self.has_stage = False
        self.dialogs = 0
        self.html_lang: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        classes = set(data.get("class", "").split())
        if tag == "html":
            self.html_lang = data.get("lang", "").strip()
        element_id = data.get("id")
        if element_id:
            self.ids.append(element_id)
        if element_id == "stage":
            self.has_stage = True
        if tag == "section" and "slide" in classes:
            self._slide = {
                "id": element_id,
                "title": data.get("data-title"),
                "active": bool({"active", "is-active"} & classes),
                "aria_hidden": data.get("aria-hidden"),
                "inert": "inert" in data,
                "headings": 0,
                "notes": [],
            }
            self.slides.append(self._slide)
        if self._slide is not None and tag in {"h1", "h2"}:
            self._slide["headings"] += 1

        if tag in {"video", "audio"}:
            item = {
                "kind": tag,
                "srcs": [data["src"]] if data.get("src") else [],
                "poster": data.get("poster", ""),
            }
            self.media.append(item)
            self._media_stack.append(item)
        elif tag == "source" and self._media_stack and data.get("src"):
            self._media_stack[-1]["srcs"].append(data["src"])
        if tag == "dialog" or data.get("role") == "dialog":
            self.dialogs += 1

        if tag not in VOID_ELEMENTS:
            for context in self._note_contexts:
                context["depth"] += 1
        if any(key == "data-notes" for key, _ in attrs):
            note = {
                "slide": self._slide,
                "duration": data.get("data-duration")
                if any(key == "data-duration" for key, _ in attrs) else None,
                "chunks": [],
            }
            self.notes.append(note)
            if self._slide is not None:
                self._slide["notes"].append(note)
            if tag not in VOID_ELEMENTS:
                self._note_contexts.append({"depth": 1, "note": note})

        for attr in ("src", "poster", "href"):
            value = data.get(attr)
            if value:
                self.assets.append((f"{tag}[{attr}]", value))
        srcset = data.get("srcset")
        if srcset:
            for candidate in srcset.split(","):
                url = candidate.strip().split()[0] if candidate.strip() else ""
                if url:
                    self.assets.append((f"{tag}[srcset]", url))
        if tag == "object" and data.get("data"):
            self.assets.append(("object[data]", data["data"]))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag not in VOID_ELEMENTS:
            remaining: list[dict] = []
            for context in self._note_contexts:
                context["depth"] -= 1
                if context["depth"] > 0:
                    remaining.append(context)
            self._note_contexts = remaining
        if tag == "section" and self._slide is not None:
            self._slide = None
        if tag in {"video", "audio"} and self._media_stack:
            self._media_stack.pop()

    def handle_data(self, data: str) -> None:
        for context in self._note_contexts:
            context["note"]["chunks"].append(data)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_file", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument(
        "--receipt", nargs="?", type=Path, const=Path("validation-receipt.json"),
        help="Write a receipt for a passing deck (default: validation-receipt.json)",
    )
    parser.add_argument(
        "--check-receipt", type=Path,
        help="Fail if a previous receipt does not match the current artifact",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_path(raw: str, root: Path) -> Path | None:
    parts = urlsplit(raw)
    if parts.scheme.lower() in NON_FILE_SCHEMES or raw.startswith("#"):
        return None
    if parts.scheme or raw.startswith("//"):
        return None
    return (root / unquote(parts.path)).resolve()


def normalized_asset_ref(raw: str) -> str:
    path = unquote(urlsplit(raw).path).replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path


def contains_private_path(value: str) -> bool:
    lowered = unquote(value).lower()
    return bool(
        re.search(r"file://|/(?:users|home)/|(?:^|[\s\"'(=])[a-z]:[\\/]", lowered)
        or any(token in lowered for token in PRIVATE_NAMES)
    )


def display_ref(value: str, limit: int = 160) -> str:
    return value if len(value) <= limit else value[:limit] + "…"


def extract_dynamic_refs(text: str) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    patterns = (
        ("fetch()", r"\bfetch\s*\(\s*(['\"`])(.*?)\1"),
        ("Worker()", r"\b(?:new\s+)?(?:SharedWorker|Worker)\s*\(\s*(['\"`])(.*?)\1"),
        ("import()", r"\bimport\s*\(\s*(['\"`])(.*?)\1"),
        (
            "import",
            r"\b(?:import|export)\s+(?:[^;\n]*?\s+from\s+)?(['\"`])(.*?)\1",
        ),
        ("URL()", r"\bnew\s+URL\s*\(\s*(['\"`])(.*?)\1"),
    )
    for label, pattern in patterns:
        refs.extend(
            (label, match.group(2).strip())
            for match in re.finditer(pattern, text, re.DOTALL)
            if match.group(2).strip()
        )
    return refs


def extract_css_refs(text: str) -> list[tuple[str, str]]:
    without_comments = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    refs: dict[str, str] = {}
    import_pattern = re.compile(
        r"@import\s+(?:url\(\s*)?(?:(['\"])(.*?)\1|([^\s\"');]+))",
        re.IGNORECASE,
    )
    for match in import_pattern.finditer(without_comments):
        raw = (match.group(2) or match.group(3) or "").strip()
        if raw:
            refs[raw] = "css[@import]"
    url_pattern = re.compile(
        r"url\(\s*(?:(['\"])(.*?)\1|([^)]*?))\s*\)",
        re.IGNORECASE | re.DOTALL,
    )
    for match in url_pattern.finditer(without_comments):
        raw = (match.group(2) or match.group(3) or "").strip()
        if raw and raw not in refs:
            refs[raw] = "css[url]"
    return [(label, raw) for raw, label in refs.items()]


def validate_dependency_manifest(
    root: Path,
    config: dict,
    errors: list[str],
) -> tuple[dict, set[str]]:
    manifest_path = root / "deck-dependencies.json"
    fact = {
        "path": str(manifest_path),
        "present": manifest_path.is_file(),
        "sha256": sha256_file(manifest_path) if manifest_path.is_file() else None,
        "version": None,
        "variant": None,
        "source_revision": None,
        "builder_revision": None,
        "files": [],
        "source_sha256": None,
        "valid": False,
    }
    declared_paths: set[str] = set()
    if not manifest_path.is_file():
        return fact, declared_paths

    initial_errors = len(errors)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"invalid deck-dependencies.json: {error}")
        return fact, declared_paths
    if not isinstance(manifest, dict):
        errors.append("deck-dependencies.json must contain an object")
        return fact, declared_paths

    if manifest.get("version") != 1:
        errors.append("deck-dependencies.json version must be 1")
    fact["version"] = manifest.get("version")
    for field in ("variant", "source_revision", "builder_revision"):
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"deck-dependencies.json {field} must be a non-empty string")
            continue
        fact[field] = value.strip()
        config_value = config.get(field)
        if field != "variant" and config_value is not None and config_value != value.strip():
            errors.append(
                f"#deck-config {field} does not match deck-dependencies.json"
            )

    raw_files = manifest.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        errors.append("deck-dependencies.json files must be a non-empty array")
        raw_files = []

    records: list[dict] = []
    for index, item in enumerate(raw_files, start=1):
        label = f"dependency file {index}"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        raw_path = item.get("path")
        role = item.get("role")
        expected_hash = item.get("sha256")
        if not isinstance(raw_path, str) or not raw_path.strip():
            errors.append(f"{label} path must be a non-empty relative path")
            continue
        raw_path = raw_path.strip()
        parts = urlsplit(raw_path)
        if (
            parts.scheme or parts.netloc or parts.query or parts.fragment
            or raw_path.startswith(("/", "\\")) or "\\" in raw_path
        ):
            errors.append(f"{label} path must be a plain relative path: {display_ref(raw_path)}")
            continue
        normalized = normalized_asset_ref(raw_path)
        if not normalized or any(part == ".." for part in Path(normalized).parts):
            errors.append(f"{label} path escapes the deck directory: {display_ref(raw_path)}")
            continue
        if contains_private_path(normalized):
            errors.append(f"{label} path is private or unsafe: {display_ref(raw_path)}")
            continue
        candidate = (root / normalized).resolve()
        try:
            relative = candidate.relative_to(root.resolve()).as_posix()
        except ValueError:
            errors.append(f"{label} path escapes the deck directory: {display_ref(raw_path)}")
            continue
        if relative in declared_paths:
            errors.append(f"duplicate dependency file path: {relative}")
            continue
        declared_paths.add(relative)
        if not isinstance(role, str) or not role.strip():
            errors.append(f"{label} role must be a non-empty string")
            role = "unknown"
        if not isinstance(expected_hash, str) or not SHA256_HEX.fullmatch(expected_hash):
            errors.append(f"{label} sha256 must contain 64 hexadecimal characters")
            expected_hash = ""
        if not candidate.is_file():
            errors.append(f"dependency file is missing: {relative}")
            actual_hash = None
        else:
            try:
                actual_hash = sha256_file(candidate)
            except OSError as error:
                errors.append(f"could not hash dependency file {relative}: {error}")
                actual_hash = None
        if actual_hash is not None and expected_hash.lower() != actual_hash:
            errors.append(f"dependency hash mismatch: {relative}")
        records.append(
            {"path": relative, "role": role.strip(), "sha256": actual_hash}
        )

    records.sort(key=lambda item: item["path"])
    fact["files"] = records
    source_identity = {
        "manifest_sha256": fact["sha256"],
        "version": fact["version"],
        "variant": fact["variant"],
        "source_revision": fact["source_revision"],
        "builder_revision": fact["builder_revision"],
        "files": records,
    }
    fact["source_sha256"] = hashlib.sha256(
        json.dumps(
            source_identity,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    fact["valid"] = len(errors) == initial_errors
    return fact, declared_paths


def extract_json_script(text: str, element_id: str) -> str | None:
    match = re.search(
        rf"<script\b(?=[^>]*\bid=[\"']{re.escape(element_id)}[\"'])[^>]*>(.*?)</script\s*>",
        text, re.DOTALL | re.IGNORECASE,
    )
    return html_lib.unescape(match.group(1)).strip() if match else None


def extract_notes(text: str, errors: list[str], warnings: list[str]) -> int | None:
    payload = extract_json_script(text, "deck-notes")
    if payload is not None:
        try:
            items = json.loads(payload)
        except json.JSONDecodeError as error:
            errors.append(f"#deck-notes contains invalid JSON: {error}")
            return None
        if not isinstance(items, list):
            errors.append("#deck-notes must contain a JSON array")
            return None
        for index, item in enumerate(items, start=1):
            if isinstance(item, str):
                if not item.strip():
                    warnings.append(f"deck note {index} is empty")
            elif isinstance(item, dict):
                note = item.get("note", item.get("text"))
                if not isinstance(note, str) or not note.strip():
                    warnings.append(f"deck note {index} has no note text")
            else:
                errors.append(f"deck note {index} must be a string or object")
        return len(items)
    match = re.search(r"(?:const|let|var)\s+notes\s*=\s*\[(.*?)\]\s*;", text, re.DOTALL)
    if match:
        count = len(re.findall(r"\btitle\s*:", match.group(1)))
        if count:
            warnings.append("speaker notes use legacy JavaScript instead of #deck-notes JSON")
            return count
    return None


def parse_config(
    text: str, parser: DeckParser, notes_count: int | None,
    errors: list[str], warnings: list[str],
) -> tuple[dict, bool]:
    payload = extract_json_script(text, "deck-config")
    if payload is None:
        features: list[str] = []
        if re.search(r"\bkeydown\b|location\.hash|hashchange|\bfunction\s+show\s*\(", text):
            features.append("navigation")
        if notes_count is not None:
            features.append("presenter")
        if parser.media:
            features.append("media")
        if parser.dialogs:
            features.append("dialog")
        warnings.append(
            "missing #deck-config; inferred legacy features: "
            + (", ".join(features) if features else "core only")
        )
        return {"version": 0, "aspect": None, "features": features, "title": None}, True
    try:
        config = json.loads(payload)
    except json.JSONDecodeError as error:
        errors.append(f"#deck-config contains invalid JSON: {error}")
        return {"version": None, "aspect": None, "features": [], "title": None}, False
    if not isinstance(config, dict):
        errors.append("#deck-config must contain a JSON object")
        return {"version": None, "aspect": None, "features": [], "title": None}, False
    if config.get("aspect") not in ALLOWED_ASPECTS:
        errors.append("#deck-config aspect must be '16:9' or '4:3'")
    raw_features = config.get("features")
    features: list[str] = []
    if not isinstance(raw_features, list) or not all(isinstance(item, str) for item in raw_features):
        errors.append("#deck-config features must be an array of feature names")
    else:
        unknown = sorted(set(raw_features) - set(ALLOWED_FEATURES))
        if unknown:
            errors.append("unsupported #deck-config features: " + ", ".join(unknown))
        duplicates = sorted({item for item in raw_features if raw_features.count(item) > 1})
        if duplicates:
            errors.append("duplicate #deck-config features: " + ", ".join(duplicates))
        features = [item for item in raw_features if item in ALLOWED_FEATURES]
    if not isinstance(config.get("title"), str) or not config.get("title", "").strip():
        warnings.append("#deck-config has no non-empty title")
    for field in ("source_revision", "builder_revision"):
        if field in config and (
            not isinstance(config[field], str) or not config[field].strip()
        ):
            errors.append(f"#deck-config {field} must be a non-empty string when present")
    config = dict(config)
    config["features"] = features
    return config, False


def probe_media(path: Path) -> tuple[dict | None, str | None]:
    if not shutil.which("ffprobe"):
        return None, "ffprobe unavailable; media codecs were not inspected"
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "stream=codec_type,codec_name,pix_fmt,width,height,sample_rate,channels:format=duration",
            "-of", "json", str(path),
        ],
        text=True,
        capture_output=True,
    )
    if completed.returncode:
        return None, completed.stderr.strip() or "ffprobe failed"
    try:
        return json.loads(completed.stdout), None
    except json.JSONDecodeError as error:
        return None, f"ffprobe returned invalid JSON: {error}"


def validate_manifest(
    root: Path,
    required: bool,
    html_media_refs: dict[str, str],
    html_poster_refs: set[str],
    errors: list[str],
    warnings: list[str],
) -> tuple[dict, dict[Path, str], set[Path]]:
    manifest_path = root / "media" / "manifest.json"
    fact = {
        "path": str(manifest_path),
        "present": manifest_path.is_file(),
        "items": 0,
        "sha256": sha256_file(manifest_path) if manifest_path.is_file() else None,
    }
    media_files: dict[Path, str] = {}
    artifact_files: set[Path] = set()
    if not manifest_path.is_file():
        if required:
            errors.append("media/manifest.json is required by the media feature or local media")
        return fact, media_files, artifact_files

    artifact_files.add(manifest_path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"invalid media manifest: {error}")
        return fact, media_files, artifact_files
    if not isinstance(manifest, dict) or not isinstance(manifest.get("items"), list):
        errors.append("media/manifest.json must be an object with an items array")
        return fact, media_files, artifact_files

    items = manifest["items"]
    fact["items"] = len(items)
    allowed_truth = {"VERIFIED", "PROPOSED", "SIMULATED", "UNKNOWN"}
    keys: set[str] = set()
    manifest_media: dict[str, str] = {}
    manifest_posters: set[str] = set()

    def manifest_file(raw: object, label: str, field: str) -> tuple[str | None, Path | None]:
        if not isinstance(raw, str) or not raw.strip():
            errors.append(f"{label} has no {field}")
            return None, None
        parts = urlsplit(raw)
        if parts.scheme or raw.startswith("//") or raw.startswith("/"):
            errors.append(f"{label} {field} must be a relative path: {display_ref(raw)}")
            return None, None
        normalized = normalized_asset_ref(raw)
        candidate = (root / normalized).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            errors.append(f"{label} {field} escapes the deck directory: {display_ref(raw)}")
            return None, None
        if not candidate.is_file() or candidate.stat().st_size == 0:
            errors.append(f"{label} {field} is missing or empty: {display_ref(raw)}")
            return None, None
        artifact_files.add(candidate)
        return normalized, candidate

    for index, item in enumerate(items, start=1):
        label = f"media manifest item {index}"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        key = item.get("key")
        if not isinstance(key, str) or not key.strip():
            errors.append(f"{label} has no non-empty key")
        elif key in keys:
            errors.append(f"duplicate media manifest key: {key}")
        else:
            keys.add(key)

        truth = item.get("truth", item.get("truth_state"))
        if truth not in allowed_truth:
            errors.append(f"{label} has invalid truth state: {truth!r}")
        source = item.get("source", item.get("provenance", ""))
        if not isinstance(source, str):
            errors.append(f"{label} source/provenance must be a string")
        elif not source.strip():
            errors.append(f"{label} has no shareable source/provenance note")
        elif contains_private_path(source):
            errors.append(f"{label} source contains a private filename or local path")

        normalized_src, source_path = manifest_file(item.get("src"), label, "src")
        kind = item.get("kind")
        if kind not in {None, "video", "audio"}:
            errors.append(f"{label} has invalid kind: {kind!r}")
            kind = None
        if kind is None and normalized_src:
            suffix = Path(normalized_src).suffix.lower()
            if item.get("poster") or suffix in VIDEO_SUFFIXES:
                kind = "video"
            elif suffix in AUDIO_SUFFIXES:
                kind = "audio"
            if kind:
                warnings.append(f"{label} has no kind; inferred {kind} for legacy compatibility")
        if kind is None:
            errors.append(f"{label} kind must be 'video' or 'audio'")
            continue
        if normalized_src:
            manifest_media[normalized_src] = kind
        if source_path:
            media_files[source_path] = kind

        if kind == "video":
            normalized_poster, _ = manifest_file(item.get("poster"), label, "poster")
            if normalized_poster:
                manifest_posters.add(normalized_poster)
            for field in ("duration_seconds", "width", "height", "video_codec", "pixel_format"):
                if field not in item:
                    warnings.append(f"{label} has no {field}")
        else:
            if item.get("poster"):
                normalized_poster, _ = manifest_file(item.get("poster"), label, "poster")
                if normalized_poster:
                    manifest_posters.add(normalized_poster)
            for field in ("duration_seconds", "audio_codec"):
                if field not in item:
                    warnings.append(f"{label} has no {field}")

    unlisted_media = sorted(ref for ref in html_media_refs if ref not in manifest_media)
    if unlisted_media:
        errors.append("HTML media missing from manifest: " + ", ".join(unlisted_media))
    wrong_kinds = sorted(
        ref for ref, kind in html_media_refs.items()
        if manifest_media.get(ref) is not None and manifest_media[ref] != kind
    )
    if wrong_kinds:
        errors.append("HTML and manifest media kinds differ: " + ", ".join(wrong_kinds))
    unlisted_posters = sorted(ref for ref in html_poster_refs if ref not in manifest_posters)
    if unlisted_posters:
        errors.append("HTML video posters missing from manifest: " + ", ".join(unlisted_posters))
    unused_media = sorted(ref for ref in manifest_media if ref not in html_media_refs)
    if unused_media:
        warnings.append("manifest media not referenced by HTML: " + ", ".join(unused_media))
    unused_posters = sorted(ref for ref in manifest_posters if ref not in html_poster_refs)
    if unused_posters:
        warnings.append("manifest posters not referenced by HTML: " + ", ".join(unused_posters))
    return fact, media_files, artifact_files


def inspect_media(
    root: Path,
    files: dict[Path, str],
    strict_probe: bool,
    errors: list[str],
    warnings: list[str],
) -> list[dict]:
    reports: list[dict] = []
    for path, kind in sorted(files.items(), key=lambda item: str(item[0])):
        report, problem = probe_media(path)
        if problem:
            message = f"ffprobe failed for {path.name}: {problem}"
            if problem.startswith("ffprobe unavailable") and not strict_probe:
                warnings.append(message)
            else:
                errors.append(message)
            continue
        assert report is not None
        streams = report.get("streams", [])
        video = next((item for item in streams if item.get("codec_type") == "video"), None)
        audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
        item = {
            "file": str(path.relative_to(root)), "kind": kind,
            "video_codec": video.get("codec_name") if video else None,
            "pixel_format": video.get("pix_fmt") if video else None,
            "width": video.get("width") if video else None,
            "height": video.get("height") if video else None,
            "audio_codec": audio.get("codec_name") if audio else None,
            "duration": report.get("format", {}).get("duration"),
        }
        reports.append(item)
        suffix = path.suffix.lower()
        if kind == "video":
            if not video:
                errors.append(f"{path.name} has no video stream")
                continue
            if suffix == ".mp4" and video.get("codec_name") != "h264":
                errors.append(f"{path.name} must use H.264 video in MP4")
            elif suffix != ".mp4":
                warnings.append(f"{path.name} is legacy/non-preferred video; prepare MP4 for portability")
            if video.get("pix_fmt") not in {"yuv420p", "yuvj420p"}:
                warnings.append(f"{path.name} pixel format may be browser-sensitive: {video.get('pix_fmt')!r}")
            if audio and audio.get("codec_name") != "aac" and suffix == ".mp4":
                errors.append(f"{path.name} MP4 audio must use AAC")
        else:
            if not audio:
                errors.append(f"{path.name} has no audio stream")
                continue
            if suffix == ".m4a" and audio.get("codec_name") != "aac":
                errors.append(f"{path.name} must use AAC audio in M4A")
            elif suffix != ".m4a":
                warnings.append(f"{path.name} is legacy/non-preferred audio; prepare M4A for portability")
    return reports


def validate(path: Path, check_receipt: Path | None = None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    facts: dict = {}

    html_path = path.expanduser().resolve()
    if not html_path.is_file():
        return {
            "ok": False,
            "errors": [f"HTML file does not exist: {html_path}"],
            "warnings": [],
            "facts": {},
        }

    text = html_path.read_text(encoding="utf-8")
    parser = DeckParser()
    parser.feed(text)
    root = html_path.parent
    parser.assets.extend(extract_css_refs(text))
    parser.assets.extend(extract_dynamic_refs(text))

    legacy_notes_count = extract_notes(text, errors, warnings)
    inline_notes_count = len(parser.notes) if parser.notes else None
    inferred_notes_count = inline_notes_count or legacy_notes_count
    config, legacy = parse_config(text, parser, inferred_notes_count, errors, warnings)
    features = config.get("features", [])

    if not parser.html_lang:
        if legacy:
            warnings.append("document has no non-empty <html lang> value")
        else:
            errors.append("document must declare a non-empty <html lang> value")

    if not parser.has_stage:
        errors.append("missing #stage")
    if not parser.slides:
        errors.append('no <section class="slide"> elements found')
    duplicates = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
    if duplicates:
        errors.append(f"duplicate element IDs: {', '.join(duplicates)}")

    slide_ids: list[str] = []
    for number, slide in enumerate(parser.slides, start=1):
        label = slide.get("id") or f"slide {number}"
        if not slide.get("id"):
            errors.append(f"slide {number} has no id")
        else:
            slide_ids.append(slide["id"])
        if not slide.get("title"):
            warnings.append(f"{label} has no data-title")
        if not slide.get("headings"):
            warnings.append(f"{label} has no h1 or h2")

    if not legacy and not features and len(parser.slides) > 1:
        errors.append(
            "core-only deck cannot contain multiple hidden slides; enable navigation "
            "or render a single visible slide"
        )

    if "navigation" in features:
        active_count = sum(1 for item in parser.slides if item.get("active"))
        if active_count != 1:
            errors.append(f"navigation expects exactly one initial active slide; found {active_count}")
        inactive = [
            item.get("id") or "unnamed" for item in parser.slides
            if not item.get("active")
            and not (item.get("inert") and item.get("aria_hidden") == "true")
        ]
        if inactive:
            warnings.append(
                "initial inactive slides should be inert and aria-hidden: " + ", ".join(inactive)
            )
        if not re.search(r"\bkeydown\b|onkeydown", text, re.IGNORECASE):
            errors.append("navigation feature has no keyboard event handler")
        elif not re.search(
            r"ArrowLeft|ArrowRight|PageUp|PageDown|(?:['\"]Home['\"])|(?:['\"]End['\"])",
            text,
            re.IGNORECASE,
        ):
            errors.append("navigation keyboard handler has no recognized slide-navigation keys")
        if len(parser.slides) > 1 and not re.search(r"location\.hash|hashchange", text):
            warnings.append("navigation feature has no detectable hash navigation")

    if "presenter" in features:
        if legacy and not parser.notes:
            if legacy_notes_count is None:
                errors.append("presenter feature requires statically verifiable speaker notes")
            elif legacy_notes_count != len(parser.slides):
                errors.append(
                    f"detected {legacy_notes_count} notes for {len(parser.slides)} slides"
                )
            empty_note_warnings = [
                item for item in warnings
                if item.startswith("deck note ")
                and (item.endswith(" is empty") or item.endswith(" has no note text"))
            ]
            if empty_note_warnings:
                errors.append("presenter feature requires non-empty speaker notes")
        else:
            for number, slide in enumerate(parser.slides, start=1):
                slide_notes = slide.get("notes", [])
                if len(slide_notes) != 1:
                    errors.append(
                        "presenter feature requires one inline data-notes element per slide; "
                        f"slide {number} has {len(slide_notes)}"
                    )
                    continue
                note = slide_notes[0]
                if not "".join(note["chunks"]).strip():
                    errors.append(
                        f"presenter feature requires non-empty inline speaker notes on slide {number}"
                    )
                duration = note.get("duration")
                if duration is None or not re.fullmatch(r"\d+", duration.strip()):
                    errors.append(
                        f"presenter data-duration on slide {number} must be a non-negative integer"
                    )
            outside_notes = [item for item in parser.notes if item.get("slide") is None]
            if outside_notes:
                errors.append("presenter data-notes elements must be nested inside their slide")
            if not legacy and legacy_notes_count is not None:
                warnings.append(
                    "#deck-notes is legacy metadata; v1 presenter validation uses inline data-notes"
                )
    elif inferred_notes_count is not None and inferred_notes_count != len(parser.slides):
        warnings.append(
            f"unused notes count ({inferred_notes_count}) differs from slides ({len(parser.slides)})"
        )

    if "dialog" in features:
        if not parser.dialogs:
            errors.append("dialog feature is enabled but no dialog is present")
        if parser.dialogs and not re.search(r"showModal\s*\(|\brole=[\"']dialog[\"']", text):
            warnings.append("dialog feature has no detectable modal-opening behavior")

    has_motion = bool(re.search(r"(?:transition|animation)\s*:|\.animate\s*\(", text, re.IGNORECASE))
    if has_motion and not re.search(r"prefers-reduced-motion", text, re.IGNORECASE):
        errors.append("motion is present without a prefers-reduced-motion fallback")
    if not re.search(r"@media\s+print", text, re.IGNORECASE):
        warnings.append("print styles were not detected")

    remaining_markers = sorted(marker for marker in LEGACY_STARTER_MARKERS if marker in text)
    if "WOWDECK_PLACEHOLDER" in text:
        remaining_markers.insert(0, "WOWDECK_PLACEHOLDER")
    if remaining_markers:
        errors.append("starter placeholders remain: " + "; ".join(dict.fromkeys(remaining_markers)))

    if re.search(
        r"file://|/(?:Users|home)/|(?:^|[\s\"'(=])[A-Za-z]:[\\/]", text, re.IGNORECASE,
    ):
        errors.append("absolute local path or file:// reference detected")
    if re.search(
        r"(?:url\(\s*[\"']?|@import\s+[\"']?)(?:https?:)?//", text, re.IGNORECASE,
    ):
        errors.append("remote CSS asset detected; package runtime assets locally")

    html_media_refs: dict[str, str] = {}
    html_poster_refs: set[str] = set()
    for index, item in enumerate(parser.media, start=1):
        kind = item["kind"]
        if not item["srcs"]:
            errors.append(f"{kind} {index} has no src or <source>")
        if kind == "video" and not item.get("poster"):
            errors.append(f"video {index} has no poster")
        for raw in item["srcs"]:
            parts = urlsplit(raw)
            if not parts.scheme and not raw.startswith(("//", "/", "#")):
                html_media_refs[normalized_asset_ref(raw)] = kind
        poster = item.get("poster")
        if poster:
            parts = urlsplit(poster)
            if not parts.scheme and not poster.startswith(("//", "/", "#")):
                html_poster_refs.add(normalized_asset_ref(poster))

    checked_assets: set[Path] = set()
    artifact_files: set[Path] = {html_path}
    html_media_files: dict[Path, str] = {}
    runtime_dependencies: set[str] = set()
    css_pending: list[Path] = []
    script_pending: list[Path] = []
    for element, raw in parser.assets:
        parts = urlsplit(raw)
        scheme = parts.scheme.lower()
        normalized_path = unquote(parts.path).lower()
        if scheme in {"http", "https"} or raw.startswith("//"):
            if element != "a[href]":
                errors.append(f"remote runtime asset in {element}: {display_ref(raw)}")
            continue
        if scheme == "blob":
            errors.append(f"non-portable blob asset in {element}: {display_ref(raw)}")
            continue
        if scheme == "data":
            if len(raw) > 2_000_000:
                warnings.append(f"large embedded data asset in {element}: {len(raw)} characters")
            continue
        if scheme in {"mailto", "tel"} or raw.startswith("#"):
            continue
        if scheme:
            errors.append(f"unsupported URL scheme in {element}: {display_ref(raw)}")
            continue
        if any(token in normalized_path for token in PRIVATE_NAMES):
            errors.append(f"suspicious private reference in {element}: {display_ref(raw)}")
        candidate = local_path(raw, root)
        if candidate is None:
            continue
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            errors.append(f"asset escapes deck directory in {element}: {display_ref(raw)}")
            continue
        if candidate not in checked_assets:
            checked_assets.add(candidate)
            if not candidate.is_file():
                errors.append(f"missing local asset in {element}: {display_ref(raw)}")
                continue
            if candidate.stat().st_size == 0:
                errors.append(f"empty local asset in {element}: {display_ref(raw)}")
                continue
            artifact_files.add(candidate)
        relative = candidate.relative_to(root.resolve()).as_posix()
        runtime_dependencies.add(relative)
        if candidate.suffix.lower() == ".css":
            css_pending.append(candidate)
        if candidate.suffix.lower() in {".js", ".mjs", ".cjs"}:
            script_pending.append(candidate)
        normalized = normalized_asset_ref(raw)
        if normalized in html_media_refs and candidate.is_file():
            html_media_files[candidate] = html_media_refs[normalized]

    script_seen: set[Path] = set()
    while script_pending:
        script_path = script_pending.pop()
        if script_path in script_seen or not script_path.is_file():
            continue
        script_seen.add(script_path)
        try:
            script_text = script_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            errors.append(
                f"could not inspect script dependency {script_path.relative_to(root)}: {error}"
            )
            continue
        for element, raw in extract_dynamic_refs(script_text):
            parts = urlsplit(raw)
            scheme = parts.scheme.lower()
            label = f"{script_path.relative_to(root).as_posix()} {element}"
            if scheme in {"http", "https"} or raw.startswith("//"):
                errors.append(f"remote runtime asset in {label}: {display_ref(raw)}")
                continue
            if scheme == "data" or raw.startswith("#"):
                continue
            if scheme == "blob":
                errors.append(f"non-portable blob asset in {label}: {display_ref(raw)}")
                continue
            if scheme:
                errors.append(f"unsupported URL scheme in {label}: {display_ref(raw)}")
                continue
            if contains_private_path(raw):
                errors.append(f"suspicious private reference in {label}: {display_ref(raw)}")
            candidate = (script_path.parent / unquote(parts.path)).resolve()
            try:
                relative = candidate.relative_to(root.resolve()).as_posix()
            except ValueError:
                errors.append(f"asset escapes deck directory in {label}: {display_ref(raw)}")
                continue
            runtime_dependencies.add(relative)
            if candidate not in checked_assets:
                checked_assets.add(candidate)
                if not candidate.is_file():
                    errors.append(f"missing local asset in {label}: {display_ref(raw)}")
                    continue
                if candidate.stat().st_size == 0:
                    errors.append(f"empty local asset in {label}: {display_ref(raw)}")
                    continue
                artifact_files.add(candidate)
            if not candidate.is_file():
                continue
            suffix = candidate.suffix.lower()
            if suffix in {".js", ".mjs", ".cjs"}:
                script_pending.append(candidate)
            elif suffix == ".css":
                css_pending.append(candidate)

    css_seen: set[Path] = set()
    while css_pending:
        css_path = css_pending.pop()
        if css_path in css_seen or not css_path.is_file():
            continue
        css_seen.add(css_path)
        try:
            css_text = css_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            errors.append(
                f"could not inspect CSS dependency {css_path.relative_to(root)}: {error}"
            )
            continue
        for element, raw in extract_css_refs(css_text):
            parts = urlsplit(raw)
            scheme = parts.scheme.lower()
            label = f"{css_path.relative_to(root).as_posix()} {element}"
            if scheme in {"http", "https"} or raw.startswith("//"):
                errors.append(f"remote runtime asset in {label}: {display_ref(raw)}")
                continue
            if scheme == "data" or raw.startswith("#"):
                continue
            if scheme == "blob":
                errors.append(f"non-portable blob asset in {label}: {display_ref(raw)}")
                continue
            if scheme:
                errors.append(f"unsupported URL scheme in {label}: {display_ref(raw)}")
                continue
            if contains_private_path(raw):
                errors.append(f"suspicious private reference in {label}: {display_ref(raw)}")
            candidate = (css_path.parent / unquote(parts.path)).resolve()
            try:
                relative = candidate.relative_to(root.resolve()).as_posix()
            except ValueError:
                errors.append(f"asset escapes deck directory in {label}: {display_ref(raw)}")
                continue
            runtime_dependencies.add(relative)
            if candidate not in checked_assets:
                checked_assets.add(candidate)
                if not candidate.is_file():
                    errors.append(f"missing local asset in {label}: {display_ref(raw)}")
                    continue
                if candidate.stat().st_size == 0:
                    errors.append(f"empty local asset in {label}: {display_ref(raw)}")
                    continue
                artifact_files.add(candidate)
            if candidate.is_file() and candidate.suffix.lower() == ".css":
                css_pending.append(candidate)

    manifest_required = not legacy and ("media" in features or bool(html_media_refs))
    if legacy and html_media_refs and not (root / "media" / "manifest.json").is_file():
        warnings.append(
            "legacy deck has local media but no manifest; add one to record truth and provenance"
        )
    manifest_fact, manifest_media_files, manifest_artifacts = validate_manifest(
        root, manifest_required, html_media_refs, html_poster_refs, errors, warnings,
    )
    artifact_files.update(manifest_artifacts)
    if manifest_fact.get("present"):
        runtime_dependencies.add("media/manifest.json")
    media_files = dict(manifest_media_files)
    media_files.update(html_media_files)
    media_reports = inspect_media(root, media_files, not legacy, errors, warnings)

    dependency_fact, declared_dependencies = validate_dependency_manifest(
        root, config, errors,
    )
    missing_dependencies = sorted(runtime_dependencies - declared_dependencies)
    if dependency_fact["present"] and missing_dependencies:
        errors.append(
            "undeclared local runtime dependencies: " + ", ".join(missing_dependencies)
        )
        dependency_fact["valid"] = False
    elif not dependency_fact["present"] and runtime_dependencies:
        message = (
            "deck-dependencies.json is required for local runtime dependencies: "
            + ", ".join(sorted(runtime_dependencies))
        )
        if legacy:
            warnings.append(message)
        else:
            errors.append(message)

    asset_hashes: dict[str, str] = {}
    for candidate in sorted(artifact_files):
        try:
            relative = str(candidate.relative_to(root)).replace("\\", "/")
            asset_hashes[relative] = sha256_file(candidate)
        except (OSError, ValueError) as error:
            errors.append(f"could not hash artifact file {candidate}: {error}")

    index_relative = str(html_path.relative_to(root)).replace("\\", "/")
    index_sha256 = asset_hashes.get(index_relative, sha256_file(html_path))
    manifest_sha256 = manifest_fact.get("sha256")
    source_bound = bool(
        dependency_fact.get("present")
        and dependency_fact.get("valid")
        and not missing_dependencies
    )
    if legacy:
        passing_status = "PASS_LEGACY_ARTIFACT_ONLY"
        validation_level = "legacy_artifact_only"
        reproducibility = "artifact-only"
    elif source_bound:
        passing_status = "PASS_SOURCE_BOUND"
        validation_level = "source_bound"
        reproducibility = "source-bound"
    else:
        passing_status = "PASS_RENDERED_ARTIFACT"
        validation_level = "rendered_artifact"
        reproducibility = "rendered-only"
    effective_source_revision = (
        dependency_fact.get("source_revision") or config.get("source_revision")
    )
    effective_builder_revision = (
        dependency_fact.get("builder_revision") or config.get("builder_revision")
    )
    identity = {
        "files": asset_hashes,
        "features": features,
        "slide_count": len(parser.slides),
        "dependency_manifest_sha256": dependency_fact.get("sha256"),
        "dependency_files": dependency_fact.get("files", []),
        "source_sha256": dependency_fact.get("source_sha256"),
        "variant": dependency_fact.get("variant"),
        "source_revision": effective_source_revision,
        "builder_revision": effective_builder_revision,
    }
    artifact_sha256 = hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    facts.update(
        {
            "html": str(html_path),
            "legacy_config": legacy,
            "config": config,
            "features": features,
            "source_revision": effective_source_revision,
            "builder_revision": effective_builder_revision,
            "variant": dependency_fact.get("variant"),
            "slides": len(parser.slides),
            "slide_count": len(parser.slides),
            "slide_ids": slide_ids,
            "index_sha256": index_sha256,
            "manifest_sha256": manifest_sha256,
            "dependency_manifest_sha256": dependency_fact.get("sha256"),
            "dependency_files": dependency_fact.get("files", []),
            "source_sha256": dependency_fact.get("source_sha256"),
            "artifact_sha256": artifact_sha256,
            "artifact_identity": identity,
            "asset_sha256": asset_hashes,
            "local_assets_checked": len(checked_assets),
            "media": media_reports,
            "manifest": manifest_fact,
            "dependency_manifest": dependency_fact,
            "notes": inline_notes_count if parser.notes else legacy_notes_count,
            "validation_level": validation_level,
            "reproducibility": reproducibility,
        }
    )

    if check_receipt is not None:
        receipt_path = check_receipt.expanduser()
        if not receipt_path.is_absolute():
            receipt_path = root / receipt_path
        receipt_path = receipt_path.resolve()
        if not receipt_path.is_file():
            errors.append(f"validation receipt does not exist: {receipt_path}")
            facts["receipt_status"] = "missing"
        else:
            try:
                previous = json.loads(receipt_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                errors.append(f"invalid validation receipt: {error}")
                facts["receipt_status"] = "invalid"
            else:
                previous_hash = previous.get("artifact_sha256") if isinstance(previous, dict) else None
                if previous_hash != artifact_sha256:
                    errors.append("validation receipt is stale for the current artifact")
                    facts["receipt_status"] = "stale"
                else:
                    facts["receipt_status"] = "current"

    ok = not errors
    facts["status"] = passing_status if ok else "FAIL"
    return {"ok": ok, "errors": errors, "warnings": warnings, "facts": facts}


def receipt_payload(result: dict) -> dict:
    facts = result["facts"]
    return {
        "version": 1,
        "status": facts["status"],
        "validation_level": facts["validation_level"],
        "reproducibility": facts["reproducibility"],
        "index_sha256": facts["index_sha256"],
        "slide_count": facts["slide_count"],
        "manifest_sha256": facts["manifest_sha256"],
        "features": facts["features"],
        "source_revision": facts.get("source_revision"),
        "builder_revision": facts.get("builder_revision"),
        "variant": facts.get("variant"),
        "dependency_manifest_sha256": facts.get("dependency_manifest_sha256"),
        "dependency_files": facts.get("dependency_files", []),
        "source_sha256": facts.get("source_sha256"),
        "asset_sha256": facts["asset_sha256"],
        "artifact_sha256": facts["artifact_sha256"],
    }


def main() -> int:
    args = parse_args()
    result = validate(args.html_file, args.check_receipt)
    if args.receipt is not None:
        if result["ok"]:
            root = args.html_file.expanduser().resolve().parent
            receipt_path = args.receipt.expanduser()
            if not receipt_path.is_absolute():
                receipt_path = root / receipt_path
            receipt_path = receipt_path.resolve()
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(
                json.dumps(receipt_payload(result), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result["facts"]["receipt_written"] = str(receipt_path)
        else:
            result["warnings"].append("receipt was not written because validation failed")

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = result["facts"].get("status", "FAIL")
        print(f"[{status}] {result['facts'].get('html', args.html_file)}")
        print(f"Slides: {result['facts'].get('slide_count', 0)}")
        features = result["facts"].get("features", [])
        print(f"Features: {', '.join(features) if features else 'core only'}")
        if result["facts"].get("index_sha256"):
            print(f"Index SHA256: {result['facts']['index_sha256']}")
        print(f"Manifest SHA256: {result['facts'].get('manifest_sha256') or 'none'}")
        if result["facts"].get("artifact_sha256"):
            print(f"Artifact SHA256: {result['facts']['artifact_sha256']}")
        if result["facts"].get("receipt_written"):
            print(f"Receipt: {result['facts']['receipt_written']}")
        for item in result["errors"]:
            print(f"ERROR: {item}")
        for item in result["warnings"]:
            print(f"WARN: {item}")
        if result["ok"] and not result["warnings"]:
            print("No structural warnings detected.")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
