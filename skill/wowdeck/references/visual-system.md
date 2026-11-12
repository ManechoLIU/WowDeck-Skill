# Visual direction and scene craft

Visuals are part of the explanation. Start with what the audience should notice and experience, then choose geometry, evidence, type and movement that express it. Use these techniques as a working vocabulary, not a mandatory slide sequence.

## Establish the direction

Inspect any accepted deck or reference in its rendered form. Name the useful technique precisely: a stable overview, in-place focus, evidence at readable scale, coordinated output board, scene continuity, restrained depth, or a paced reveal. Transfer those techniques rather than cloning the industry's palette, wording or motifs. When revising, preserve the accepted direction unless a new decision changes it.

Write a short art-direction brief in the existing working source:

`subject / audience experience / primary geometry / typography / material and depth / color roles / motion grammar / traits to avoid`

Make the direction specific enough to influence the scene. “Modern, premium, cinematic” gives no geometry or attention hierarchy. A subject may suggest a plan table, editorial studio, field notebook, evidence wall or another useful visual language; a literal metaphor is optional. Avoid choosing a template from an industry name alone.

Use one deck-wide `light` or `dark` canvas mode, with shared tokens for background, ink, muted ink, line, local surfaces, accent and focus. Keep that polarity across cover, chapters and ending. Vary composition, density, scale, imagery and local contrast to create rhythm. Preserve truthful screenshots inside a consistent frame/matte instead of recoloring their evidence. Print can have a separately validated substrate.

## Compose recognisable scene families

Choose a family for its explanatory job. Reuse alignments and anchors so the deck feels coherent; vary focal scale and position so scenes do not become clones.

| Scene / question | Build it this way | Useful motion and static equivalent |
|---|---|---|
| Opening / what is this about? | Strong concise thesis with one product/result/subject field; minimal chrome and a deliberate focal hierarchy | A restrained arrival; static title and focal visual already readable |
| Overview / where are we? | A stable map of the important relationships or capabilities; keep spatial positions recognisable | Dim context and focus one region in place; final still retains map and active label |
| Capability / what changes? | Recognisable situation + action + visible result; contrast a small input with a dominant output | Transform the same named object across states; side-by-side or labeled final state in reduced motion |
| Product tour / where do I act? | A readable interface crop with 1–3 exact callouts and a nearby result; retain an overview when orientation is needed | Focus shifts between actual controls/states; step labels and overview remain in the static version |
| Outputs / what can I use? | Show real permitted outputs at different useful scales, with a common topic and a clear relationship | Compose the set or reveal its roles; final board remains legible without the reveal |
| Workflow / how does it proceed? | Directed path, actors, decisions, review and outputs; use lanes when ownership matters | Reveal in reasoning order or move a named object; final arrows and labels encode the same order |
| Comparison / what differs? | Shared task, baseline and criteria; align corresponding elements instead of separate prose cards | Highlight one comparison at a time; all criteria and qualifications remain visible statically |
| Evidence / why believe it? | Dominant artifact/photo/chart with a precise interpretation and source; little decorative competition | Zoom/callout preserves context; no transient-only evidence |
| Synthesis / what remains? | Reconnect the demonstrated changes into a simpler whole; end at the audience's intended understanding/action | Settle into a clear final state; avoid a closing page that merely repeats the opening slogan |

A useful demonstration sequence is `overview → in-place focus → work/result → meaning → reconnect`. Keep the object or position stable between scenes. This creates continuity without forcing a story map onto a short lesson or inserting repeated transition pages for ceremony.

## Make evidence and outcomes large enough

Use an actual permitted interface or output when explaining a product. Start from the result when it helps the audience understand the promise, then show the relevant work. Full-screen application thumbnails are often too small: crop to the meaningful operation, use a focused enlargement, and preserve enough context to locate it. Callout connectors should terminate at the exact referent. Separate annotation from the original pixels.

Images can explain the subject, create atmosphere, demonstrate a state or show evidence. Give each a purpose; decoration alone does not fulfil a requested product demonstration. If an exact asset is missing, inspect available assets first, then use a truthful HTML/SVG diagram or labeled concept. Do not fabricate documentary UI or silently replace a requested video with a generic poster.

Frame portrait media deliberately; do not stretch it across the canvas. Use a representative poster, a concise “what to notice” caption, controls and failure recovery. Let the audience see the action and result without a long idle recording. Narration, when requested, must describe the visible operation at the same time, with natural pauses; a script or duration sum does not prove synchronisation. Follow [quality-gates.md](quality-gates.md) for media and export acceptance.

## Scale and typography for projection

Select 16:9 or 4:3 from the actual delivery conditions; uniformly scale a fixed logical stage and letterbox rather than stretch. For a 1600 × 900 stage, useful starting values are:

- safe margins around 64–88 px, adjusted for controls/captions and the venue;
- display type around 72–104 px, scene headings 48–68 px, body 26–34 px, supporting labels 18–24 px;
- one dominant focus, a short reading order, and supporting text that can be read at the target distance.

These are starting points, not an excuse to shrink content until it fits. Inspect the densest scene at the smallest target viewport. Split, crop, simplify or move secondary detail when required. Use CJK-capable fonts and intentional Chinese line breaks; avoid enormous titles above tiny body paragraphs. Keep critical words, chart labels and arrows as HTML/SVG text.

Use stable meanings for color, with shape/text/position as well. Verify contrast and the smallest necessary text. Informative images need alternative text or an equivalent description; decoration should have empty alt text or `aria-hidden="true"`. Charts retain units, scope, sources and uncertainty; do not draw invented improvement bars.

## Design motion as a sequence of attention

Use motion when it contributes to the talk, including a deliberate emotional beat. Reduced-motion support is an accessible counterpart, not a reason to strip expressive normal-mode animation from a request for it.

| Meaning | Technique | Practical starting point |
|---|---|---|
| Orient | Quiet scene transition with a stable title or shared anchor | 220–400 ms; short travel rather than a large fly-in |
| Focus | In-place enlargement or dimming of context around a selected region | 450–750 ms; keep the referent anchored and readable |
| Explain order | Reveal connected nodes or stages in their real dependency order | 300–550 ms per change, 60–120 ms stagger for tightly related items |
| Show change | Move/transform the same named object from input to result | 500–850 ms; preserve identity and show the final output |
| Establish hierarchy | Bring forward the relevant layer, then settle | 450–700 ms; restrained perspective/scale, no critical text distortion |
| Sustain atmosphere | Subtle texture/light/motif that belongs to the subject | Slow and low contrast, stopped offscreen; remove in reduced motion |

Write `before → after / trigger / purpose / readable final state`. Match durations to speaking and reading time; these values are tuning starts, not fixed quotas. For multi-step tours expose replay or deterministic revisit behavior. Clear timers and animation state on leave; stop hidden-slide work. A generic fade on every page does not meet a request for varied narrative motion. Adding unrelated animations to every object makes the explanation harder.

In reduced motion remove travel, parallax, looping and unnecessary delay. Show essential final content immediately or through direct state replacement. Keep order, labels, focus, keyboard behavior and media controls equivalent. Never gate essential content on `transitionend`.

## Calibrate finished-scene fidelity

Open [scene-craft.html](../assets/reference/scene-craft.html) as a synthetic working example. Study continuity, focus, a named object changing state, readable content within the artifact, and an output composition. Adopt a technique when it serves the current subject; its dark canvas and scene order are examples, not requirements.

When the user points to a praised deck, use that exact deck as the craft benchmark locally. Compare comparable roles at the same viewing scale: demonstration to demonstration, flow to flow, ending to ending. Name the visible gap and repair it. Do not reduce the reference to its colors or assume that an outline plus diagrams matches its finish.

A wireframe is useful for staging, but a finished illustrative product scene needs enough concrete content to inspect: a meaningful input, a source cue, a real decision/change, and a readable output. Use a truthful native illustration with deliberate geometry/detail when photography is unavailable; a repeated generic rectangle/icon does not explain the subject. Use available space for legible evidence and hierarchy, while keeping quiet pauses intentional. Visual weight and density should follow the story rather than leaving every operation as a small panel beside broad empty margins.

## Produce, then judge the result

Read the storyboard as a visual sequence. Are the product and outputs actually visible? Do processes show a direction and a transformation? Does a comparison use shared criteria? Can the audience tell a quiet statement from an evidence scene? Do the strongest moments earn their scale and timing?

Render representative scenes before expanding; then inspect an all-slide gallery and full-size scenes. Watch reveals, replay/revisit, and reduced-motion states. Source code, image counts, animation counts and declared layout names cannot establish taste or comprehension. A decorative SVG on every page is no better than no meaningful picture; an HTML-only diagram or typographic scene can be excellent. Use [quality-gates.md](quality-gates.md) to report these judgments separately from runtime checks.
