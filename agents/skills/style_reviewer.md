# Style Reviewer Skill

## Purpose
Review sermon content for alignment with Katie's preaching voice and style. Ensures the sermon sounds authentically like Katie—her vocabulary, rhythm, approach—while maintaining quality and avoiding her noted patterns to avoid.

## Input Expectations
```json
{
  "sermon_content": "The sermon draft to review",
  "section": "full | introduction | body | conclusion",
  "specific_concerns": ["Optional areas to check"],
  "comparison_notes": "Optional notes from previous sermons"
}
```

## Output Format
```json
{
  "overall_assessment": {
    "authenticity_score": "strong | adequate | needs_work",
    "voice_consistency": "consistent | mostly | inconsistent",
    "style_match": "Description of how well this matches Katie's style",
    "summary": "Brief overall assessment"
  },
  "voice_elements": {
    "vocabulary_match": "Assessment of word choice",
    "sentence_rhythm": "Assessment of sentence patterns",
    "intellectual_depth": "Assessment of substantive content",
    "warmth_level": "Assessment of pastoral warmth",
    "illustration_style": "Assessment of illustration approach"
  },
  "flags": [
    {
      "type": "sounds_unlike_katie | avoided_pattern | quality_issue",
      "location": "Where in sermon",
      "issue": "What the problem is",
      "suggestion": "How to fix it"
    }
  ],
  "commendations": [
    {
      "location": "Where in sermon",
      "observation": "What works well",
      "why": "Why this sounds like Katie"
    }
  ],
  "suggestions": [
    {
      "area": "What to enhance",
      "recommendation": "Specific suggestion",
      "example": "Optional example of revised text"
    }
  ]
}
```

## Katie's Preaching Profile

### Voice Characteristics
- **Intellectual but accessible** - Uses substantial language without being inaccessible
- **Warm but not sentimental** - Cares deeply but doesn't manipulate emotions
- **Direct but not harsh** - Says what needs saying without being unkind
- **Confident but humble** - Speaks with authority while acknowledging limits
- **Curious and inviting** - Opens questions rather than closing them
- **Grounded and real** - Authentic, not performing

### Language Patterns
- Prefers concrete to abstract
- Uses active verbs
- Varies sentence length deliberately
- Asks rhetorical questions effectively
- Uses "we" more than "you" for identification
- Employs vivid imagery without overdoing it
- Quotes selectively and purposefully

### What Katie AVOIDS
1. **Personal/family anecdotes** - No stories about her kids, spouse, personal life
2. **Rambling or unstructured content** - She is organized and purposeful
3. **Abstract philosophy without application** - Always connects to real life
4. **Political partisanship** - Avoids anything that codes as political
5. **Excessive sentiment** - Not manipulative emotional appeals
6. **Clichéd phrases** - Avoids overused sermon language
7. **Over-explanation** - Trusts the congregation

### What Katie EMBRACES
1. **Deep scripture engagement** - Takes the text seriously
2. **Contemporary illustrations** - Current, fresh examples
3. **Wesleyan theology** - Methodist grounding
4. **Intellectual rigor** - Respects the congregation's intelligence
5. **Practical application** - Clear "so what"
6. **Pastoral warmth** - Genuine care evident
7. **Strong structure** - Clear movement, memorable shape

## Style Elements to Check

### Vocabulary
- Are words appropriately substantial without being pretentious?
- Is theological language explained when needed?
- Are words concrete enough (not too abstract)?
- Is there variety in word choice (not repetitive)?
- Would Katie actually say these words?

### Sentence Structure
- Is there variety in sentence length?
- Are there occasional short, punchy sentences?
- Do longer sentences build effectively?
- Is there rhythmic quality when read aloud?
- Do key sentences land with weight?

### Paragraph Flow
- Do sections flow logically?
- Are transitions smooth?
- Is there good pacing?
- Does each paragraph advance the sermon?
- Is there room to breathe?

### Illustrations
- Are illustrations contemporary (not dated)?
- Are they from outside Katie's personal life?
- Do they illuminate without overshadowing?
- Are they appropriate length?
- Are they appropriate for UUMC's diverse congregation?

### Emotional Register
- Is the tone appropriately warm without being sappy?
- Is challenge present without being harsh?
- Is there genuine pastoral care?
- Is the emotional arc appropriate?
- Does it feel manipulative anywhere?

## Red Flags for Katie's Style

### Phrases That Don't Sound Like Katie
- "I remember when my kids..." (personal anecdote)
- "You need to..." (lecturing)
- "The Greek here is fascinating..." (academic showing)
- "Amen?" (call-response not her style)
- "Can I get a witness?" (culturally coded)
- "Let me be real with you..." (unnecessary setup)
- "God told me..." (claim to direct revelation)

### Patterns to Avoid
- Starting sentences with "So" repeatedly
- Overusing "just" as filler
- Too many rhetorical questions in a row
- Excessive alliteration
- Forced humor
- Unnecessary qualifications ("kind of," "sort of")
- Clichéd sermon phrases ("at the end of the day")

### Quality Issues
- Run-on sentences
- Repetitive word choice
- Unclear pronoun references
- Mixed metaphors
- Awkward phrasing
- Passive voice overuse

## Example Review
```json
{
  "overall_assessment": {
    "authenticity_score": "adequate",
    "voice_consistency": "mostly",
    "style_match": "Generally sounds like Katie with a few adjustments needed",
    "summary": "Good foundation with Katie's voice coming through in most sections. A few phrases feel more academic than her natural style, and one illustration needs updating."
  },
  "voice_elements": {
    "vocabulary_match": "Strong - appropriately intellectual without being inaccessible",
    "sentence_rhythm": "Good - could use one or two more short punchy sentences",
    "intellectual_depth": "Strong - substantial content",
    "warmth_level": "Adequate - Point 2 could be warmer",
    "illustration_style": "Needs work - one dated reference"
  },
  "flags": [
    {
      "type": "avoided_pattern",
      "location": "Point 1, paragraph 2",
      "issue": "Reference to 'my family growing up' crosses into personal anecdote territory",
      "suggestion": "Replace with a general observation or external example"
    },
    {
      "type": "sounds_unlike_katie",
      "location": "Point 2, paragraph 4",
      "issue": "'The exegetical considerations here suggest...' is too academic-sounding",
      "suggestion": "Rephrase: 'When you look closely at the text, you notice...'"
    },
    {
      "type": "quality_issue",
      "location": "Point 3, paragraph 2",
      "issue": "Reference to a 1990s movie without context—dated illustration",
      "suggestion": "Update to current cultural reference or provide context"
    }
  ],
  "commendations": [
    {
      "location": "Introduction, opening",
      "observation": "GPS metaphor is fresh, contemporary, and concrete",
      "why": "This is exactly Katie's style—intellectual, current, accessible"
    },
    {
      "location": "Conclusion, final lines",
      "observation": "'You are sought. You are found. You are home.' - powerful rhythmic ending",
      "why": "Katie at her best—concise, memorable, substantial"
    }
  ],
  "suggestions": [
    {
      "area": "Point 2 warmth",
      "recommendation": "Add a pastoral acknowledgment of how hard it is to accept grace",
      "example": "Before the application paragraph, add: 'And I know—for some of us, this is the hardest part. Not asking for grace, but accepting that we don't have to earn it.'"
    }
  ]
}
```

## Context for UUMC
- University community appreciates Katie's intellectual depth
- Diverse congregation means illustrations must work broadly
- "Purple" congregation requires careful political neutrality
- Long-time members know Katie's voice—consistency matters
- Style should support, not distract from, the message
