# Quality gates and delivery acceptance

Use these gates before calling a presentation or any derivative complete. Run only the gates that apply, but never replace format-specific acceptance with file existence, a successful command, or acceptance of another format.

## Gate 1 — Strategy and content logic

- The five-part Strategy Note exists and matches the current request.
- Audience, context, desired shift, and communication job are consistent with the artifact.
- Sequence is a justified route through the content dependency graph, not an inherited page template.
- Terminology, examples, depth, density, self-containedness, and ending match the intended audience and sharing context.
- Each unit has a clear role and focus; it does not need to be a sales claim or conclusion.
- Optional features and requested deliverables are justified by delivery constraints.

## Gate 2 — Truth, evidence, rights, and privacy

- Decision- or understanding-changing claims retain source, scope, date, status, and uncertainty at the prominence their risk requires.
- Fact, interpretation, proposal, simulation, generated material, and unknown are not conflated.
- Quotes, metrics, interfaces, outcomes, and behavior are not fabricated or upgraded beyond current evidence.
- Asset provenance, rights, and sharing scope are known for the intended audience.
- The distributable set contains no credentials, raw private material, internal Strategy Note, local absolute paths, unnecessary drafts, or hidden publication dependencies.

Failure on a material claim, rights boundary, or privacy boundary is blocking.

## Gate 3 — Single source of truth and artifact identity

Maintain one canonical authoring package: structured content, configuration, approved assets, and the builder/runtime revision needed to reproduce the audience-visible result. HTML is the primary rendered artifact; PDF, PPTX, MP4, screenshots, and public deployments are further derived outputs. Do not repair any rendered output independently without reconciling the canonical source. When a legacy deck has only a final HTML file, label it `artifact-only` and preserve that limitation.

Bind every requested output with:

- the validator receipt's `artifact_sha256`, computed from the rendered HTML, referenced runtime assets, dependency closure, and declared source identity;
- the receipt's `index_sha256`, `manifest_sha256` when media exists, slide count, and declared feature set;
- optional `source_revision` and `builder_revision` provenance anchors when the authoring package provides them;
- `source_sha256`, `variant`, dependency-manifest hash, and dependency-file hashes for source-bound decks;
- output kind, path or URL, generation time, and content hash where a file exists;
- the acceptance evidence actually obtained for that exact output.

Use the validator receipt plus an embedded or sidecar delivery record as the binding evidence. Regenerate the receipt after any canonical HTML or referenced-asset change; use receipt checking to reject stale evidence. A Git commit may supplement identity only when it fully represents the delivered source, but it does not replace the artifact hash.

Bind each derivative by its own exact path or URL and hash together with the source `artifact_sha256`. A file with a stale or missing binding is not the same accepted artifact merely because its title looks right.

## Gate 4 — Visual, accessibility, and reduced motion

- Visual choices derive from the Strategy Note and dependency graph rather than an unrelated template.
- The visual contract and `deck-config` declare one deck-wide `light` or `dark` canvas mode; every slide background stays within that mode, including cover, dividers, media pages, and ending.
- No full-slide light/dark inversion is used for pacing or emphasis. Local cards, screenshots, media frames, overlays, and dialogs may contrast without becoming an alternate page theme.
- Logical size, responsive behavior, safe regions, type, contrast, and density work in the actual target conditions.
- Reading order, keyboard focus, alternative text, status cues, and interactive names are usable.
- Source evidence remains distinguishable from explanation or decoration when needed.
- Emphasis has semantic purpose; ordinary and focal states are visibly different when rhythm matters.
- Reduced-motion mode preserves all content, hierarchy, state, and reachability without waiting for animation completion.

Inspect an all-slide contact sheet or equivalent full-slide rendered gallery for canvas continuity, then inspect representative screens in detail. A computed-style inventory is insufficient because full-screen descendants, pseudo-elements, gradients, and media can change the perceived canvas. Source review alone cannot pass this gate.

## Gate 5 — Runtime composition

- `deck-config` contains parseable `version`, `title`, supported `aspect`, and only recognized optional features.
- Baseline behavior works without assuming `navigation`, `presenter`, `media`, or `dialog`.
- Every declared feature satisfies its contract in [html-runtime.md](html-runtime.md); undeclared features remain inactive and expose no dead interface chrome.
- Runtime state remains synchronized across all enabled surfaces.
- Missing assets, unsupported enhancements, rejected autoplay, and media errors have understandable fallbacks.
- No feature or essential content depends solely on hover, color, autoplay, or a completed animation.

Run the structural validator from the skill directory:

```bash
python3 scripts/validate_deck.py path/to/index.html --receipt
python3 scripts/validate_deck.py path/to/index.html --check-receipt validation-receipt.json
```

`--receipt` writes `validation-receipt.json` in the deck root by default and only on a passing result. Relative `--check-receipt` paths resolve from that root. Use `--json` when another tool needs the findings. Recheck the receipt immediately before deriving or delivering outputs; any current artifact-hash mismatch is a failure, not a warning.

Interpret the receipt status precisely:

- `PASS_SOURCE_BOUND`: `deck-dependencies.json` is valid and the accepted artifact is bound to its declared authoring/runtime dependency closure.
- `PASS_RENDERED_ARTIFACT`: a current configured HTML artifact passed, but no reproducible dependency package was proven.
- `PASS_LEGACY_ARTIFACT_ONLY`: a legacy deck passed compatibility checks without the current configuration contract.

Do not shorten the last two statuses to an unqualified “source verified.”

The validator must reject unresolved `WOWDECK_PLACEHOLDER` markers, missing or escaping relative assets, private or absolute paths, remote runtime dependencies, undeclared detectable dynamic dependencies, invalid feature contracts, declared slide/background-mode conflicts, media/manifest mismatches, and unreadable declared media. Its background check proves declaration consistency only. Any perceived full-slide polarity switch in the rendered all-slide gallery fails Gate 4 even when structural validation passes; structural acceptance does not replace browser acceptance.

## Gate 6 — Staged media acceptance

Advance media explicitly. Do not treat a later stage as passed because an earlier one succeeded.

1. **Purpose and authorization** — Define why the medium is needed, what truth it conveys, its audience, cost, rights, and whether generation, purchase, recording, or external calls are authorized. Stop before a paid or externally mutating action without the required authority.
2. **Source and provenance** — Acquire or identify the exact source; record owner, license/sharing scope, truth status, edits, and intended fallback. A prompt or placeholder is not an asset.
3. **Technical preparation** — Verify dimensions, duration, codecs/container, audio, captions, poster or static substitute, filename, relative path, and manifest entry. Use browser-safe encodings for the target, not a universal assumed codec.
4. **Local integration** — Load from the packaged path, exercise visible controls and error recovery, verify pause/replay/navigation interactions, and inspect print/reduced-motion fallbacks in the actual HTML.
5. **Derived-output acceptance** — Confirm the medium's intended representation separately in PDF, PPTX, and MP4 outputs that were requested. Interactive playback in HTML does not prove export behavior.
6. **Published acceptance** — Only after publication is authorized, verify the deployed asset from the public or intended authenticated entry point. A local server, upload command, or deployment log is not end-to-end proof.

Record the highest stage actually passed for each media item. Unknown external outcomes require readback or a receipt before retrying.

## Deliverable matrix

Validate only requested rows, but report each row independently.

| Deliverable | Identity binding | Required acceptance |
|---|---|---|
| HTML package | Validator receipt with exact `artifact_sha256` and source-component hashes | Structural validation plus opening in the target browser path; inspect representative renders; exercise declared features, keyboard/focus, assets, target viewports, reduced motion, and console/runtime errors. If browser execution is unavailable, report HTML runtime as unverified. |
| PDF | File hash bound to source `artifact_sha256` | Open the PDF, confirm page count/order and intended page size, render every page to images, and inspect clipping, fonts, images, links if required, and static replacements for interaction/media. A successful print command is insufficient. |
| PPTX | File hash bound to source `artifact_sha256` | Open in the required presentation viewer, confirm slide count/order, geometry, fonts, text/image/chart/media treatment, notes if requested, and slideshow rendering. State whether content is editable or flattened. A valid ZIP/XML package is insufficient. |
| MP4 | File hash bound to source `artifact_sha256` | Probe container, codec, resolution, frame rate, duration, and audio; play the whole video or inspect it systematically for blank/frozen/cut frames, legible timing, captions, transitions, audio sync, and the intended ending. Interactive HTML controls do not carry over. |
| Public link | Exact URL and deployed source `artifact_sha256` with expected access scope | From the intended external or authenticated entry point, verify the page, required assets, deep links if promised, privacy/auth behavior, and the deployed revision. Local health checks, build success, or an upload receipt alone do not pass. |

Derived formats may legitimately omit interaction, but the Strategy Note must define the replacement behavior. Do not claim native editability, embedded media, accessibility, or public availability unless that property was verified in the target format or environment.

## Completion report

Report:

1. the canonical source and accepted `artifact_sha256` receipt;
2. requested deliverables produced and their identity bindings;
3. strategy, truth, visual, runtime, media, and format-specific gates actually exercised;
4. browsers, viewers, viewports, playback paths, and public entry points actually tested;
5. assumptions, unknowns, unverified formats, and publication boundaries that remain.

Use precise layer language: “HTML structural validation passed,” “PDF rendered and inspected,” or “public URL verified.” Do not collapse local build, browser behavior, export, upload, deployment, and public access into a single “done” claim.
