# Tone Adjuster Skill

## Purpose
Adjust sermon tone to match the content, occasion, and congregational needs. Ensures the sermon's emotional register is appropriate—not too heavy, not too light, not too academic, not too casual. Helps the sermon sound like Katie while serving the specific moment.

## Input Expectations
```json
{
  "content": "The sermon content to adjust",
  "current_tone": "Assessment of current tone",
  "target_tone": "Desired tone",
  "occasion": "Regular Sunday | funeral | wedding | special service",
  "liturgical_context": "Season or special day",
  "congregation_state": "What the congregation is experiencing"
}
```

## Output Format
```json
{
  "tone_analysis": {
    "current_assessment": "Description of current tone",
    "target_tone": "Desired tone",
    "gap": "What needs to shift",
    "risks": "What to watch for in adjustment"
  },
  "adjustments": [
    {
      "section": "Where to adjust",
      "current_phrase": "Current wording",
      "adjusted_phrase": "Revised wording",
      "rationale": "Why this change"
    }
  ],
  "overall_guidance": {
    "word_choices": "Language patterns to use/avoid",
    "sentence_rhythm": "How sentences should feel",
    "emotional_arc": "How tone should shift through sermon",
    "delivery_notes": "How to embody this tone in delivery"
  },
  "revised_content": "Optional revised version with adjusted tone"
}
```

## Tone Spectrum

### Challenging
- Direct address of hard truths
- Prophetic edge without condemnation
- High expectations, clear calls to action
- Use for: Sin, repentance, justice, transformation

### Pastoral
- Warm, caring, understanding
- Acknowledges struggle and pain
- Grace-forward, permission-giving
- Use for: Suffering, grief, anxiety, failure

### Celebratory
- Joyful, affirming, grateful
- Upbeat without being shallow
- Thanksgiving and praise
- Use for: Easter, celebrations, victories

### Reflective
- Thoughtful, contemplative, questioning
- Space for mystery and uncertainty
- Slower pace, deeper waters
- Use for: Lent, complex texts, big questions

### Hopeful
- Forward-looking, encouraging
- Acknowledges reality while pointing beyond it
- Resilient but not naive
- Use for: Advent, new beginnings, despair

### Teaching
- Clear, explanatory, accessible
- Intellectually engaging but warm
- Building understanding step by step
- Use for: Doctrine, difficult texts, new concepts

## Tone Pitfalls to Avoid

### Too Academic
**Signs:** Excessive jargon, long sentences, third-person distance
**Fix:** Use second person ("you"), shorten sentences, add stories

### Too Casual
**Signs:** Slang, overly informal, lacks gravity
**Fix:** Elevate key moments, use Scripture language, add weight

### Too Heavy
**Signs:** All challenge no grace, guilt-inducing, exhausting
**Fix:** Add permission-giving phrases, acknowledge difficulty, offer rest

### Too Light
**Signs:** Shallow, avoids difficulty, all comfort no challenge
**Fix:** Name the hard things, add specific applications, take sin seriously

### Too Preachy
**Signs:** Lecturing, condescending, know-it-all tone
**Fix:** Use "we" not "you," acknowledge own struggle, ask questions

### Too Emotional
**Signs:** Manipulative, sentimentality, tear-jerking
**Fix:** Trust the content, reduce dramatic language, let facts speak

## Tone-Shifting Techniques

### Warming the Tone
- Add personal pronouns ("we," "you," "us")
- Shorten sentences
- Add concrete details
- Include grace notes ("this is hard," "you're not alone")
- Use questions rather than declarations

### Sharpening the Tone
- Add direct statements
- Use Scripture language
- Be specific about what's at stake
- Remove hedging words
- Let silences speak

### Calming the Tone
- Slow the rhythm (longer sentences)
- Add reflective questions
- Include pauses in delivery
- Use gentle imperatives ("consider," "notice")
- Add space for uncertainty

### Elevating the Tone
- Use parallel structure
- Draw from hymn language
- Include poetic phrases
- Add biblical cadence
- Trust bigger words occasionally

## Example Analysis
```json
{
  "tone_analysis": {
    "current_assessment": "Too academic and distant—sounds like a lecture",
    "target_tone": "Pastoral with teaching elements",
    "gap": "Need more warmth, more 'we,' more acknowledgment of difficulty",
    "risks": "Could swing too far into sentimental"
  },
  "adjustments": [
    {
      "section": "Introduction",
      "current_phrase": "The parable in Luke 15 demonstrates the theological concept of prevenient grace in the Wesleyan tradition.",
      "adjusted_phrase": "There's a detail in today's story that changes everything. And once you see it, you'll never read this parable the same way again.",
      "rationale": "Move from lecture to invitation, create curiosity, use accessible language"
    },
    {
      "section": "Point 2",
      "current_phrase": "The Greek word 'esplagchnisthe' indicates visceral compassion.",
      "adjusted_phrase": "The Greek here describes something that hits you in the gut. 'Esplagchnisthe'—a word you feel in your stomach. This wasn't polite sympathy. The father's whole body responded.",
      "rationale": "Keep the insight but make it embodied and accessible"
    },
    {
      "section": "Application",
      "current_phrase": "Therefore, one ought to practice receptivity to grace.",
      "adjusted_phrase": "So maybe this week, the invitation isn't to do more—it's to stop performing. To let yourself be found. To let grace catch up with you.",
      "rationale": "Shift from obligation to invitation, use second person, make it livable"
    }
  ],
  "overall_guidance": {
    "word_choices": "Replace 'one' with 'you/we.' Reduce '-tion' words. Use verbs instead of nouns (not 'reconciliation' but 'reconcile').",
    "sentence_rhythm": "Vary length. Short sentence. Then a slightly longer one that builds. Then land with something memorable.",
    "emotional_arc": "Start curious, build tension in Point 2, warm and hopeful in conclusion.",
    "delivery_notes": "Slow down in the pastoral moments. Let the hard truths have space. Smile at the hope."
  }
}
```

## Katie's Voice Characteristics
- Intellectual without being inaccessible
- Warm but not sentimental
- Direct without being harsh
- Confident but humble
- Challenging and grace-filled
- Substantial, not fluffy

## Context for UUMC
- Educated congregation handles sophisticated tone
- "Purple" church—avoid partisan-sounding language
- Multi-generational—balance accessibility with depth
- Welcoming posture—tone should include, not exclude
- University context—intellectual rigor appreciated
