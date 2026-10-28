# Presentation strategy

Use this reference before authoring a new presentation or changing its content logic. The output is a short internal Strategy Note and a dependency graph. Keep them as working material unless the user asks to receive them; do not leak private reasoning or research into the distributable deck.

## The five-part Strategy Note

Use exactly these five sections. Each section may be brief when the answer is obvious.

### 1. Audience and context

Record who will encounter the artifact, what they already know, what language and detail they can use, what they may resist or misunderstand, and how attention will be constrained. Include the real context: live talk, classroom, defense, asynchronous reading, large display, mobile sharing, print, video, or a mixture.

Separate the primary audience from secondary viewers introduced by forwarding or publication. A presentation that must survive without a speaker needs enough context, labels, captions, and conclusions in the artifact itself.

### 2. Desired shift and communication job

Write the audience shift as `current state -> intended state`. The state may concern understanding, capability, confidence, emotion, alignment, judgment, or action.

Name the job with verbs such as explain, teach, compare, report, explore, defend, persuade, demonstrate, celebrate, or invite discussion. Multiple verbs are allowed, but establish precedence when they compete. Do not silently turn every job into persuasion or a request for approval.

### 3. Central question, route, and ending

State the central question or thesis that gives the presentation coherence. Then summarize the route as a sequence of dependencies: what the audience must encounter or understand before the next move becomes meaningful.

Choose an ending that completes the intended shift. It may be a synthesis, decision, practice, transfer task, discussion, remembered image, open question, celebration, or next action. A call to action is not the universal default.

### 4. Claim and evidence risk

List the claims whose failure would change a decision, understanding, or real-world action. For each, record its source, status, uncertainty, allowed wording, and where the audience needs a visible qualification.

Use a risk-proportional policy:

- Low consequence: preserve attribution and avoid invention; compact sourcing may be enough.
- Material consequence: keep source, scope, date, and uncertainty close to the claim.
- High consequence or contested: require current authoritative evidence, explicit limits, and review appropriate to the domain.

Mark simulations, generated data, future states, and reconstructed interfaces where the audience encounters them. Do not present brand mood, an illustrative image, a local mock, or a synthetic metric as evidence of an external fact.

### 5. Delivery constraints and optional features

Record duration, target stage, venue/viewports, language, offline needs, sharing/privacy limits, browser or viewer constraints, and every requested output. Identify the HTML source package as canonical and name the requested derivatives.

Select only the optional runtime features that earn their cost:

- `navigation`: controlled slide-by-slide movement, keyboard input, or deep links;
- `presenter`: shareable notes, timing, or speaker controls;
- `media`: audio/video playback, captions, posters, and failure recovery;
- `dialog`: intentionally layered details that need focus-managed overlays.

Still images, diagrams, charts, and reduced-motion behavior are not feature flags. Reduced-motion support is always required. If no optional feature is needed, use a single presentation unit or explicitly implement a document-style reading mode.

## Build the content dependency graph

Do not choose page titles first. Inventory material as nodes, then connect only relationships that affect comprehension or trust.

Useful node roles include:

- audience-known context or a concrete entry point;
- question, concept, definition, or method;
- observation, claim, evidence, uncertainty, or counterpoint;
- example, comparison, procedure, or demonstration;
- implication, synthesis, decision, practice, or next action.

Useful edge meanings include `requires`, `explains`, `supports`, `contrasts`, `causes`, `qualifies`, and `enables`. Keep source provenance attached to the relevant claim or evidence node.

Choose a route through the graph that:

1. starts from something the audience can recognize;
2. supplies prerequisites before dependent ideas;
3. resolves the central question without unnecessary branches;
4. places caveats where they change interpretation;
5. reaches the intended ending within the delivery constraints.

The route may be linear, comparative, cyclical, exploratory, or layered. Branches can become appendices or dialogs only when the delivery context supports them. Split screens when one view cannot maintain a clear hierarchy; combine nodes when separation would create ceremony without improving understanding.

For each screen, write a role in plain language, such as “establish the measurement boundary” or “let learners test the rule.” A role is not a fixed layout or required headline form. Titles may be statements, questions, steps, labels, or emotional beats.

## Use priors without turning them into templates

Teaching, research, analysis, status reporting, launches, demonstrations, and persuasive talks have useful conventions. Treat those conventions as questions to test against the graph, not page sequences to copy. Keep a convention only when it fits the material dependencies, audience shift, and delivery context.

When an external framework is relevant, extract only a general inference such as “make the unresolved question visible before resolving it” or “compare alternatives on shared criteria.” Rephrase it for the current situation. Do not inherit branded stage names, sample language, page counts, or a canned beginning and ending.

## Adapt the same facts to different audiences

When making audience variants, freeze the source facts and evidence first. Then vary only what the Strategy Note justifies: entry point, terminology, explanation depth, density, examples, self-containedness, optional interaction, and ending behavior. If the evidence or claim changes, that is a content revision—not an audience adaptation—and must receive a new artifact receipt.

Before implementation, check that two materially different audiences would not receive the same route merely with different colors or vocabulary.
