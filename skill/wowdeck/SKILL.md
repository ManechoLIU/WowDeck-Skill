---
name: wowdeck
description: Create polished, visually directed HTML presentations with concrete audience stories, product demonstrations, diagrams, imagery, and purposeful motion. Use for talks, lessons, roadshows, reports, demos, and revisions; validate requested PDF, PPTX, MP4, or public-link derivatives separately.
---

# WowDeck

Make a presentation people can understand, remember, and want to watch. Deliver finished visual scenes, with concrete content and a paced sequence. A valid HTML shell, a polished outline, or a pile of cards is an intermediate artifact.

## Start from the actual task

Inspect the supplied material, existing deck, product, assets, and accepted choices. A praised deck is a craft reference: inspect its actual rendered scenes and transitions, then name the transferable techniques. Keep its industry, private content, and palette separate from those techniques.

Choose the communication job before the route. For a product introduction, explain the product through meaningful work and visible outputs. For teaching, develop understanding through examples and practice. For a report, make the evidence and its implications legible. Use conventions as useful defaults; adapt them when the material calls for another route. Explicit current user instructions and accepted choices take precedence over aesthetic defaults; adapt and validate affected runtime contracts rather than silently overriding the direction.

Keep the Strategy Note compact: audience, desired change, throughline, evidence limits, delivery conditions. Use [strategy.md](references/strategy.md) for complex or ambiguous material. Do not spend the production effort on internal forms while leaving the deck unmade.

## Direct the content and the scenes together

Read [content-direction.md](references/content-direction.md) before writing a new deck or materially changing its story. For product work, first inspect enough source material to name the actual inputs, actions, outputs, and useful next uses. Business-facing language must still explain the product. “Audience: business owners” does not mean “replace the product with management slogans.”

Write one integrated storyboard in the existing working source: audience question, concrete takeaway, source/example, visual scene, attention/motion, next connection. Keep a full usage journey when needed, and give important capabilities their own demonstrations rather than squeezing every feature into one generic flow.

Where useful, let the audience see an output or changed situation before explaining the mechanism. Build the route around recognisable situations, inspectable work, and consequences; do not begin with a feature menu or force a pitch arc onto unrelated tasks.

## Produce the visual experience

Read [visual-system.md](references/visual-system.md). It contains composition families, projection sizes, scene transformations, media treatments, and motion recipes. For a product talk or a request for expressive visuals, open [scene-craft.html](assets/reference/scene-craft.html) in a browser and inspect its overview→focus→change→output treatments; it is a synthetic craft specimen, not a page sequence or palette to clone. Choose a subject-specific visual language and actually implement it. Layout, typography, imagery, diagrams, and motion are expressive tools; choose and combine them deliberately.

For a product or visually rich talk, a strong working pattern is `orient in a stable overview → focus on one capability → show the work/result → explain its significance → reconnect`. Use it when it helps orientation, without manufacturing a hub on every page. A light canvas, dark canvas, quiet typography, or energetic motion can all be excellent; preserve the accepted direction and keep one deck-wide light/dark canvas mode.

Build a small representative slice before multiplying pages: opening, strongest demonstration, a relationship/process scene when relevant, densest page, and ending. Render it. Compare its full-size scenes with the user’s praised reference when available, otherwise the craft specimen: can the audience inspect an actual result, see a meaningful transformation, and follow an intentional focal hierarchy? A generic wireframe, tiny panel in an empty canvas, or repeated entrance animation is still an intermediate. Refine those gaps before extending the deck. This production checkpoint needs no new approval when choices are already settled.

## Build and inspect

The initializer is optional runtime scaffolding:

```bash
python3 scripts/init_deck.py OUTPUT_DIR --title "Deck title" --features navigation
```

Resolve script paths from this skill directory. Replace the placeholder slide **and its starter composition styles**; reuse the tested controller, not its title/paragraph geometry as the whole design. [html-runtime.md](references/html-runtime.md) describes the existing navigation, presenter, media, and dialog contracts. Images, diagrams, charts, composition, and motion do not require feature flags.

Keep one reproducible authoring package when possible; a small HTML-only deck can remain honestly `artifact-only`. Do not add a build system merely to satisfy paperwork. Bind requested derivatives to the accepted source.

```bash
python3 scripts/validate_deck.py OUTPUT_DIR/index.html --receipt
node scripts/inspect_deck.cjs OUTPUT_DIR/index.html OUTPUT_DIR/inspection
```

The second command needs Playwright, sharp and an installed Chromium (set `NODE_PATH` to the available package directory if necessary). It captures actual navigation and rendered pages. Review the contact sheet **and full-size scenes**, then watch intended reveals in the browser. Opening a tab is not inspection. Neither tool judges the story, taste, or persuasion: use [quality-gates.md](references/quality-gates.md) for that separate review. If browser execution is unavailable, report the render layer as unverified.

## Keep truth and scope intact

- Preserve sources, uncertainty, rights, and sharing limits. A plausible workflow or generated concept is not product evidence or measured ROI.
- Use permitted existing assets and HTML/SVG to explain missing visuals. A video placeholder is a reserve, not a working demo; disclose unmet requested media instead of silently downgrading it to text. Generated or paid media needs the applicable authority.
- Select stage geometry and optional runtime controls for the delivery conditions; preserve reduced-motion access and readable static output.
- Publish only requested outputs. Public links, deployment, external calls, and paid generation have their own authorization and acceptance.
- When improving this shared skill, keep private decks, media, identities, feedback quotes, conversation history, and local paths outside it. Share abstract techniques and synthetic examples only. [experience-casebook.md](references/experience-casebook.md) records reusable conditions and failure patterns.
