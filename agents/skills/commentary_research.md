# Commentary Research Skill

## Purpose
Gather insights from trusted biblical commentaries and scholarly sources. Synthesizes multiple perspectives to inform sermon preparation while prioritizing Wesleyan/Methodist voices.

## Input Expectations
```json
{
  "scripture_reference": "Book Chapter:Verse-Verse",
  "specific_questions": ["Optional list of specific questions to research"],
  "focus_areas": ["Optional: historical, theological, practical, etc."]
}
```

## Output Format
```json
{
  "passage": "Scripture reference researched",
  "commentary_synthesis": {
    "consensus_view": "What most scholars agree on",
    "key_insights": [
      {
        "source": "Commentary/author name",
        "insight": "Notable observation or interpretation",
        "relevance": "Why this matters for preaching"
      }
    ],
    "differing_views": [
      {
        "position_a": "One interpretation",
        "position_b": "Alternative interpretation",
        "evaluation": "Assessment of each for preaching"
      }
    ]
  },
  "wesleyan_perspective": {
    "wesleys_view": "What John/Charles Wesley said if applicable",
    "methodist_tradition": "How Methodist tradition has interpreted",
    "contemporary_methodist": "Modern Methodist scholarly views"
  },
  "practical_applications": [
    {
      "insight": "Commentary observation",
      "application": "How this translates to modern application",
      "illustration_potential": "Could this lead to an illustration?"
    }
  ],
  "sermon_resources": {
    "quotes_to_consider": ["Notable quotable lines from commentators"],
    "cautions": ["What to be careful about in preaching this"],
    "recommended_emphasis": "Suggested primary focus based on research"
  }
}
```

## Constraints and Guidelines
- Prioritize Wesleyan/Methodist commentary sources
- Include both classic and contemporary voices
- Balance academic insight with pastoral applicability
- Note where scholarly consensus exists vs. where views differ
- Flag any controversial interpretations
- Avoid obscure academic debates not relevant to preaching
- Synthesize, don't just list—provide evaluative summary
- Consider what's appropriate for UUMC's educated, diverse congregation

## Trusted Commentary Sources

### Primary (Wesleyan/Methodist)
- Wesley's Notes on the Old and New Testament
- Asbury Bible Commentary
- New Interpreter's Bible (United Methodist)
- Wesley One Volume Commentary

### Scholarly
- Word Biblical Commentary
- Anchor Bible Commentary
- New International Commentary series
- Interpretation Commentary series
- Sacra Pagina (Catholic, good ecumenical perspective)

### Practical/Preaching
- Feasting on the Word
- Connections (Westminster John Knox)
- The New Interpreter's Handbook of Preaching

## Example Output Snippet
```json
{
  "passage": "Luke 15:11-32",
  "consensus_view": "The parable addresses God's extravagant grace and the danger of self-righteous resentment. Most scholars agree the elder brother represents religious insiders who resist grace for outsiders.",
  "wesleyan_perspective": {
    "wesleys_view": "Wesley emphasized both the father's prevenient grace (running to meet the son) and the son's responsive faith (coming to himself). Classic example of divine initiative and human response working together.",
    "methodist_tradition": "Methodist tradition has used this parable to emphasize that no one is beyond the reach of grace, connecting to the Wesleyan doctrine of universal atonement."
  },
  "quotes_to_consider": [
    "The father's love is not careful or calculating but extravagant and scandalous. - Henri Nouwen",
    "This is not a parable about a prodigal son but about a prodigal father—one who is 'wasteful' with his love. - Timothy Keller"
  ]
}
```

## Context for UUMC
- Congregation values intellectual depth
- Include ecumenical perspectives (not just Protestant)
- Connect to Methodist heritage when possible
- Avoid commentary debates that don't serve the sermon
- Pastor Katie appreciates scholarly grounding
