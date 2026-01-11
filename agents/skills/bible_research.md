# Bible Research Skill

## Purpose
Deep scripture study and exegesis for sermon preparation. Provides comprehensive biblical analysis including original language insights, literary context, historical background, and theological significance.

## Input Expectations
```json
{
  "scripture_reference": "Book Chapter:Verse-Verse (e.g., 'Romans 8:28-30')",
  "sermon_focus": "Optional specific angle or question to explore",
  "lectionary_context": "Optional related readings for the day"
}
```

## Output Format
```json
{
  "passage": {
    "reference": "Full scripture reference",
    "text_nrsv": "NRSV translation",
    "text_alternate": "Alternative translation for comparison"
  },
  "literary_analysis": {
    "genre": "Type of literature (narrative, epistle, poetry, etc.)",
    "structure": "Outline of the passage",
    "key_terms": [
      {
        "english": "English word",
        "original": "Greek/Hebrew term",
        "meaning": "Expanded meaning and nuance"
      }
    ],
    "rhetorical_devices": "Any notable literary features"
  },
  "context": {
    "immediate": "Surrounding verses/chapter context",
    "book": "How this fits in the larger book",
    "canonical": "Connection to broader biblical narrative",
    "historical": "Historical setting and audience"
  },
  "theological_themes": [
    {
      "theme": "Major theme identified",
      "development": "How the passage develops this theme",
      "wesleyan_connection": "Connection to Wesleyan theology"
    }
  ],
  "interpretive_challenges": [
    {
      "issue": "Difficult aspect of the text",
      "approaches": "How scholars have addressed it",
      "recommendation": "Suggested approach for preaching"
    }
  ],
  "preaching_angles": [
    {
      "focus": "Potential sermon focus",
      "big_idea": "One-sentence summary",
      "congregational_relevance": "Why this matters to UUMC"
    }
  ]
}
```

## Constraints and Guidelines
- Use NRSV as primary translation (United Methodist standard)
- Include original language insights but keep accessible
- Connect to Wesleyan theological tradition where appropriate
- Consider the text's use in Methodist hymnody and tradition
- Identify any sensitive or controversial aspects that need care
- Note connections to lectionary readings if applicable
- Avoid overly academic language; keep practical for preaching
- Consider how the text speaks to University UMC's context

## Research Sources to Consider
- Scholarly commentaries (Anchor Bible, Word Biblical, etc.)
- Wesleyan/Methodist commentaries when available
- Wesley's Notes on the New/Old Testament
- Original language resources (BDAG, HALOT)
- Historical and cultural background resources

## Example Output Snippet
```json
{
  "passage": {
    "reference": "Romans 8:28",
    "text_nrsv": "We know that all things work together for good for those who love God, who are called according to his purpose."
  },
  "key_terms": [
    {
      "english": "work together",
      "original": "synergei (συνεργεῖ)",
      "meaning": "Collaborative action; God working alongside, not overriding human agency. Connects to Wesleyan emphasis on divine-human cooperation in salvation."
    }
  ],
  "wesleyan_connection": "Wesley's emphasis on prevenient grace—God's initiative that enables human response—illuminates how 'all things working together' is not fatalism but divine-human partnership."
}
```

## Context for UUMC
- Pastor Katie values deep scripture engagement
- Congregation includes educated laity who appreciate depth
- "Purple" congregation—avoid politically charged interpretations
- University community appreciates intellectual rigor
- Balance academic insight with pastoral accessibility
