# Content direction and screen storyboards

Use this reference after the Strategy Note and dependency graph, before layout or a material content rewrite. Keep its working records internal; the audience receives the resulting story and visuals, not production instructions.

## Turn source material into audience meaning

Protect the original facts, numbers, actors, distinctive wording, certainty, scope, and unresolved ambiguity before editing. Do not fill missing referents, causes, owners, dates, adoption, or commercial outcomes. Cluster material by the audience’s questions rather than the repository structure, meeting chronology, or feature menu.

State one throughline that answers the central question. Test the route from the audience’s position: why does the opening concern them; what do they understand next; what new fact, example, comparison, relationship, or experience does each screen add; what can they now understand or do at the ending? Remove a repeated claim or combine thin screens when there is no useful increment. Do not turn every transition into suspense or every ending into a sales ask.

For explanatory and claim-bearing screens, write a short, concrete takeaway the listener could repeat. Prefer the source’s strong wording when accurate; otherwise distill its meaning without increasing certainty. A title may express that takeaway, ask a useful question, or orient the audience. Do not force slogans, rhetorical questions, parallel sentences, or a fixed three-bullet pattern. Preserve enough detail to explain the mechanism and its conditions; important reasoning must not disappear in the name of brevity.

Before visual polish, fix the weakest communication link: relevance, clarity, evidence, comprehension, or ending. Polished typography cannot repair a missing product explanation.

## Product and business talks

Apply this section when the communication job includes explaining, demonstrating, or selling a product. It does not impose a pitch structure on teaching, research, celebration, or reporting.

For each important capability, establish the relationships below using supported facts:

`recognizable task or friction -> person’s action -> product response -> usable output -> operational significance`

Operational significance can concern preparation time, repeated entry, handoffs, traceability, consistency, asset reuse, or another audience-relevant change. Explain how the capability creates that change. Claimed savings, revenue, conversion, or ROI require their own evidence and assumptions; a plausible mechanism is not a measured result.

Build at least one coherent usage journey when a complete workflow is requested or essential to understanding the product. Follow the same person and business object from input through meaningful product steps to an inspectable output and its next use. Connect the main interface, process diagram, and demo to that journey. Describe only supported next uses: a save action alone does not establish later retrieval, re-editing, sharing, or publishing. A product tour that merely lists menus, and a marketing story that never shows what the product does, both leave a gap.

Choose diagrams by the question they answer:

- **Business capability map:** who uses what and for which result. For business audiences, use their task vocabulary instead of code modules, APIs, databases, or agent internals.
- **Workflow:** actors, steps, handoffs, decisions, and outputs needed to understand the work.
- **Information flow:** where information comes from, how it is transformed, where it goes, and which result uses it. Show relevant human review and limitations.
- **Comparison:** use the same task, scope, and criteria on both sides. A manual-versus-product comparison must not invent a competitor’s behavior or a baseline measurement.
- **Data chart:** use only justified values with units, time window, source, and uncertainty. Without measurements, explain the mechanism or propose what to measure; do not draw invented uplift bars.

An illustrative scenario must be recognizable as an example. Fictional businesses must not appear to be real customers; anonymization alone does not make an invented result factual.

## Keep audience copy separate from production notes

Business and user talks should speak in the audience’s language. Put debugging, implementation reasoning, test status, asset TODOs, and generation instructions in internal working material. Do not fill the visible deck with “pending validation” badges or author instructions.

Retain material qualifications where they affect interpretation, expressed as audience-relevant scope: an example, a target workflow, a supported range, or an assumption. Omit an unsupported claim or frame it at its actual certainty. Removing development chatter never authorizes inventing live functionality, a customer, or a proven outcome.

## The compact storyboard

Use one row per screen in the existing working source or outline; do not create a second content authority. Depth and fields may be compact for a simple deck. Cover these decisions before implementation:

| Decision | What to record |
|---|---|
| Audience question and screen role | Why this screen exists here; what preceding understanding it needs |
| New meaning and audience copy | Takeaway or intended experience, title, essential explanation, relevant qualification |
| Evidence and asset | Claim source; exact screenshot, chart, diagram, video, or intentional text composition; provenance and availability |
| Visual relationship | What the composition must communicate: sequence, comparison, hierarchy, transformation, focus, or another justified relation |
| Attention and motion | What is noticed first; reveal/transition purpose if needed; readable static and reduced-motion state |
| Timing and continuity | Speaking/reading time when constrained, link into the next screen, and any interaction or media allowance |

Do not lock every screen into the same component or require an image on every page. A real interface can carry demonstration; a diagram can explain relationships; expressive typography can carry a strong idea; whitespace can give a pause. Every selected visual must do useful work.

For a visual-heavy or long presentation, implement an early representative set from the storyboard: an opening, an important product/evidence screen, and a dense relationship screen when applicable. Inspect real renders for readability, visual force, and content clarity before extending the system. Existing accepted references allow proceeding without a new approval round; ask only for a material unresolved choice.

## Coverage and rehearsal

Map each explicit request to its screen and acceptance evidence in the existing working record. “Requested / planned / implemented / browser-checked / gap” are different states. An image prompt, empty media frame, declared feature flag, or CSS animation rule does not satisfy the corresponding implemented behavior.

A requested video reserve needs a deliberate poster/frame, intended role, placement, and graceful fallback, with missing media recorded internally. Actual playback is accepted separately. Use permitted existing assets or native HTML/SVG diagrams when suitable. New paid generation needs its own authority; do not silently replace a requested visual deliverable with bare text when assets are unavailable.

When a time limit exists, budget speech, pauses, reveals, demo playback, and transitions together. Cut redundancy and move secondary detail to an appropriate optional layer before making speech unnaturally fast. A timing sum is a plan; only an actual continuous rehearsal supports a claim that the talk fits.
