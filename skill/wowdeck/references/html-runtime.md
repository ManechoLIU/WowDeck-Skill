# HTML runtime contract

Use this reference when creating or changing the browser artifact. Runtime behavior follows the Strategy Note; it must not impose a narrative, visual style, aspect ratio, or delivery mode.

The initializer provides a structural starting point, not audience-ready content or a completed visual system. Keep its controller contracts, but replace its placeholder DOM and composition CSS (`.slide`, `.slide-content`, title/paragraph sizing and header/footer treatment) for the chosen scenes. A controller is reusable infrastructure; its starter geometry is not a theme. Implement the storyboard’s composition, assets, diagrams, and justified motion before acceptance; a valid configuration or working next-slide key is not proof of presentation quality.

## Package and configuration

Use a portable package with a single HTML entry point and relative local assets unless the delivery environment requires another structure. Do not depend on credentials, user-specific absolute paths, `file://` URLs, unpublished local services, or private source files.

Embed one machine-readable configuration block:

```html
<script id="deck-config" type="application/json">
{
  "version": 2,
  "title": "Presentation title",
  "aspect": "4:3",
  "background_mode": "light",
  "features": ["navigation"],
  "source_revision": "optional-content-revision",
  "builder_revision": "optional-builder-revision"
}
</script>
```

`aspect` accepts `16:9` or `4:3`; choose from the Strategy Note instead of assuming the starter's 16:9 default. If another geometry is essential, change and validate the runtime contract explicitly rather than inventing an unsupported value. In config version 2, `background_mode` is required, accepts `light` or `dark`, and declares the single canvas mode used by the whole deck; mirror it on `<html data-background-mode="...">`. Do not add per-slide inverse modes. Version 1 artifacts without this field remain compatibility inputs and receive a migration warning; do not use that compatibility path for newly generated decks. The starter defaults to `navigation`, but an empty feature list is valid for core-only output.

Only these optional feature names are valid:

- `navigation`
- `presenter`
- `media`
- `dialog`

Do not declare `motion`, `data`, `learning`, `print`, accessibility, or reduced motion as optional features. They are content concerns or baseline behavior. `source_revision` and `builder_revision` are optional provenance anchors when the project has stable identifiers; they do not replace file hashes. Artifact identity comes from the validator receipt described in [quality-gates.md](quality-gates.md).

For a reproducible deck, add `deck-dependencies.json` beside `index.html`:

```json
{
  "version": 1,
  "variant": "beginner-teaching",
  "source_revision": "content revision or hash",
  "builder_revision": "builder revision or hash",
  "files": [
    {"path": "content.json", "role": "authoring", "sha256": "..."},
    {"path": "build.py", "role": "builder", "sha256": "..."}
  ]
}
```

List every authoring input needed to reproduce the deck and every local runtime dependency referenced by HTML, CSS, or JavaScript. Use plain relative paths and current SHA256 values. The validator follows local CSS and detectable `fetch()`, Worker, and dynamic import references; an undeclared or changed dependency invalidates source-bound acceptance. A self-contained inline deck may be accepted only as `rendered-only`. A legacy final file with no reproducible source remains `artifact-only`.

Keep visible internal boundaries even when the rendered delivery is a single file:

1. content and source-linked data;
2. tokens, components, and layouts;
3. core rendering and accessibility behavior;
4. controllers for enabled optional features.

The canonical authoring package contains the structured content, configuration, approved assets, and the builder/runtime revision needed to reproduce the deck. The HTML artifact is the primary rendered delivery. Derived PDF, PPTX, and MP4 files must be regenerated from the same accepted source revision and bound to the rendered HTML artifact hash rather than edited as independent truth sources. If a legacy deck has no reproducible authoring package, mark it `artifact-only` and do not invent one.

## Core baseline

Every HTML presentation must provide:

- a stage containing `.slide` sections in stable reading order, with unique non-sensitive `id` and concise `data-title` values;
- a heading or accessible name for each presentation unit;
- the declared size/fit or responsive behavior;
- one declared `light` or `dark` background mode shared by every presentation unit;
- legible no-script and initial states appropriate to the delivery context;
- relative asset resolution and explicit fallbacks for unavailable assets;
- visible keyboard focus for interactive elements;
- meaningful alternative text and non-color status cues;
- print behavior when print or PDF is requested;
- `prefers-reduced-motion` behavior that preserves all meaning and reachability;
- no private notes, credentials, local paths, or unapproved source material in client-visible code.

Core-only output with `features: []` is valid for a single presentation unit. A one-screen-at-a-time deck with multiple `.slide` units must enable `navigation`. If the task instead needs an all-units document reading mode, implement and validate that mode explicitly rather than treating it as an undeclared core behavior.

## `navigation`

Enable `navigation` only when controlled movement, direct entry, or presentation controls improve the delivery. Provide at least one visible control and a keyboard path. Add hashes, an agenda, progress, or counters only when the context needs them.

When one unit is shown at a time, the active index, visible unit, URL state, counter, progress, selection, and presenter state that exist must agree. A navigation transaction should:

1. resolve and clamp the target;
2. close temporary overlays;
3. pause media that is leaving the active unit;
4. update active/inactive and accessible states;
5. synchronize every enabled navigation surface;
6. restore a meaningful focus target when keyboard navigation initiated the change.

Inactive units should be both hidden from assistive technology and non-interactive when they are visually hidden. Never rely on an animation finishing before the destination becomes usable. Keyboard navigation should focus the newly active slide; pointer controls and hash-driven navigation should not actively move focus away from the user's current control or context.

Expose the active state through `window.WowDeck.show()`. When `navigation` is enabled, expose `next()` and `previous()` as well. Keep pointer controls and the documented keyboard path behaviorally equivalent.

## `presenter`

Enable `presenter` for shareable speaker notes, planned timing, or speaker controls. Notes and timing are not required otherwise.

- The canonical source for presenter notes is exactly one hidden `<aside data-notes data-duration="SECONDS" hidden>...</aside>` inside each `.slide`. `data-duration` is that slide's optional non-negative planned duration in whole seconds. Do not duplicate notes in a detached JSON block or maintain a second notes array.
- When `presenter` is enabled, every slide must have a non-empty canonical note. Missing or whitespace-only notes do not make presenter controls available; omit the feature instead of presenting an unusable notes or timer UI.
- Keep the notes panel synchronized from the active slide's canonical `aside`. Navigation changes the displayed note and planned duration in the same transaction as the active slide.
- Elapsed time remains at `00:00` on page load. Start it only from the explicit **Start** control, change that control to **Pause** while running, and to **Resume** while paused.
- Runtime-facing presenter labels use concise Chinese copy when the document `lang` begins with `zh`; all other languages fall back to English. This includes controls, notes, planned time, and timer actions without requiring a general i18n framework.
- Keep notes, private research, and operational secrets separate; all HTML source is client-visible.
- Pause or lower conflicting media when presenter UI obscures or competes with it.
- Make presentation controls usable without changing the audience-visible content state unexpectedly.

Canonical slide example:

```html
<section class="slide" id="slide-2" data-title="Evidence" tabindex="-1">
  <!-- audience-visible slide content -->
  <aside data-notes data-duration="45" hidden>
    Explain the qualification before showing the comparison.
  </aside>
</section>
```

## `media`

Enable `media` for timed audio or video. Ordinary images, diagrams, and charts do not require this feature.

For every media item, use a versioned manifest entry with `key`, `kind` (`video` or `audio`), relative `src`, truth status, shareable `source`, `duration_seconds`, and `preparation`. Video also records `poster`, width, height, video codec, pixel format, and audio codec when present. Audio records its audio codec and does not need a fabricated poster. Captions or a transcript are required when speech carries essential meaning.

Use `[data-media-shell]` for the integrated item, `[data-media-fallback]` for its static or failure representation, and `[data-media-status]` for a readable state. Expose `window.WowDeck.pauseMedia()` when `media` is enabled.

Controller invariants:

- autoplay begins muted and is never required to reveal essential content;
- rejected autoplay exposes a manual action;
- leaving a unit, hiding the document, or opening a blocking overlay pauses playback;
- stale timers cannot start media after navigation;
- no more than the intended number of streams plays at once;
- play, pause, ended, replay, loading, and error states are understandable;
- print and reduced-motion paths use an intentional static fallback.

Follow the media stages in [quality-gates.md](quality-gates.md). Technical metadata or file existence alone does not prove playback.

## `dialog`

Enable `dialog` only when layered reading is useful and the same information should not occupy the primary route.

- Use native `<dialog data-dialog="id">` where appropriate or equivalent dialog semantics. Connect controls through `data-open-dialog="id"`, `data-close-dialog`, and expose `window.WowDeck.openDialog()` / `closeDialog()` when enabled.
- Provide an accessible name, focus entry, Tab/Shift+Tab containment, Escape and explicit close behavior.
- Inert the background while open and restore focus to the trigger on close.
- Insert untrusted text with `textContent` or safe element creation, not `innerHTML`.
- Provide a print/export representation for material that must survive outside the interactive HTML.

Do not hide essential qualifications or the only version of required content inside an undiscoverable dialog.

## Progressive enhancement and compatibility

Treat fullscreen APIs, advanced color functions, backdrop filters, view transitions, and autoplay as enhancements. Provide readable fallbacks. Avoid shipping a framework or remote dependency merely to implement a small controller.

Test the browsers, viewers, viewports, input methods, and network assumptions recorded in the Strategy Note. A parsed DOM, local HTTP `200`, or passing structural validator is not browser acceptance.
