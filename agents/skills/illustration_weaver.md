# Illustration Weaver Skill

## Purpose
Seamlessly integrate illustrations into sermon content so they illuminate rather than distract. Handles the craft of incorporating stories, examples, and images into the sermon's flow without breaking momentum or overshadowing the scripture.

## Input Expectations
```json
{
  "illustration": "The illustration content to weave in",
  "sermon_point": "The point being illustrated",
  "preceding_content": "What comes before the illustration",
  "following_content": "What comes after the illustration",
  "illustration_purpose": "illuminate | prove | apply | transition | humanize",
  "tone": "The sermon's overall tone"
}
```

## Output Format
```json
{
  "woven_section": {
    "lead_in": "Sentences that introduce the illustration",
    "illustration": "The illustration itself, shaped for this context",
    "lead_out": "Sentences that connect back to the sermon point",
    "full_text": "Complete woven section"
  },
  "integration_notes": {
    "transition_technique": "How this flows from previous content",
    "connection_made_explicit": "How illustration connects to point",
    "pacing": "Suggested delivery rhythm",
    "length_appropriate": "Assessment of length for this purpose"
  },
  "alternatives": {
    "shorter_version": "Condensed version if needed",
    "different_entry": "Alternative way to introduce"
  }
}
```

## Weaving Techniques

### Lead-In Approaches

**Direct Introduction**
"Consider this: [illustration]"
"There's a story that captures this well: [illustration]"

**Observational Bridge**
"You see this in [context]: [illustration]"
"This shows up in unexpected places: [illustration]"

**Question Bridge**
"What does this look like in practice? [illustration]"
"How do we know this is true? [illustration]"

**Contrast Bridge**
"It's one thing to say this, but another to see it lived out: [illustration]"
"The opposite is also instructive: [illustration]"

**Connection Bridge**
"It reminds me of [illustration]"
"This is what [person/group] discovered: [illustration]"

### Lead-Out Approaches

**Explicit Connection**
"This is what [biblical character/concept] discovered too."
"And isn't this exactly what our text describes?"

**Application Bridge**
"For us, this might look like..."
"The question for us is..."

**Deepening Bridge**
"But notice—the parallel goes even deeper:"
"And if this is true, then..."

**Rhetorical Landing**
"That's what grace looks like."
"This is the kingdom breaking through."

## Constraints and Guidelines

### Do's
- Make the connection explicit (don't assume people see it)
- Keep transitions smooth and natural
- Match illustration tone to sermon tone
- Use the illustration's strongest image
- Return to scripture after illustrating
- Let the illustration serve the point

### Don'ts
- Don't let illustration upstage scripture
- Don't over-explain the illustration
- Don't force connections that aren't there
- Don't stack multiple illustrations back-to-back
- Don't use illustrations as filler
- Don't introduce then abandon (always land it)
- Don't make the illustration the point

### Pacing Principles
- Illustrations are rest stops, not destinations
- Congregation needs time to visualize
- Transition out should redirect to text
- Balance showing and telling
- Trust the illustration to do its work

## Illustration Length Guidelines

**Short Illustration (50-75 words)**
- Single image or moment
- Quick example
- Use when point is already clear

**Medium Illustration (100-150 words)**
- Brief story with context
- Example with details
- Standard sermon illustration

**Long Illustration (200-300 words)**
- Full narrative arc
- Complex example
- Use sparingly (once per sermon max)

## Example Output
```json
{
  "woven_section": {
    "full_text": "This is what Wesley called prevenient grace—the grace that 'comes before.' Before we recognize our need. Before we take a step toward home. Before we even wake up to the fact that we've wandered.\n\nI think of what happened in Chile in 2010, when thirty-three miners were trapped two thousand feet underground after a cave-in. For seventeen days, rescuers drilled and searched, not knowing if anyone had survived. But here's what strikes me: even before the miners knew rescue was coming, even in those dark days when they had no communication with the surface, people above ground were already working to save them. Drilling through rock. Engineering a capsule. Preparing everything needed to bring them home.\n\nThe miners didn't save themselves. They couldn't. But they also weren't forgotten. Grace was coming for them before they had any idea it was on the way.\n\nAnd friends, this is the heartbeat of the gospel: you are not forgotten. Before you knew to look up, God was already looking down. Before you could take a step toward home, home was already running toward you.",
    "lead_in": "I think of what happened in Chile in 2010...",
    "lead_out": "And friends, this is the heartbeat of the gospel: you are not forgotten.",
    "illustration": "Chilean miner rescue - grace working before awareness"
  },
  "integration_notes": {
    "transition_technique": "Wesley concept leads to concrete example",
    "connection_made_explicit": "Final lines explicitly tie miners to prevenient grace",
    "pacing": "Slow down on 'two thousand feet underground' for weight"
  }
}
```

## Context for UUMC
- Educated congregation follows sophisticated illustrations
- Avoid illustrations that need lengthy setup
- Trust the congregation to make connections
- Can use metaphor and imagery freely
- Katie's style: substantial, not sentimental
