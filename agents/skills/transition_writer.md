# Transition Writer Skill

## Purpose
Write smooth, purposeful transitions between sermon sections. Good transitions prevent the "sermon feels choppy" problem, help listeners track the sermon's flow, and create momentum from beginning to end. Transitions are the connective tissue of good preaching.

## Input Expectations
```json
{
  "from_section": "Summary of what just concluded",
  "to_section": "Summary of what's coming next",
  "transition_type": "logical | temporal | thematic | contrast | question | summary",
  "tone": "The sermon's overall tone",
  "sermon_context": "Where we are in the sermon arc"
}
```

## Output Format
```json
{
  "transition": {
    "type": "Type of transition used",
    "text": "The transition text",
    "function": "What this transition accomplishes"
  },
  "alternatives": [
    {
      "type": "Different transition approach",
      "text": "Alternative transition"
    }
  ],
  "notes": {
    "delivery_tip": "How to handle this moment",
    "timing": "Natural pause or continuous?"
  }
}
```

## Transition Types

### Logical ("Therefore")
Shows how one point leads to the next.
- "If this is true, then..."
- "This leads us to ask..."
- "Because of this, we see that..."
- "And if God does this, then..."

### Temporal ("Then")
Moves through time or sequence.
- "But the story doesn't end there..."
- "What happens next changes everything..."
- "Earlier in this passage... now..."
- "First... second... and finally..."

### Thematic ("Similarly")
Connects related ideas.
- "We see the same pattern in..."
- "This theme appears again..."
- "Another aspect of this..."
- "Scripture echoes this elsewhere..."

### Contrast ("But")
Highlights difference or tension.
- "But there's another side to this..."
- "However, the text doesn't stop there..."
- "And yet..."
- "On the other hand..."

### Question ("What if?")
Uses questions to pivot.
- "But what does this mean for us?"
- "So how do we live this out?"
- "You might be wondering..."
- "Here's the question I keep coming back to..."

### Summary ("So far")
Recaps before moving forward.
- "So we've seen that... Now..."
- "Having established this... we turn to..."
- "With that in mind..."
- "Given all this..."

## Transition Placement

### Introduction → Point 1
Light transition—you've set up the text, now dive in.
"Let's look at what the text actually says..."
"Three things stand out as we explore this passage..."

### Point 1 → Point 2
Acknowledge completion, create anticipation.
"But there's more here. If grace goes before us... then what do we do with that?"
"That's the first movement. But the father doesn't just wait—he runs."

### Point 2 → Point 3
Build momentum toward conclusion.
"And this brings us to the heart of it all..."
"Which leads to the most challenging question..."

### Points → Application
Signal shift from understanding to action.
"So what does this mean for us this week?"
"This isn't just ancient history. It's Monday morning reality."

### Application → Conclusion
Prepare for landing.
"As we close..."
"Let me leave you with this..."
"Here's what I want you to hold..."

## Constraints and Guidelines

### Do's
- Make transitions purposeful, not just filler
- Use transitions to show sermon logic
- Vary transition types throughout the sermon
- Use transitions to help lost listeners re-engage
- Keep transitions brief but clear
- Let transitions breathe (slight pause)

### Don'ts
- Don't make transitions mechanical ("Secondly...")
- Don't use the same transition pattern every time
- Don't skip transitions—abrupt shifts lose listeners
- Don't make transitions too long
- Don't use transitions to stall
- Don't forget to write them (common sermon problem)

## Example Transitions

**After Introduction**
"That's the world this parable enters. Now let's see how Jesus surprises everyone in the room."

**Between Major Points**
"If grace runs to meet us before we even look up—and it does—then what does that mean for how we wait for others?"

**Contrast Transition**
"But here's where the story takes an unexpected turn. Because there's another son."

**Question Transition**
"You might be thinking: this sounds great, but what do I actually DO with this? I'm so glad you asked."

**Toward Application**
"Here's where it gets personal. This isn't just a story about a father and his sons. It's a story about you and me and the God who never stops looking down the road."

**Toward Conclusion**
"As we close, I want you to hold onto one thing. Just one."

## Example Output
```json
{
  "transition": {
    "type": "question",
    "text": "So if grace runs to meet us before we even turn around—and the text is clear that it does—then what does that change about how we live? Here's where it gets practical.",
    "function": "Moves from doctrinal point about prevenient grace to application section"
  },
  "alternatives": [
    {
      "type": "logical",
      "text": "Because God runs toward us, we're freed to run toward others. Let me show you what I mean."
    },
    {
      "type": "summary",
      "text": "We've seen the father watching, waiting, running. Now the question becomes: how do we live like people who've been found?"
    }
  ],
  "notes": {
    "delivery_tip": "Brief pause after 'that it does' before pivoting to practical. Let the doctrine settle before turning to action.",
    "timing": "Natural breath pause—don't rush through"
  }
}
```

## Context for UUMC
- Congregation tracks sophisticated sermons—transitions can be subtle
- Avoid mechanical transitions that feel formulaic
- Can use more literary/artistic transitions
- Katie's style: fluid, not choppy
- Trust listeners to follow—don't over-explain
