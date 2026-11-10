# Visual system

Use this reference to translate the Strategy Note and dependency graph into a coherent visual language. Visual design must explain, orient, compare, emphasize, or create the intended experience; it is not a theme applied after the content is finished.

## Derive a visual contract

Before composing screens, record:

- visual purpose and the audience's viewing conditions;
- composition model and intended logical size or responsive behavior;
- primary geometry, alignment, spacing, and density;
- typography behavior across required languages;
- one deck-wide canvas mode (`light` or `dark`), its base background family, and the allowed local surface range;
- color, status, and emphasis semantics;
- diagram, chart, image, and media treatment;
- ordinary state, focal state, and any rhythm or reveal behavior;
- traits to avoid because they would mislead, distract, or resemble an unrelated template.

Derive these choices from the cognitive task, content carriers, brand material, audience, and delivery context. An industry metaphor is optional. Do not map an industry name directly to a visual template, and do not preserve a prior deck's geometry merely by changing colors.

## Keep one deck-wide background mode

Choose `light` or `dark` once for the presentation canvas and keep it across the cover, ordinary slides, section dividers, evidence pages, media pages, and ending. Do not alternate, invert, or switch between light and dark full-slide backgrounds to manufacture rhythm, signal a chapter, or make a page feel important. A deck that changes canvas polarity reads as multiple visual systems even when its accent colors match.

Create pacing and emphasis inside the chosen mode through layout, whitespace, type scale, focal imagery, accent placement, density, borders, diagrams, and semantically justified motion. Cards, panels, charts, dialogs, screenshots, and media frames may use local contrast, but they must remain subordinate surfaces rather than turning the whole slide into the opposite mode. Keep full-bleed imagery inside the same perceived canvas family with a consistent crop, matte, or overlay. Do not recolor truthful screenshots or video merely to satisfy the mode; preserve the evidence and use a fixed canvas matte, frame, header, footer, or layout crop to keep the deck visually continuous.

Use shared deck-level tokens for the canvas, text, muted text, lines, panels, focus, and accent. Do not keep unused inverse-theme slide classes or per-page background overrides in a newly generated deck; they invite accidental theme switching during revision. Print or export may use a different substrate only as an explicit format-specific transformation that is validated separately, not as mixed styling in the live deck.

## Compose from semantic relationships

Use the dependency graph to choose visual structures:

- shared coordinates for comparisons;
- adjacency and alignment for related items;
- direction and labeled connectors for sequence or causality;
- containment for hierarchy or scope;
- repeated position for continuity across states;
- tables or small multiples when precise comparison matters more than drama;
- diagrams or annotated evidence when relationships matter more than prose.

Write the intended audience takeaway before drawing a diagram or chart. Show only relationships needed for that takeaway, but retain units, scope, uncertainty, and source cues that affect interpretation.

Do not force every screen into a “one conclusion plus proof” pattern. A screen may establish context, pose a question, teach a step, provide breathing room, invite comparison, hold an experience, or support discussion. It still needs a clear role and visual focus.

## Size, fit, and safe regions

Do not assume 16:9. Select the supported `16:9` or `4:3` stage from the Strategy Note and let the runtime map it to the corresponding logical dimensions. Scale the stage uniformly and allow letterboxing rather than stretching it. If the task requires a different ratio or a responsive document rather than a stage, treat that as an explicit runtime change; do not silently coerce it to 16:9.

Express safe regions in relation to the selected stage and target environment. Account for projector overscan, browser chrome, captions, controls, mobile crops, and print margins where applicable. Verify the densest screen at the smallest target viewport instead of shrinking all typography until it fits.

## Typography and hierarchy

- Choose typefaces that cover the required scripts and can be legally packaged or reliably substituted.
- Use a small, intentional set of text roles. Size, weight, measure, spacing, and position should make reading order evident without color.
- Match terminology and density to the audience. Do not hide missing explanation behind tiny labels or oversized decorative type.
- Use tabular numerals where comparisons or timing require stable alignment.
- Keep essential copy as text when search, accessibility, localization, or editability matters.

Design a clear static hierarchy for every screen. For a longer or performance-oriented presentation, add an emphasis map naming the screen, what the audience should notice, the chosen emphasis method, its semantic purpose, and its static/reduced-motion equivalent. Ordinary screens should create contrast and breathing room; if everything is a highlight, nothing is.

## Color, evidence, and accessibility

Assign stable meanings to color roles and verify contrast in the target environment. Never make color the only carrier of status, change, or correctness. Add text, shape, icon, pattern, or position.

Keep sourced evidence visually distinguishable from interpretation or decoration when confusion would matter. Do not crop, recolor, or annotate source media in a way that changes its apparent meaning; disclose material edits and keep annotations separable where practical.

Every informative image needs meaningful alternative text or an adjacent textual equivalent. Decorative images use empty alternative text. Charts need a concise accessible takeaway plus the units, scope, and source required to interpret them.

## Media and generated visuals

Use imagery or timed media only when it contributes evidence, explanation, demonstration, atmosphere, or memory. Record its purpose, source, rights, truth status, and fallback before integration.

Generated visuals must not impersonate documentary evidence. Critical labels and claims should remain in HTML/SVG text rather than being baked into generated pixels. A missing trustworthy asset is a reason to use a diagram, evidence board, or explicit placeholder—not to fabricate a screenshot.

Follow the staged media gates in [quality-gates.md](quality-gates.md).

## Motion and reduced motion

Motion is a presentation technique, not a runtime feature. Use it only when it clarifies continuity, causality, hierarchy, feedback, or an intentional emotional beat. Prefer short, interruptible transitions and deterministic reveals. Essential information must not exist only during an animation or after a `transitionend` event.

`prefers-reduced-motion` support is mandatory whether or not the deck uses noticeable animation. In reduced-motion mode:

- remove non-essential travel, parallax, looping, and delay;
- make all essential content reachable immediately;
- preserve state changes through static hierarchy, labels, or direct replacement;
- keep keyboard and focus behavior identical;
- ensure media does not autoplay solely to create a reveal.

Also ensure that the initial state is understandable before scripts or animations run.

## Visual acceptance

Inspect rendered output, not only the DOM or source code. Review an all-slide contact sheet or equivalent full-slide rendered gallery to confirm that every slide remains in the declared canvas mode, then inspect the entry screen, the densest screen, a representative evidence/data screen, every media treatment, and the ending at actual target sizes. Computed styles alone are not visual proof. Check reading order, clipping, contrast, focus, source labels, and whether the intended emphasis survives a screenshot, print, and reduced-motion mode when those paths matter.

## From art direction to visible craft

Use the storyboard in [content-direction.md](content-direction.md) to select the visual relationship before selecting a layout. For example, make a comparison spatially comparable, make a workflow’s direction clear, and connect an interface callout to the exact feature it explains. Do not arrange everything as equal cards or rely on a generic glow to create a product identity.

For product introductions, use legible real product imagery when available and relevant. A full interface thumbnail can orient the audience; focused crops and restrained callouts explain the task. Preserve provenance and context, avoid unreadably small text, and do not crop away a limitation that changes meaning. Illustrations or generated UI concepts must not masquerade as actual product evidence.

Create variation inside the accepted visual system: a strong typographic opening, a product stage, an annotated detail, a process or information-flow diagram, a comparison, or a quiet synthesis may each suit different content. These are options, not a sequence or quota. Avoid both monotonous repeated card grids and unrelated layouts that destroy continuity. A request for richer visual effects requires visible composition and semantic motion, not merely a different gradient.

For talks explicitly requesting strong motion, plan techniques by meaning and timing: staged flow reveals for order, connected movement for a real transformation, focus/callout changes for interface explanation, and restrained depth for hierarchy. Do not make every screen fade upward identically. Keep atmosphere subordinate to the explanation, stop work on hidden slides, and respect the baseline reduced-motion and static-output contracts. Judge the rendered sequence and revisit/replay behavior, not the number of keyframes.

Apply relevant patterns in [experience-casebook.md](experience-casebook.md) without adopting an example’s palette, wording, page count, or feature set as a universal recipe.
