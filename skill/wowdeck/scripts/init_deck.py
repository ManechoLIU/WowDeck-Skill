#!/usr/bin/env python3
"""Initialize a portable, feature-aware WowDeck HTML presentation."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
LANG_TAG = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
ALLOWED_FEATURES = ("navigation", "presenter", "media", "dialog")
BACKGROUND_MODES = ("light", "dark")
ASPECTS = {
    "16:9": (16, 9),
    "4:3": (4, 3),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path, help="Directory to create")
    parser.add_argument("--title", default="Untitled Presentation")
    parser.add_argument("--subtitle", default="A presentation for its intended audience")
    parser.add_argument("--lang", default="en", help="BCP 47-style document language tag")
    parser.add_argument("--accent", default="#56D9B0", help="Six-digit CSS hex color")
    parser.add_argument("--aspect", choices=tuple(ASPECTS), default="16:9")
    parser.add_argument(
        "--background-mode",
        choices=BACKGROUND_MODES,
        default="light",
        help="One canvas mode shared by every slide (default: light)",
    )
    parser.add_argument(
        "--features",
        nargs="+",
        action="append",
        metavar="FEATURE",
        help=(
            "Enabled features, separated by spaces or commas. "
            "Allowed: navigation, presenter, media, dialog, or 'none'. Default: navigation"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace index.html; preserve an existing media manifest",
    )
    return parser.parse_args()


def normalized_features(groups: list[list[str]] | None) -> list[str]:
    if not groups:
        return ["navigation"]

    requested: list[str] = []
    for group in groups:
        for value in group:
            requested.extend(item.strip() for item in value.split(",") if item.strip())

    if "none" in requested:
        if len(requested) != 1:
            raise SystemExit("feature 'none' cannot be combined with other features")
        return []

    unknown = sorted(set(requested) - set(ALLOWED_FEATURES))
    if unknown:
        allowed = ", ".join(ALLOWED_FEATURES)
        raise SystemExit(f"unsupported feature(s): {', '.join(unknown)}; allowed: {allowed}")

    # A stable order keeps config and validation receipts deterministic.
    return [feature for feature in ALLOWED_FEATURES if feature in requested]


def html_safe_json(value: object) -> str:
    """Serialize JSON without characters that can escape an HTML script block."""
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return payload.translate(
        str.maketrans(
            {
                "<": r"\u003c",
                ">": r"\u003e",
                "&": r"\u0026",
                "\u2028": r"\u2028",
                "\u2029": r"\u2029",
            }
        )
    )


def replace_deck_config(source: str, config: dict) -> str:
    payload = html_safe_json(config)
    pattern = re.compile(
        r"(<script\b(?=[^>]*\bid=[\"']deck-config[\"'])[^>]*>)(.*?)(</script\s*>)",
        re.DOTALL | re.IGNORECASE,
    )
    if pattern.search(source):
        return pattern.sub(lambda match: f"{match.group(1)}{payload}{match.group(3)}", source, count=1)
    if "{{DECK_CONFIG_JSON}}" in source:
        return source.replace("{{DECK_CONFIG_JSON}}", payload)
    raise SystemExit("starter template has no #deck-config JSON block")


def main() -> int:
    args = parse_args()
    if not HEX_COLOR.fullmatch(args.accent):
        raise SystemExit("--accent must be a six-digit hex color such as #56D9B0")
    if not LANG_TAG.fullmatch(args.lang):
        raise SystemExit("--lang must be a BCP 47-style tag such as en, zh-CN, or pt-BR")

    features = normalized_features(args.features)
    root = Path(__file__).resolve().parents[1]
    template_path = root / "assets" / "starter" / "index.html"
    if not template_path.is_file():
        raise SystemExit(f"starter template is missing: {template_path}")

    output = args.output_dir.expanduser().resolve()
    index_path = output / "index.html"
    manifest_path = output / "media" / "manifest.json"

    if index_path.exists() and not args.force:
        raise SystemExit(f"refusing to overwrite existing file: {index_path}")

    width, height = ASPECTS[args.aspect]
    config = {
        "version": 2,
        "aspect": args.aspect,
        "background_mode": args.background_mode,
        "features": features,
        "title": args.title,
    }
    source = template_path.read_text(encoding="utf-8")
    replacements = {
        "{{DECK_TITLE_HTML}}": html.escape(args.title, quote=True),
        "{{DECK_SUBTITLE_HTML}}": html.escape(args.subtitle, quote=True),
        "{{DECK_LANG}}": html.escape(args.lang, quote=True),
        "{{BACKGROUND_MODE}}": args.background_mode,
        "{{DECK_TITLE_JSON}}": html_safe_json(args.title),
        "{{ACCENT_CSS}}": args.accent,
        "{{ACCENT_RGB}}": ", ".join(
            str(int(args.accent[index:index + 2], 16)) for index in (1, 3, 5)
        ),
        "{{ASPECT}}": args.aspect,
        "{{ASPECT_CSS}}": f"{width} / {height}",
        "{{ASPECT_WIDTH}}": str(width),
        "{{ASPECT_HEIGHT}}": str(height),
        "{{FEATURES_JSON}}": html_safe_json(features),
    }
    for placeholder, value in replacements.items():
        source = source.replace(placeholder, value)
    source = replace_deck_config(source, config)

    unresolved = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", source)))
    if unresolved:
        raise SystemExit(f"unresolved template placeholders: {', '.join(unresolved)}")

    output.mkdir(parents=True, exist_ok=True)
    index_path.write_text(source, encoding="utf-8")
    print(f"Created {index_path}")

    if "media" in features:
        manifest_created = False
        if not manifest_path.exists():
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest = {
                "version": 1,
                "items": [],
                "truth_states": ["VERIFIED", "PROPOSED", "SIMULATED", "UNKNOWN"],
            }
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            manifest_created = True
        print(f"{'Created' if manifest_created else 'Kept'} {manifest_path}")

    print(f"Aspect: {args.aspect}")
    print(f"Background mode: {args.background_mode}")
    print(f"Features: {', '.join(features) if features else 'core only'}")
    print("Next: replace every WOWDECK_PLACEHOLDER, then run validate_deck.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
