# Illustration Finder Skill

## Purpose
Find contemporary, relevant illustrations that illuminate sermon points. Sources fresh, current examples from news, culture, science, literature, and everyday life. Explicitly avoids personal/family anecdotes per Katie's preaching style.

## Input Expectations
```json
{
  "sermon_point": "The theological or practical point needing illustration",
  "scripture_context": "The passage being preached",
  "tone": "serious | hopeful | challenging | pastoral",
  "congregation_context": "Any specific congregational needs",
  "avoid_topics": ["Optional list of topics to avoid"]
}
```

## Output Format
```json
{
  "point_to_illustrate": "Summary of the sermon point",
  "illustrations": [
    {
      "title": "Brief title for reference",
      "category": "news | science | literature | history | culture | everyday | nature",
      "content": "The illustration itself, written in sermon-ready form",
      "source": "Where this comes from (verifiable)",
      "connection": "How this connects to the sermon point",
      "length": "short | medium | long",
      "tone": "Match with requested tone",
      "usage_notes": "Any considerations for using this illustration"
    }
  ],
  "alternative_approaches": [
    "Brief mention of other angles that could work"
  ],
  "cautions": ["Any sensitivities to be aware of"]
}
```

## Constraints and Guidelines

### What to Include
- Current events (within last 2-3 years when possible)
- Scientific discoveries and research findings
- Literature and poetry (classic and contemporary)
- Historical examples with fresh perspective
- Everyday life observations (not from Katie's personal life)
- Nature and creation
- Art, music, film (appropriate for diverse congregation)
- Sports and culture (when broadly accessible)
- Human interest stories from reputable news sources

### What to AVOID
- Personal anecdotes about family, children, spouse
- Dated illustrations (unless historical point)
- Politically charged examples
- Illustrations that require explaining they're not political
- Overused sermon illustrations (check Snopes)
- Celebrity gossip or tabloid content
- Anything that could embarrass or expose individuals
- Illustrations that only work for certain demographics
- Manipulative emotional stories
- Made-up scenarios presented as real

### Quality Standards
- Verify factual accuracy (check multiple sources)
- Ensure current relevance
- Consider diverse congregation's perspective
- Match illustration length to point's importance
- Make the illustration serve the text, not overshadow it
- Include source for accountability

## Illustration Categories

### News & Current Events
- Look for stories of hope, resilience, community
- Science discoveries that reveal wonder
- Human interest stories of transformation
- Avoid: partisan politics, divisive social issues

### Literature & Arts
- Poetry that captures the point concisely
- Novel excerpts that resonate
- Film scenes widely known
- Song lyrics (check appropriateness)

### History
- Lesser-known historical figures
- Methodist/Wesleyan history when relevant
- Louisiana/Baton Rouge local history
- Church history done accessibly

### Science & Nature
- Astronomy and cosmology (wonder, perspective)
- Biology and ecology (interconnection)
- Psychology research (human nature)
- Environmental observations

### Everyday Life
- Common experiences universally relatable
- Workplace scenarios (generic, not personal)
- Parenting challenges (general, not Katie's)
- Community life observations

## Example Output Snippet
```json
{
  "point_to_illustrate": "God's grace reaches us before we even know to look for it",
  "illustrations": [
    {
      "title": "The James Webb Telescope Discovery",
      "category": "science",
      "content": "In 2022, the James Webb Space Telescope sent back images of galaxies that formed just 300 million years after the Big Bang—light that had been traveling toward us for over 13 billion years. Long before humanity existed, before Earth formed, before our sun ignited, that light was already on its way to us. The universe was preparing a gift we wouldn't be ready to receive for billions of years. This is a little like how Wesley described prevenient grace—God's love reaching toward us long before we had any capacity to reach back.",
      "source": "NASA James Webb Space Telescope mission, 2022",
      "connection": "Prevenient grace as divine initiative that precedes human awareness",
      "length": "medium",
      "tone": "hopeful",
      "usage_notes": "Works well for educated congregation; could simplify for accessibility"
    }
  ]
}
```

## Context for UUMC
- University community appreciates intellectual illustrations
- Diverse congregation—choose broadly accessible examples
- Avoid anything that reads as political
- Louisiana/Baton Rouge examples welcome when natural
- "Purple" congregation—don't assume shared cultural touchpoints
- Pastor Katie's style: substantial, not sentimental
