#!/usr/bin/env python3
"""Render the binary-search teaching fixture from its canonical JSON source."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CONTENT_PATH = ROOT / "content.json"
OUTPUT_PATH = ROOT / "index.html"
DEPENDENCY_PATH = ROOT / "deck-dependencies.json"


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_for_script(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def number_strip(
    numbers: list[int],
    *,
    label: str,
    mid_index: int | None = None,
    mid_label: str = "当前中间",
    past_indices: list[int] | None = None,
    discarded_indices: list[int] | None = None,
    candidate_indices: list[int] | None = None,
    found: bool = False,
) -> str:
    past = set(past_indices or [])
    discarded = set(discarded_indices or [])
    candidates = set(candidate_indices or [])
    cells: list[str] = []
    for index, value in enumerate(numbers):
        classes = ["number-cell"]
        statuses: list[str] = []
        if index in past:
            classes.append("is-past")
            statuses.append("此前已排除")
        if index in discarded:
            classes.append("is-discarded")
            statuses.append("本轮排除")
        if index in candidates:
            classes.append("is-candidate")
            statuses.append("仍是候选")
        marker = ""
        if index == mid_index:
            classes.append("is-found" if found else "is-mid")
            marker_text = "找到" if found else mid_label
            marker = f'<span class="cell-marker" aria-hidden="true">{escape(marker_text)}</span>'
            statuses.append("目标值" if found else "当前中间数")
        status_text = "，".join(statuses) if statuses else "数字"
        cells.append(
            f'<li class="{" ".join(classes)}" aria-label="{escape(value)}，{escape(status_text)}">'
            f'{marker}<strong>{escape(value)}</strong></li>'
        )
    return (
        f'<div class="number-board" aria-label="{escape(label)}">'
        f'<ul class="number-strip">{"".join(cells)}</ul>'
        '<div class="strip-legend" aria-hidden="true">'
        '<span><i class="legend-dot candidate"></i>仍可能</span>'
        '<span><i class="legend-dot middle"></i>当前中间</span>'
        '<span><i class="legend-dot discarded"></i>已排除</span>'
        '</div></div>'
    )


def title_block(slide: dict[str, Any]) -> str:
    return (
        f'<div class="title-block reveal" style="--delay:60ms">'
        f'<p class="eyebrow">{escape(slide["eyebrow"])}</p>'
        f'<h1 id="heading-{escape(slide["id"])}" tabindex="-1">{escape(slide["title"])}</h1>'
        '</div>'
    )


def render_intro(slide: dict[str, Any], numbers: list[int]) -> str:
    return (
        '<div class="intro-layout">'
        f'<div>{title_block(slide)}'
        f'<p class="lead reveal" style="--delay:120ms">{escape(slide["lead"])}</p></div>'
        '<div class="target-card reveal" style="--delay:180ms">'
        '<span>要找的数字</span>'
        f'<strong>{escape(slide["target"])}</strong>'
        f'<p>{escape(slide["focus_text"])}</p>'
        '</div></div>'
        f'<div class="reveal" style="--delay:220ms">{number_strip(numbers, label="升序数字列表，先看中间数", mid_index=slide["mid_index"], mid_label=slide["mid_label"])}</div>'
        f'<p class="takeaway reveal" style="--delay:280ms">{escape(slide["takeaway"])}</p>'
    )


def render_rule(slide: dict[str, Any], numbers: list[int]) -> str:
    logic = "".join(
        '<li class="logic-step reveal" style="--delay:{delay}ms">'
        '<span class="logic-mark">{mark}</span>'
        '<div><strong>{label}</strong><p>{text}</p></div></li>'.format(
            delay=180 + index * 70,
            mark=escape(item["mark"]),
            label=escape(item["label"]),
            text=escape(item["text"]),
        )
        for index, item in enumerate(slide["logic"])
    )
    return (
        f'{title_block(slide)}'
        f'<p class="premise reveal" style="--delay:120ms"><span>前提</span>{escape(slide["premise"])}</p>'
        f'<div class="compact-strip reveal" style="--delay:150ms">{number_strip(numbers, label="有序数字列，中间数为 29", mid_index=slide["mid_index"], mid_label="中间 29")}</div>'
        f'<ol class="logic-chain">{logic}</ol>'
        f'<p class="boundary reveal" style="--delay:420ms"><strong>边界：</strong>{escape(slide["boundary"])}</p>'
    )


def render_step(slide: dict[str, Any], numbers: list[int], *, found: bool = False) -> str:
    strip = number_strip(
        numbers,
        label=f'{slide["title"]}后的数字状态',
        mid_index=slide["mid_index"],
        past_indices=slide.get("past_indices"),
        discarded_indices=slide.get("discarded_indices"),
        candidate_indices=slide.get("candidate_indices"),
        found=found,
    )
    if found:
        detail = (
            '<div class="summary-grid reveal" style="--delay:260ms">'
            f'<p><span>比较路径</span><strong>{escape(slide["trail"])}</strong></p>'
            f'<p><span>范围变化</span><strong>{escape(slide["shrink"])}</strong></p>'
            '</div>'
            f'<p class="nuance reveal" style="--delay:330ms">{escape(slide["nuance"])}</p>'
        )
    else:
        detail = (
            '<div class="reason-grid reveal" style="--delay:260ms">'
            f'<p><span>为什么</span>{escape(slide["reason"])}</p>'
            f'<p><span>怎么做</span><strong>{escape(slide["action"])}</strong></p>'
            f'<p><span>结果</span><strong>{escape(slide["remaining"])}</strong></p>'
            '</div>'
        )
    return (
        '<div class="step-heading">'
        f'{title_block(slide)}'
        f'<div class="comparison reveal" style="--delay:120ms" aria-label="比较结果 {escape(slide["comparison"])}">{escape(slide["comparison"])}</div>'
        '</div>'
        f'<div class="reveal" style="--delay:190ms">{strip}</div>'
        f'{detail}'
    )


def render_practice(slide: dict[str, Any], numbers: list[int]) -> str:
    instructions = "".join(
        f'<li><span>{index}</span>{escape(text)}</li>'
        for index, text in enumerate(slide["instructions"], start=1)
    )
    return (
        '<div class="practice-heading">'
        f'{title_block(slide)}'
        f'<div class="practice-target reveal" style="--delay:120ms"><span>目标</span><strong>{escape(slide["target"])}</strong></div>'
        '</div>'
        f'<div class="reveal" style="--delay:170ms">{number_strip(numbers, label="手算练习的升序数字列", mid_index=slide["mid_index"], mid_label=slide["mid_label"])}</div>'
        f'<ol class="practice-steps reveal" style="--delay:230ms">{instructions}</ol>'
        f'<p class="pause-note reveal" style="--delay:300ms">{escape(slide["pause_note"])}</p>'
    )


def render_answer(slide: dict[str, Any], numbers: list[int]) -> str:
    trail = "".join(
        '<li class="trail-card"><strong>{value}</strong><span>{comparison}</span><em>{move}</em></li>'.format(
            value=escape(item["value"]),
            comparison=escape(item["comparison"]),
            move=escape(item["move"]),
        )
        for item in slide["trail"]
    )
    recipe = "".join(
        f'<li><span>{index}</span>{escape(item)}</li>'
        for index, item in enumerate(slide["recipe"], start=1)
    )
    return (
        f'{title_block(slide)}'
        f'<ol class="trail reveal" style="--delay:120ms">{trail}</ol>'
        f'<div class="answer-strip reveal" style="--delay:190ms">{number_strip(numbers, label="找到 58 后的最终状态", mid_index=slide["mid_index"], past_indices=slide["past_indices"], candidate_indices=slide["candidate_indices"], found=True)}</div>'
        f'<ol class="recipe reveal" style="--delay:250ms">{recipe}</ol>'
        f'<p class="closing reveal" style="--delay:320ms">{escape(slide["closing"])}</p>'
    )


RENDERERS = {
    "intro": render_intro,
    "rule": render_rule,
    "step": render_step,
    "found": lambda slide, numbers: render_step(slide, numbers, found=True),
    "practice": render_practice,
    "answer": render_answer,
}


def render_slide(
    slide: dict[str, Any], numbers: list[int], series_label: str, index: int, total: int
) -> str:
    renderer = RENDERERS.get(slide["kind"])
    if renderer is None:
        raise ValueError(f'unsupported slide kind: {slide["kind"]}')
    active = index == 0
    state_attrs = 'aria-hidden="false"' if active else 'aria-hidden="true" inert'
    state_class = "slide is-active" if active else "slide"
    body = renderer(slide, numbers)
    return f'''<section class="{state_class}" id="{escape(slide["id"])}" data-title="{escape(slide["data_title"])}" aria-labelledby="heading-{escape(slide["id"])}" {state_attrs}>
      <header class="slide-header">
        <span>{escape(series_label)}</span>
        <span>{index + 1:02d} / {total:02d}</span>
      </header>
      <main class="slide-main {escape(slide["kind"])}-slide">
        {body}
      </main>
      <footer class="slide-footer">
        <span class="role-label">{escape(slide["role"])}</span>
        <span>{escape(slide["footer"])}</span>
      </footer>
    </section>'''


def render_document(content: dict[str, Any]) -> str:
    lesson = content["lesson"]
    slides_data = lesson["slides"]
    if not 5 <= len(slides_data) <= 7:
        raise ValueError("this forward fixture must contain 5–7 slides")
    if content["features"] != ["navigation"]:
        raise ValueError("this forward fixture enables navigation only")
    slide_ids = [slide["id"] for slide in slides_data]
    if len(slide_ids) != len(set(slide_ids)):
        raise ValueError("slide ids must be unique")

    config = {
        "version": 1,
        "title": content["title"],
        "aspect": content["aspect"],
        "features": content["features"],
        "source_revision": sha256(CONTENT_PATH),
        "builder_revision": sha256(Path(__file__)),
    }
    slides = "\n".join(
        render_slide(
            slide,
            lesson["numbers"],
            lesson["series_label"],
            index,
            len(slides_data),
        )
        for index, slide in enumerate(slides_data)
    )
    document = HTML_TEMPLATE
    replacements = {
        "@@LANG@@": escape(content["lang"]),
        "@@TITLE@@": escape(content["title"]),
        "@@SUBTITLE@@": escape(content["subtitle"]),
        "@@CONFIG@@": json_for_script(config),
        "@@SLIDES@@": slides,
        "@@TOTAL@@": str(len(slides_data)),
    }
    for token, value in replacements.items():
        document = document.replace(token, value)
    unresolved = [token for token in replacements if token in document]
    if unresolved:
        raise ValueError(f"unresolved template tokens: {unresolved}")
    return document


def write_dependency_manifest(content: dict[str, Any]) -> dict[str, Any]:
    source_revision = sha256(CONTENT_PATH)
    builder_revision = sha256(Path(__file__))
    manifest = {
        "version": 1,
        "variant": content["variant"],
        "source_revision": source_revision,
        "builder_revision": builder_revision,
        "files": [
            {
                "path": CONTENT_PATH.name,
                "role": "authoring",
                "sha256": source_revision,
            },
            {
                "path": Path(__file__).name,
                "role": "runtime",
                "sha256": builder_revision,
            },
        ],
    }
    DEPENDENCY_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


HTML_TEMPLATE = r'''<!doctype html>
<html lang="@@LANG@@" data-aspect="16:9">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta name="description" content="@@SUBTITLE@@">
  <link rel="icon" href="data:,">
  <title>@@TITLE@@</title>
  <script id="deck-config" type="application/json">@@CONFIG@@</script>
  <style>
    :root {
      --stage-width: 1600px;
      --stage-height: 900px;
      --stage-scale: 1;
      --stage-shell-width: var(--stage-width);
      --stage-shell-height: var(--stage-height);
      --paper: #f8f4e9;
      --paper-deep: #eee7d6;
      --ink: #182b31;
      --muted: #56676c;
      --line: #c9c4b7;
      --accent: #b84a2b;
      --accent-soft: #f4d5c7;
      --candidate: #0f5962;
      --candidate-soft: #dcebed;
      --found: #21694f;
      --found-soft: #d8eadf;
      --discarded: #747b7c;
      --charcoal: #14252a;
      --focus: #075fb4;
      --ease: cubic-bezier(.22, .72, .24, 1);
    }

    *, *::before, *::after { box-sizing: border-box; }

    html, body {
      width: 100%;
      height: 100%;
      margin: 0;
      overflow: hidden;
    }

    body {
      color: var(--ink);
      background:
        radial-gradient(circle at 16% 14%, rgb(241 196 156 / 14%), transparent 30%),
        #15262b;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }

    button, output { font: inherit; }

    button:focus-visible,
    [tabindex]:focus-visible {
      outline: 4px solid var(--focus);
      outline-offset: 5px;
    }

    #deck-viewport {
      position: fixed;
      inset: 0;
      display: grid;
      place-items: center;
      overflow: hidden;
      padding: 24px 24px 88px;
    }

    #stage-shell {
      position: relative;
      width: var(--stage-shell-width);
      height: var(--stage-shell-height);
    }

    #stage {
      position: absolute;
      inset: 0 auto auto 0;
      width: var(--stage-width);
      height: var(--stage-height);
      overflow: hidden;
      color: var(--ink);
      background:
        linear-gradient(90deg, rgb(24 43 49 / 3%) 1px, transparent 1px),
        linear-gradient(rgb(24 43 49 / 3%) 1px, transparent 1px),
        var(--paper);
      background-size: 40px 40px;
      box-shadow: 0 32px 100px rgb(0 0 0 / 38%);
      transform: scale(var(--stage-scale));
      transform-origin: top left;
    }

    .slide {
      position: absolute;
      inset: 0;
      display: grid;
      grid-template-rows: 44px minmax(0, 1fr) 42px;
      gap: 22px;
      padding: 44px 64px 38px;
      visibility: hidden;
      opacity: 0;
      transform: translateX(14px);
      pointer-events: none;
    }

    :root[data-ready="true"] .slide {
      transition: opacity 220ms var(--ease), transform 220ms var(--ease);
    }

    .slide.is-active {
      z-index: 1;
      visibility: visible;
      opacity: 1;
      transform: none;
      pointer-events: auto;
      transition-delay: 0s;
    }

    .slide-header,
    .slide-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 30px;
      color: var(--muted);
      font-size: 18px;
      letter-spacing: .04em;
    }

    .slide-header {
      border-bottom: 1px solid var(--line);
      font-weight: 700;
    }

    .slide-footer {
      border-top: 1px solid var(--line);
      font-size: 17px;
    }

    .slide-footer > :last-child {
      overflow: hidden;
      max-width: 1050px;
      white-space: nowrap;
      text-overflow: ellipsis;
    }

    .role-label {
      flex: none;
      color: var(--accent);
      font-weight: 800;
    }

    .slide-main {
      min-width: 0;
      min-height: 0;
      display: grid;
      align-content: center;
      gap: 22px;
    }

    h1, p { margin: 0; }

    .title-block h1 {
      max-width: 1220px;
      margin-top: 9px;
      font-size: 64px;
      line-height: 1.06;
      letter-spacing: -.035em;
      text-wrap: balance;
    }

    .eyebrow {
      color: var(--accent);
      font-size: 19px;
      font-weight: 850;
      letter-spacing: .12em;
    }

    .lead {
      max-width: 930px;
      margin-top: 20px;
      color: var(--muted);
      font-size: 29px;
      line-height: 1.48;
    }

    .intro-layout,
    .step-heading,
    .practice-heading {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: end;
      gap: 42px;
    }

    .target-card,
    .practice-target {
      width: 260px;
      padding: 24px 28px;
      border: 2px solid var(--accent);
      border-radius: 20px;
      background: var(--accent-soft);
    }

    .target-card span,
    .practice-target span {
      display: block;
      color: var(--accent);
      font-size: 17px;
      font-weight: 850;
      letter-spacing: .08em;
    }

    .target-card strong,
    .practice-target strong {
      display: block;
      margin: 3px 0;
      font-size: 82px;
      line-height: 1;
      font-variant-numeric: tabular-nums;
    }

    .target-card p { color: var(--muted); font-size: 20px; }

    .number-board { width: 100%; }

    .number-strip {
      display: grid;
      grid-template-columns: repeat(15, minmax(0, 1fr));
      gap: 8px;
      margin: 0;
      padding: 22px 0 0;
      list-style: none;
    }

    .number-cell {
      position: relative;
      display: grid;
      place-items: center;
      min-width: 0;
      height: 76px;
      border: 2px solid #8e999b;
      border-radius: 12px;
      color: var(--candidate);
      background: rgb(255 255 255 / 62%);
      font-size: 30px;
      font-variant-numeric: tabular-nums;
    }

    .number-cell strong { position: relative; z-index: 1; }

    .number-cell.is-candidate {
      border-color: var(--candidate);
      background: var(--candidate-soft);
    }

    .number-cell.is-past,
    .number-cell.is-discarded {
      overflow: hidden;
      color: var(--discarded);
      border-color: #a4aaa9;
      background: #e6e2d8;
    }

    .number-cell.is-past { opacity: .52; }

    .number-cell.is-past::after,
    .number-cell.is-discarded::after {
      content: "";
      position: absolute;
      inset: 50% -8px auto;
      height: 3px;
      background: #7a8180;
      transform: rotate(-22deg);
      transform-origin: center;
    }

    .number-cell.is-mid {
      opacity: 1;
      border: 4px solid var(--accent);
      color: var(--ink);
      background: var(--accent-soft);
      box-shadow: 0 0 0 4px rgb(184 74 43 / 14%);
    }

    .number-cell.is-found {
      opacity: 1;
      border: 4px solid var(--found);
      color: #fff;
      background: var(--found);
      box-shadow: 0 0 0 5px rgb(33 105 79 / 15%);
    }

    .number-cell.is-found::after { display: none; }

    .cell-marker {
      position: absolute;
      inset: -25px 50% auto auto;
      z-index: 2;
      width: max-content;
      max-width: 108px;
      padding: 3px 7px;
      border-radius: 6px;
      color: #fff;
      background: var(--accent);
      font-size: 13px;
      font-weight: 850;
      line-height: 1.1;
      transform: translateX(50%);
    }

    .is-found .cell-marker { background: var(--found); }

    .strip-legend {
      display: flex;
      justify-content: flex-end;
      gap: 22px;
      margin-top: 12px;
      color: var(--muted);
      font-size: 15px;
    }

    .strip-legend span { display: flex; align-items: center; gap: 7px; }

    .legend-dot {
      width: 13px;
      height: 13px;
      border-radius: 4px;
      border: 2px solid currentColor;
    }

    .legend-dot.candidate { color: var(--candidate); background: var(--candidate-soft); }
    .legend-dot.middle { color: var(--accent); background: var(--accent-soft); }
    .legend-dot.discarded {
      color: var(--discarded);
      background: linear-gradient(-30deg, transparent 42%, currentColor 43% 57%, transparent 58%);
    }

    .takeaway,
    .boundary,
    .pause-note,
    .nuance,
    .closing {
      padding: 16px 20px;
      border-left: 6px solid var(--accent);
      border-radius: 0 12px 12px 0;
      background: rgb(255 255 255 / 62%);
      font-size: 23px;
      line-height: 1.4;
    }

    .premise {
      display: flex;
      align-items: center;
      gap: 16px;
      font-size: 25px;
      font-weight: 750;
    }

    .premise span {
      padding: 6px 11px;
      border-radius: 999px;
      color: #fff;
      background: var(--candidate);
      font-size: 16px;
    }

    .compact-strip .number-strip { padding-top: 18px; }
    .compact-strip .number-cell { height: 58px; font-size: 25px; }
    .compact-strip .strip-legend { display: none; }

    .logic-chain {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .logic-step {
      display: grid;
      grid-template-columns: 74px 1fr;
      align-items: center;
      min-width: 0;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: rgb(255 255 255 / 64%);
    }

    .logic-mark {
      color: var(--accent);
      font-size: 52px;
      font-weight: 900;
    }

    .logic-step strong { font-size: 21px; }
    .logic-step p { margin-top: 6px; color: var(--muted); font-size: 20px; line-height: 1.35; }

    .boundary { border-left-color: var(--candidate); font-size: 20px; }

    .comparison {
      min-width: 250px;
      padding: 18px 24px;
      border-radius: 18px;
      color: #fff;
      background: var(--charcoal);
      font-size: 47px;
      font-weight: 900;
      text-align: center;
      font-variant-numeric: tabular-nums;
    }

    .reason-grid,
    .summary-grid {
      display: grid;
      grid-template-columns: 1.55fr .8fr .7fr;
      gap: 14px;
    }

    .reason-grid p,
    .summary-grid p {
      min-width: 0;
      padding: 18px 20px;
      border: 1px solid var(--line);
      border-radius: 15px;
      background: rgb(255 255 255 / 62%);
      font-size: 20px;
      line-height: 1.38;
    }

    .reason-grid span,
    .summary-grid span {
      display: block;
      margin-bottom: 7px;
      color: var(--accent);
      font-size: 15px;
      font-weight: 850;
      letter-spacing: .08em;
    }

    .reason-grid strong,
    .summary-grid strong { font-size: 23px; }

    .summary-grid { grid-template-columns: 1fr 1fr; }
    .nuance { border-left-color: var(--candidate); font-size: 20px; }

    .practice-target { width: 220px; padding-block: 18px; }
    .practice-target strong { font-size: 66px; }

    .practice-steps,
    .recipe {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .practice-steps li,
    .recipe li {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: rgb(255 255 255 / 62%);
      font-size: 19px;
      font-weight: 700;
      line-height: 1.3;
    }

    .practice-steps li span,
    .recipe li span {
      display: grid;
      flex: none;
      width: 34px;
      height: 34px;
      place-items: center;
      border-radius: 50%;
      color: #fff;
      background: var(--candidate);
      font-weight: 900;
    }

    .pause-note { border-left-color: var(--candidate); font-weight: 750; }

    .answer-slide .title-block h1 { font-size: 55px; }

    .trail {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .trail-card {
      display: grid;
      grid-template-columns: auto 1fr auto;
      align-items: center;
      gap: 16px;
      padding: 13px 18px;
      border-radius: 15px;
      color: var(--ink);
      background: var(--paper-deep);
    }

    .trail-card strong { color: var(--accent); font-size: 38px; }
    .trail-card span { font-size: 21px; font-weight: 800; text-align: center; }
    .trail-card em { color: var(--candidate); font-size: 17px; font-style: normal; font-weight: 800; }

    .answer-strip .number-strip { padding-top: 20px; }
    .answer-strip .number-cell { height: 60px; font-size: 24px; }
    .answer-strip .strip-legend { display: none; }
    .recipe li { padding-block: 11px; font-size: 17px; }
    .recipe li span { width: 30px; height: 30px; }
    .closing { border-left-color: var(--found); font-size: 21px; font-weight: 750; }

    .reveal { opacity: 0; transform: translateY(9px); }

    .slide.is-active .reveal {
      animation: reveal-in 360ms var(--ease) both;
      animation-delay: var(--delay, 0ms);
    }

    @keyframes reveal-in {
      to { opacity: 1; transform: none; }
    }

    .controls {
      position: fixed;
      inset: auto 18px 18px;
      z-index: 10;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      color: #edf4f3;
    }

    .controls button {
      min-width: 112px;
      min-height: 48px;
      padding: 10px 18px;
      border: 1px solid rgb(255 255 255 / 26%);
      border-radius: 999px;
      color: inherit;
      background: #20383f;
      cursor: pointer;
      font-weight: 800;
    }

    .controls button:hover:not(:disabled) { background: #2a4a53; }
    .controls button:disabled { opacity: .38; cursor: default; }

    .counter {
      min-width: 92px;
      text-align: center;
      font-variant-numeric: tabular-nums;
      font-weight: 800;
    }

    .key-hint {
      position: fixed;
      right: 24px;
      bottom: 31px;
      color: #b7c7c8;
      font-size: 14px;
    }

    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        scroll-behavior: auto !important;
        animation-duration: .001ms !important;
        animation-delay: 0ms !important;
        transition-duration: .001ms !important;
      }

      .reveal { opacity: 1; transform: none; animation: none !important; }
    }

    @media print {
      @page { size: 16.6667in 9.375in; margin: 0; }

      html, body {
        width: auto;
        height: auto;
        overflow: visible;
        background: #fff;
      }

      #deck-viewport {
        position: static;
        display: block;
        padding: 0;
        overflow: visible;
      }

      #stage-shell,
      #stage {
        position: static;
        width: 1600px;
        height: auto;
        transform: none;
        box-shadow: none;
        overflow: visible;
      }

      .slide,
      .slide.is-active {
        position: relative;
        width: 1600px;
        height: 900px;
        visibility: visible;
        opacity: 1;
        transform: none;
        pointer-events: auto;
        break-after: page;
        page-break-after: always;
      }

      .slide:last-child { break-after: auto; page-break-after: auto; }
      .reveal { opacity: 1; transform: none; animation: none !important; }
      .controls, .key-hint { display: none !important; }
    }
  </style>
</head>
<body>
  <div id="deck-viewport">
    <div id="stage-shell">
      <div id="stage" role="region" aria-roledescription="幻灯片" aria-label="@@TITLE@@">
        @@SLIDES@@
      </div>
    </div>
  </div>

  <nav class="controls" aria-label="页面导航">
    <button type="button" id="previous-slide" aria-label="上一页">← 上一页</button>
    <output class="counter" id="slide-counter" aria-live="polite">1 / @@TOTAL@@</output>
    <button type="button" id="next-slide" aria-label="下一页">下一页 →</button>
  </nav>
  <p class="key-hint" aria-hidden="true">← → / 空格</p>
  <p class="sr-only" id="navigation-help">使用左右方向键、Page Up、Page Down、Home、End 或空格翻页。</p>
  <noscript><p class="sr-only">此演示需要 JavaScript 以启用翻页；当前仍可阅读第一页。</p></noscript>

  <script>
    (() => {
      'use strict';

      const root = document.documentElement;
      const viewport = document.getElementById('deck-viewport');
      const stage = document.getElementById('stage');
      const slides = Array.from(stage.querySelectorAll('.slide'));
      const previousButton = document.getElementById('previous-slide');
      const nextButton = document.getElementById('next-slide');
      const counter = document.getElementById('slide-counter');
      const config = JSON.parse(document.getElementById('deck-config').textContent);
      let activeIndex = 0;

      root.dataset.aspect = config.aspect;
      root.dataset.features = config.features.join(' ');

      function fitStage() {
        const availableWidth = Math.max(1, viewport.clientWidth - 48);
        const availableHeight = Math.max(1, viewport.clientHeight - 112);
        const scale = Math.min(availableWidth / 1600, availableHeight / 900, 1);
        root.style.setProperty('--stage-scale', String(scale));
        root.style.setProperty('--stage-shell-width', `${1600 * scale}px`);
        root.style.setProperty('--stage-shell-height', `${900 * scale}px`);
      }

      function resolveIndex(target) {
        if (Number.isInteger(target)) return Math.max(0, Math.min(slides.length - 1, target));
        if (typeof target !== 'string') return activeIndex;
        const token = target.replace(/^#/, '');
        if (/^\d+$/.test(token)) {
          const number = Number.parseInt(token, 10) - 1;
          return number >= 0 && number < slides.length ? number : activeIndex;
        }
        const byId = slides.findIndex((slide) => slide.id === token);
        return byId >= 0 ? byId : activeIndex;
      }

      function hashIndex() {
        if (!location.hash) return 0;
        let token = location.hash.slice(1);
        try { token = decodeURIComponent(token); } catch (_error) { return 0; }
        return resolveIndex(token);
      }

      function show(target, options = {}) {
        const nextIndex = resolveIndex(target);
        const focusHeading = options.focus === true;
        const updateHash = options.updateHash !== false;
        activeIndex = nextIndex;

        slides.forEach((slide, index) => {
          const active = index === activeIndex;
          slide.classList.toggle('is-active', active);
          slide.setAttribute('aria-hidden', active ? 'false' : 'true');
          if (active) slide.removeAttribute('inert');
          else slide.setAttribute('inert', '');
        });

        counter.textContent = `${activeIndex + 1} / ${slides.length}`;
        previousButton.disabled = activeIndex === 0;
        nextButton.disabled = activeIndex === slides.length - 1;
        const activeSlide = slides[activeIndex];
        document.title = `${activeSlide.dataset.title} · ${config.title}`;

        if (updateHash) {
          const nextHash = `#${encodeURIComponent(activeSlide.id)}`;
          if (location.hash !== nextHash) history.replaceState(null, '', nextHash);
        }
        if (focusHeading) {
          const heading = activeSlide.querySelector('h1, h2');
          requestAnimationFrame(() => heading?.focus({ preventScroll: true }));
        }
        return activeIndex;
      }

      function move(delta, focus = false) {
        return show(activeIndex + delta, { focus });
      }

      previousButton.addEventListener('click', () => move(-1));
      nextButton.addEventListener('click', () => move(1));

      document.addEventListener('keydown', (event) => {
        if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey) return;
        if (event.target instanceof HTMLElement && event.target.closest('button, input, textarea, select, a[href]')) return;
        let target = null;
        if (event.key === 'ArrowRight' || event.key === 'PageDown' || event.key === ' ') target = activeIndex + 1;
        if (event.key === 'ArrowLeft' || event.key === 'PageUp') target = activeIndex - 1;
        if (event.key === 'Home') target = 0;
        if (event.key === 'End') target = slides.length - 1;
        if (target === null) return;
        event.preventDefault();
        show(target, { focus: true });
      });

      window.addEventListener('hashchange', () => show(hashIndex(), { updateHash: false }));
      window.addEventListener('resize', fitStage, { passive: true });

      window.WowDeck = Object.freeze({
        show: (target) => show(target),
        next: () => move(1),
        previous: () => move(-1),
      });

      fitStage();
      show(hashIndex());
      requestAnimationFrame(() => { root.dataset.ready = 'true'; });
      document.fonts?.ready.then(fitStage);
    })();
  </script>
</body>
</html>
'''


def main() -> int:
    content = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    manifest = write_dependency_manifest(content)
    output = render_document(content)
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    print(f"Built {OUTPUT_PATH.name} from {CONTENT_PATH.name}")
    print(f"Dependencies: {DEPENDENCY_PATH.name} ({manifest['variant']})")
    print(f"Slides: {len(content['lesson']['slides'])}")
    print(f"Index SHA256: {sha256(OUTPUT_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
