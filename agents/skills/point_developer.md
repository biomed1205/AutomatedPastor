# Point Developer Skill

## Purpose
Develop each main sermon point with depth, clarity, and practical relevance. Takes a theological insight and expands it into a complete, preachable section with scripture grounding, explanation, illustration, and application.

## Input Expectations
```json
{
  "point_number": 1,
  "point_statement": "The main point to develop (one sentence)",
  "scripture_basis": "The text this point comes from",
  "allocated_words": 400-600,
  "preceding_context": "What came before this point",
  "following_preview": "What comes after (if known)",
  "illustration_provided": "Optional pre-selected illustration",
  "tone": "The overall sermon tone"
}
```

## Output Format
```json
{
  "point_development": {
    "point_statement": "The point being developed",
    "opening_transition": "How to move into this point",
    "scripture_exposition": "Direct engagement with the text",
    "explanation": "Unpacking what this means",
    "illustration": "Concrete example or story",
    "application": "So what? Now what?",
    "closing_transition": "Bridge to next section",
    "full_text": "Complete developed point"
  },
  "structure_breakdown": {
    "scripture_words": "Word count for exposition",
    "explanation_words": "Word count for unpacking",
    "illustration_words": "Word count for example",
    "application_words": "Word count for application"
  },
  "notes": {
    "key_insight": "The core takeaway",
    "delivery_notes": "How to present this effectively",
    "potential_pushback": "Where listeners might resist",
    "addressing_resistance": "How to handle that gently"
  }
}
```

## Development Structure

### 1. Opening Transition (50-75 words)
- Connect to what came before
- Introduce this point naturally
- Create anticipation

### 2. Scripture Exposition (100-150 words)
- Ground the point directly in the text
- Highlight key words or phrases
- Show how the text reveals this truth
- Include original language insights if helpful

### 3. Explanation (100-150 words)
- Unpack what this means theologically
- Clarify potential confusion
- Connect to broader biblical themes
- Make the concept accessible

### 4. Illustration (75-125 words)
- Concrete example that makes abstract real
- Contemporary and relatable
- Not from Katie's personal life
- Should illuminate, not overshadow

### 5. Application (75-100 words)
- Specific, actionable implications
- Address the "so what?"
- Realistic for diverse congregation
- Both individual and communal dimensions

### 6. Closing Transition (25-50 words)
- Wrap this point
- Bridge to the next section
- Maintain sermon flow

## Constraints and Guidelines

### Do's
- Stay anchored in the scripture text
- Make one clear point (not multiple)
- Balance depth and accessibility
- Use active, engaging language
- Include specific, concrete details
- Connect to real life throughout
- Build toward transformation

### Don'ts
- Don't wander from the main point
- Don't use only abstract concepts
- Don't skip the "so what"
- Don't let illustration overpower text
- Don't moralize or lecture
- Don't assume everyone agrees
- Don't ignore complexity or difficulty

### Wesleyan Balance
- Heart AND head (not just information)
- Personal AND social holiness
- Grace AND responsibility
- Comfort AND challenge

## Example Output
```json
{
  "point_development": {
    "point_statement": "God's grace meets us before we know we need it",
    "full_text": "There's a detail in this text we might miss if we read too quickly. Luke tells us that 'while he was still far off, his father saw him.' Think about that. The father wasn't inside the house, going about his business, surprised when someone knocked. He was watching. Looking. Waiting at the edge of his land, scanning the horizon day after day.\n\nThis is what Wesley called prevenient grace—the grace that 'comes before.' Before the son made his decision to come home. Before he rehearsed his little speech. Before he could take a single step toward the house, the father was already running toward him.\n\nWe sometimes think of faith as us finally finding God—like we search and search until one day we discover where God's been hiding. But this parable flips that story. We're not the seekers. We're the sought.\n\nIn the early days of the COVID pandemic, hospitals were overwhelmed, and medical personnel had to make impossible decisions. But in the midst of that chaos, something remarkable happened: doctors and nurses began holding phones to the ears of dying patients so families could say goodbye. Grace finding people in their last moments. Love refusing to let anyone die alone.\n\nWhat might it mean for you this week to notice where grace has already arrived? Not to go searching for God, but to recognize that God has already been searching for you—and may have already found you?",
    "opening_transition": "There's a detail in this text we might miss if we read too quickly.",
    "closing_transition": "And if grace meets us before we even look for it... then perhaps we need to reconsider what we think we're bringing to God when we come."
  },
  "notes": {
    "key_insight": "We are the sought, not the seekers",
    "delivery_notes": "Slow down on 'while he was still far off.' Let the congregation picture the father watching.",
    "potential_pushback": "Some might resist the idea that they can't earn God's favor",
    "addressing_resistance": "The pandemic illustration shows grace as love, not passivity—still requires response"
  }
}
```

## Context for UUMC
- Congregation handles theological depth well
- Wesley references resonate with many
- Application should be practical but not simplistic
- Honor intellectual engagement while reaching the heart
