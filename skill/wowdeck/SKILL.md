---
name: wowdeck
description: Design, build, adapt, or audit scenario-driven HTML presentations whose content logic, visual form, runtime capabilities, and acceptance match the audience, communication job, evidence risk, and delivery context. Use for browser-authored talks, lessons, reports, defenses, demos, launches, and requested PDF, PPTX, MP4, or public-link derivatives.
---

# WowDeck

Build a presentation for the specific act of communication in front of you. Do not begin from a pitch arc, industry template, fixed aspect ratio, fixed page sequence, or mandatory interaction set.

The canonical authoring source is the smallest reproducible package of structured content, configuration, approved assets, and builder/runtime revision. HTML is the primary delivery artifact rendered from that source. Create only the deliverables the user requested, and keep every derivative bound to the same accepted source and rendered-artifact identity. A public link is a separate publication outcome, not an automatic consequence of producing local files.

## Operating contract

- Inspect the supplied sources, current implementation, delivery environment, and existing decisions before designing.
- Preserve factual boundaries. Distinguish sourced facts, interpretations, proposals, simulations, generated material, and unknowns at a prominence proportional to their risk.
- Translate explicit audience, product-value, imagery, diagram, video, and motion requests into observable acceptance conditions. Optional capabilities become required when the request needs them; minimal runtime is not permission to under-deliver.
- Treat scenario labels and external presentation frameworks as reasoning aids only. Derive general principles; do not copy their branded language, sample copy, or fixed narrative arc.
- Choose one deck-wide canvas mode—`light` or `dark`—and keep every slide background within it. Never alternate light and dark full-slide backgrounds for rhythm or emphasis; create variation with composition, scale, spacing, typography, accent, imagery, and local surfaces instead.
- Keep one canonical source of truth for content, configuration, assets, and generation logic. Regenerate HTML and its derivatives instead of editing HTML, PDF, PPTX, and MP4 as independent versions. If only a final HTML artifact exists, label it `artifact-only` rather than implying it is reproducible.
- Ask only when a missing choice would materially change the audience, communication outcome, artifact format, cost, publication authority, or risk. Otherwise record a reasonable assumption and continue.

## Workflow

1. Write the five-part internal Strategy Note in [references/strategy.md](references/strategy.md). It defines the audience/context, desired shift/job, central question/route/ending, claim/evidence risk, and delivery constraints/features.
2. Build a dependency graph from the material, then choose a justified route through it. The graph—not a scenario template—determines sequence, screen roles, explanation depth, and closing behavior. Use [references/content-direction.md](references/content-direction.md) to turn that route into audience-ready wording, a compact per-screen storyboard, and a visual production brief before layout. For product talks, connect real user actions to concrete business value and show a coherent usage journey; a feature list or a slogan is not a product explanation.
3. Synthesize a visual system from the communication task and delivery conditions. Review applicable reusable patterns in [references/experience-casebook.md](references/experience-casebook.md); apply their conditions without copying an example’s industry, palette, or page sequence. Read [references/visual-system.md](references/visual-system.md) when creating or materially changing art direction, layouts, charts, emphasis, or motion. Build and inspect representative pages before expanding a long deck; do not let a starter shell or repeated card grid become the visual system by inertia.
4. Implement the storyboard’s visual production brief and any justified semantic motion, then compose the HTML capabilities the task needs. A starter shell or text-only outline is not a finished visual presentation. Every important claim needs an appropriate visual carrier: interface, diagram, chart, comparison, evidence image, media frame, or intentional typographic composition. Read [references/html-runtime.md](references/html-runtime.md) when implementing or changing the browser artifact. The only optional runtime features are `navigation`, `presenter`, `media`, and `dialog`; reduced-motion support is part of the baseline.
5. When reproducible source inputs exist, declare them in `deck-dependencies.json`; otherwise label the result rendered-only or artifact-only. Bind the canonical source and requested outputs to one artifact identity, then validate each requested format by its own acceptance path. Run the visual coverage and representative-page checks in [references/quality-gates.md](references/quality-gates.md) before calling a deck complete; structural validation alone cannot establish visual quality.

## Boundaries

- Do not require a call to action, decision ask, climax, presenter notes, media, dialog, agenda, progress indicator, or animation unless the Strategy Note justifies it.
- Do not force 16:9. Select the supported 16:9 or 4:3 stage from the delivery need; if another geometry is essential, treat it as an explicit runtime change and test the actual target environment.
- Generated imagery, paid media generation, external publication, and deployment require the authorization appropriate to those actions. A local render or HTTP response does not prove a public outcome.
- Keep internal Strategy Notes, private research, credentials, absolute local paths, and unapproved source material out of distributable artifacts.
- When extracting or updating this skill, publish abstract methods, neutral templates, and synthetic tests only. Reading private decks or feedback for learning does not authorize uploading them: keep original presentations, media, project/customer identities, quotes, dates, conversation records, and recognizable case histories local unless separately authorized for the exact material. A private remote repository still counts as an upload.
