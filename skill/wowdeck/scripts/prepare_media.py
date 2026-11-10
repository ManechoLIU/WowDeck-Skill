#!/usr/bin/env python3
"""Prepare browser-safe video or audio and record its provenance."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


SAFE_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
TRUTH_STATES = ("VERIFIED", "PROPOSED", "SIMULATED", "UNKNOWN")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    # Keep the positional shape of the previous video-only command.
    parser.add_argument("input_media", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--kind", choices=("auto", "video", "audio"), default="auto")
    parser.add_argument("--name", help="Output basename; defaults to input stem")
    parser.add_argument("--truth", choices=TRUTH_STATES, default="UNKNOWN")
    parser.add_argument(
        "--source",
        required=True,
        help="Shareable provenance note or public identifier",
    )
    parser.add_argument("--poster-at", type=float, help="Video poster timestamp in seconds")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing output and manifest entry with the same name",
    )
    return parser.parse_args()


def run(command: list[str]) -> None:
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise SystemExit(f"command failed: {' '.join(command[:2])}\n{detail}")


def probe(path: Path) -> dict:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        text=True,
        capture_output=True,
    )
    if completed.returncode:
        raise SystemExit(completed.stderr.strip() or f"ffprobe failed for {path}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise SystemExit(f"ffprobe returned invalid JSON for {path}: {error}") from error


def stream(info: dict, codec_type: str) -> dict | None:
    candidates = [
        item for item in info.get("streams", []) if item.get("codec_type") == codec_type
    ]
    if codec_type == "video":
        visual = [
            item
            for item in candidates
            if not (item.get("disposition") or {}).get("attached_pic")
        ]
        return visual[0] if visual else None
    return candidates[0] if candidates else None


def validate_source_note(value: str) -> str:
    note = value.strip()
    if not note:
        raise SystemExit("--source must not be empty")
    if len(note) > 500 or any(character in note for character in "\r\n"):
        raise SystemExit("--source must be a single shareable line of at most 500 characters")
    if re.search(
        r"file://|/(?:Users|home)/|(?:^|[\s\"'(=])[A-Za-z]:[\\/]",
        note,
        re.IGNORECASE,
    ):
        raise SystemExit("--source must not contain a local absolute path")
    if any(
        token in note.lower()
        for token in (".env", ".git/", "聊天记录", "原文导出", "transcript")
    ):
        raise SystemExit("--source appears to contain a private filename")
    return note


def load_manifest(path: Path) -> dict:
    manifest = {
        "version": 1,
        "items": [],
        "truth_states": list(TRUTH_STATES),
    }
    if not path.exists():
        return manifest
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"invalid JSON manifest: {path}: {error}") from error
    if not isinstance(existing, dict) or not isinstance(existing.get("items"), list):
        raise SystemExit(f"manifest must contain an items array: {path}")
    return existing


def inferred_kind(requested: str, info: dict) -> str:
    video = stream(info, "video")
    audio = stream(info, "audio")
    if requested == "video":
        if not video:
            raise SystemExit("input contains no video stream")
        return requested
    if requested == "audio":
        if not audio:
            raise SystemExit("input contains no audio stream")
        return requested
    if video:
        return "video"
    if audio:
        return "audio"
    raise SystemExit("input contains no usable video or audio stream")


def prepare_video(source: Path, temporary: Path, info: dict, poster_at: float | None) -> tuple[Path, Path, dict]:
    source_video = stream(info, "video") or {}
    source_audio = stream(info, "audio")
    compatible_video = source_video.get("codec_name") == "h264" and source_video.get(
        "pix_fmt"
    ) in {"yuv420p", "yuvj420p"}
    compatible_audio = source_audio is None or source_audio.get("codec_name") == "aac"

    temp_media = temporary / "output.mp4"
    temp_poster = temporary / "poster.jpg"
    command = ["ffmpeg", "-y", "-i", str(source)]
    if compatible_video and compatible_audio:
        command += ["-map", "0:v:0", "-map", "0:a?", "-c", "copy"]
        mode = "remuxed"
    else:
        command += [
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
        ]
        mode = "transcoded"
    command += ["-movflags", "+faststart", str(temp_media)]
    run(command)

    output_info = probe(temp_media)
    output_video = stream(output_info, "video") or {}
    output_audio = stream(output_info, "audio")
    if output_video.get("codec_name") != "h264":
        raise SystemExit("prepared video is not H.264")
    if output_video.get("pix_fmt") not in {"yuv420p", "yuvj420p"}:
        raise SystemExit(
            f"prepared video has browser-sensitive pixel format {output_video.get('pix_fmt')!r}"
        )
    if output_audio and output_audio.get("codec_name") != "aac":
        raise SystemExit("prepared video audio is not AAC")

    duration = float(output_info.get("format", {}).get("duration") or 0)
    selected_poster_at = poster_at
    if selected_poster_at is None:
        selected_poster_at = duration * 0.22 if duration > 0 else 0
        if duration > 0:
            selected_poster_at = min(selected_poster_at, max(duration - 0.001, 0))
    if selected_poster_at < 0 or (duration and selected_poster_at > duration):
        raise SystemExit(f"--poster-at must be between 0 and {duration:.3f}")

    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{selected_poster_at:.3f}",
            "-i",
            str(temp_media),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(temp_poster),
        ]
    )
    if not temp_poster.is_file() or temp_poster.stat().st_size == 0:
        raise SystemExit("ffmpeg did not produce a usable video poster")

    details = {
        "duration_seconds": round(duration, 3),
        "width": output_video.get("width"),
        "height": output_video.get("height"),
        "video_codec": output_video.get("codec_name"),
        "pixel_format": output_video.get("pix_fmt"),
        "audio_codec": output_audio.get("codec_name") if output_audio else None,
        "preparation": mode,
    }
    return temp_media, temp_poster, details


def prepare_audio(source: Path, temporary: Path, info: dict) -> tuple[Path, dict]:
    source_audio = stream(info, "audio") or {}
    temp_media = temporary / "output.m4a"
    command = ["ffmpeg", "-y", "-i", str(source), "-map", "0:a:0", "-vn"]
    if source_audio.get("codec_name") == "aac":
        command += ["-c:a", "copy"]
        mode = "remuxed"
    else:
        command += ["-c:a", "aac", "-b:a", "160k"]
        mode = "transcoded"
    command += ["-movflags", "+faststart", str(temp_media)]
    run(command)

    output_info = probe(temp_media)
    output_audio = stream(output_info, "audio") or {}
    if stream(output_info, "video"):
        raise SystemExit("prepared audio unexpectedly contains a video stream")
    if output_audio.get("codec_name") != "aac":
        raise SystemExit("prepared audio is not AAC")
    duration = float(output_info.get("format", {}).get("duration") or 0)
    details = {
        "duration_seconds": round(duration, 3),
        "audio_codec": output_audio.get("codec_name"),
        "sample_rate": output_audio.get("sample_rate"),
        "channels": output_audio.get("channels"),
        "preparation": mode,
    }
    return temp_media, details


def main() -> int:
    args = parse_args()
    for dependency in ("ffmpeg", "ffprobe"):
        if not shutil.which(dependency):
            raise SystemExit(f"{dependency} is required but was not found")

    source_path = args.input_media.expanduser().resolve()
    if not source_path.is_file():
        raise SystemExit(f"input media does not exist: {source_path}")

    name = args.name or source_path.stem
    if not SAFE_NAME.fullmatch(name):
        raise SystemExit("--name may contain only letters, digits, hyphens, and underscores")
    source_note = validate_source_note(args.source)

    output_dir = args.output_dir.expanduser().resolve()
    if output_dir.name != "media":
        raise SystemExit("output_dir must be the deck's media directory named 'media'")
    manifest_path = output_dir / "manifest.json"
    manifest = load_manifest(manifest_path)

    input_info = probe(source_path)
    kind = inferred_kind(args.kind, input_info)
    if kind == "audio" and args.poster_at is not None:
        raise SystemExit("--poster-at applies only to video")

    extension = ".mp4" if kind == "video" else ".m4a"
    media_path = output_dir / f"{name}{extension}"
    poster_path = output_dir / f"{name}.jpg" if kind == "video" else None
    name_exists = any(
        isinstance(item, dict) and item.get("key") == name for item in manifest["items"]
    )
    output_exists = media_path.exists() or (poster_path is not None and poster_path.exists())
    if not args.force and (output_exists or name_exists):
        raise SystemExit(f"refusing to overwrite media named {name!r}; pass --force to replace it")

    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="wowdeck-media-") as temporary_name:
        temporary = Path(temporary_name)
        if kind == "video":
            temp_media, temp_poster, details = prepare_video(
                source_path, temporary, input_info, args.poster_at
            )
            temp_media.replace(media_path)
            assert poster_path is not None
            temp_poster.replace(poster_path)
        else:
            temp_media, details = prepare_audio(source_path, temporary, input_info)
            temp_media.replace(media_path)

    entry = {
        "key": name,
        "kind": kind,
        "src": f"media/{media_path.name}",
        "truth": args.truth,
        "source": source_note,
        **details,
    }
    if poster_path is not None:
        entry["poster"] = f"media/{poster_path.name}"

    manifest["items"] = [
        item
        for item in manifest["items"]
        if not (isinstance(item, dict) and item.get("key") == name)
    ]
    manifest["items"].append(entry)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"{details['preparation'].capitalize()} {kind}: {media_path}")
    if poster_path is not None:
        print(f"Poster: {poster_path}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
