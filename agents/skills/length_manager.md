# Length Manager Skill

## Purpose
Manage sermon word count to stay within 2,000-2,500 words (approximately 15 minutes spoken). Helps allocate words across sections, identify areas that are too long or too short, and suggest cuts or expansions while preserving sermon integrity.

## Input Expectations
```json
{
  "current_content": "The sermon draft or section to evaluate",
  "section": "introduction | point_1 | point_2 | point_3 | conclusion | full",
  "target_length": "Target word count for this section or full sermon",
  "priority_content": ["List of elements that MUST stay"],
  "optional_content": ["List of elements that COULD be cut"]
}
```

## Output Format
```json
{
  "analysis": {
    "current_word_count": "Actual word count",
    "target_word_count": "Target word count",
    "status": "under | on-target | over",
    "difference": "How many words over/under"
  },
  "section_breakdown": {
    "introduction": {
      "current": "Word count",
      "target": "Suggested count",
      "status": "Assessment"
    }
  },
  "recommendations": {
    "cuts": [
      {
        "section": "Where to cut",
        "content": "What to cut",
        "words_saved": "How many words",
        "impact": "What's lost",
        "priority": "high | medium | low"
      }
    ],
    "expansions": [
      {
        "section": "Where to expand",
        "suggestion": "What to add",
        "words_added": "How many words",
        "benefit": "What's gained"
      }
    ]
  },
  "revised_content": "Optional revised version at target length"
}
```

## Target Word Counts

### Full Sermon: 2,000-2,500 words (15 minutes)

| Section | Target Words | Target Time | Range |
|---------|-------------|-------------|-------|
| Introduction | 200-300 | 1:30-2:00 | 150-350 |
| Point 1 | 500-600 | 4:00-5:00 | 450-700 |
| Point 2 | 500-600 | 4:00-5:00 | 450-700 |
| Point 3 | 400-500 | 3:00-4:00 | 350-550 |
| Conclusion | 200-300 | 1:30-2:00 | 150-350 |
| **Total** | **2,000-2,500** | **15:00** | **1,800-2,700** |

### Speaking Rate
- Average speaking rate: 130-150 words per minute
- Katie's style: Approximately 140 words per minute
- 15 minutes = ~2,100 words at 140 wpm

## Where to Cut (Priority Order)

### High Priority Cuts (Little Impact)
1. **Redundancy** - Saying the same thing twice differently
2. **Overexplanation** - Explaining what's already clear
3. **Excessive hedging** - "I think maybe perhaps it might be..."
4. **Filler phrases** - "As I was saying," "It's interesting that..."
5. **Too many examples** - One good illustration beats three okay ones

### Medium Priority Cuts (Some Impact)
1. **Secondary points** - Ideas that support but aren't essential
2. **Historical background** - Only keep what's necessary for meaning
3. **Greek/Hebrew details** - One key insight, not three
4. **Extended quotes** - Paraphrase or shorten
5. **Third illustration** - If you have three, cut one

### Low Priority Cuts (Consider Carefully)
1. **Primary scripture exposition** - Core of the sermon
2. **Main illustration per point** - Needed for connection
3. **Central application** - What people are supposed to do
4. **Opening hook** - First impression matters
5. **Conclusion summary** - People need the landing

## Where to Expand (If Under Target)

### High Value Additions
1. **Scripture exposition** - Deepen engagement with text
2. **Illustration** - Add concrete example
3. **Application specifics** - Make it more actionable
4. **Transition development** - Smoother flow

### Medium Value Additions
1. **Theological depth** - Wesleyan connection
2. **Pastoral aside** - Compassionate acknowledgment
3. **Contemporary relevance** - Current application
4. **Question/reflection** - Invites engagement

### Avoid Adding
1. **More points** - Don't add a fourth point
2. **Tangents** - Stay focused
3. **Padding** - Empty words to fill space
4. **Excessive quotes** - Don't outsource the message

## Cutting Techniques

### Sentence-Level Cuts
- Remove adverbs: "really, very, just, actually, simply"
- Remove throat-clearing: "I want to share, Let me tell you"
- Convert passive to active: "was given" → "gave"
- Combine sentences: Two short ones → one clear one

### Paragraph-Level Cuts
- Ask: Does this advance the sermon?
- Ask: Have I already said this differently?
- Ask: Will anyone miss this?
- Ask: Is this for them or for me?

### Section-Level Cuts
- Ask: Is this point essential to the big idea?
- Ask: Could another point absorb this?
- Ask: What's the minimum needed for clarity?

## Example Analysis
```json
{
  "analysis": {
    "current_word_count": 2847,
    "target_word_count": 2250,
    "status": "over",
    "difference": "+597 words (need to cut ~25%)"
  },
  "section_breakdown": {
    "introduction": {
      "current": 412,
      "target": 250,
      "status": "Over by 162 - cut the extended setup"
    },
    "point_1": {
      "current": 723,
      "target": 550,
      "status": "Over by 173 - two illustrations, keep one"
    },
    "point_2": {
      "current": 689,
      "target": 550,
      "status": "Over by 139 - Greek exposition too long"
    },
    "point_3": {
      "current": 598,
      "target": 450,
      "status": "Over by 148 - application could tighten"
    },
    "conclusion": {
      "current": 425,
      "target": 250,
      "status": "Over by 175 - re-preaching instead of landing"
    }
  },
  "recommendations": {
    "cuts": [
      {
        "section": "Introduction",
        "content": "Extended historical background on Pharisees",
        "words_saved": 85,
        "impact": "Low - congregation knows enough context",
        "priority": "high"
      },
      {
        "section": "Point 1",
        "content": "Second illustration (the chess analogy)",
        "words_saved": 120,
        "impact": "Medium - GPS illustration sufficient",
        "priority": "high"
      },
      {
        "section": "Point 2",
        "content": "Comparison of three Greek terms",
        "words_saved": 95,
        "impact": "Low - one term insight is enough",
        "priority": "high"
      },
      {
        "section": "Conclusion",
        "content": "Re-summarizing each point",
        "words_saved": 150,
        "impact": "Medium - trust what was said",
        "priority": "medium"
      }
    ]
  }
}
```

## Context for UUMC
- 15 minutes is the target—congregation expects this
- Better to be slightly under than over
- Depth matters more than breadth
- Trust the congregation to track—don't over-explain
- Katie's style: lean and substantial
