# Theme Extractor Skill

## Purpose
Extract and identify sermon themes from scripture passages. Analyzes the text to find the central theological ideas, narrative threads, and preachable themes that can become the sermon's focus.

## Input Expectations
```json
{
  "scripture": "The passage to analyze",
  "lectionary_context": "Optional related readings for the day",
  "liturgical_season": "Optional season context (Advent, Lent, etc.)",
  "congregation_context": "Current congregational needs or situations",
  "previous_sermons": "Optional recent sermon themes to avoid repetition"
}
```

## Output Format
```json
{
  "passage_overview": {
    "reference": "Scripture reference",
    "genre": "Narrative, epistle, poetry, etc.",
    "context": "Brief situational context"
  },
  "primary_themes": [
    {
      "theme": "Theme name",
      "description": "What this theme means",
      "textual_basis": "Where this appears in the passage",
      "big_idea_possibility": "Potential one-sentence sermon focus",
      "relevance_score": "high | medium | low",
      "preachability": "How easily this translates to sermon",
      "wesleyan_connection": "Connection to Methodist theology"
    }
  ],
  "secondary_themes": [
    {
      "theme": "Theme name",
      "description": "Brief description",
      "notes": "Why this is secondary, or when it might be primary"
    }
  ],
  "theme_connections": {
    "lectionary_harmony": "How themes connect to other readings",
    "seasonal_fit": "How themes fit liturgical season",
    "congregational_timeliness": "Current relevance for UUMC"
  },
  "recommended_focus": {
    "theme": "Recommended primary theme",
    "big_idea": "One-sentence sermon focus",
    "rationale": "Why this is the recommended focus",
    "alternative": "Strong alternative if preferred"
  }
}
```

## Theme Extraction Process

### Step 1: Literary Analysis
- What type of literature is this?
- What's the narrative arc or argument flow?
- What words/images repeat or stand out?
- What tension or problem does the text address?

### Step 2: Theological Identification
- What does this reveal about God?
- What does this reveal about humanity?
- What does this reveal about salvation/grace?
- What does this reveal about faithful living?

### Step 3: Contextual Filtering
- What themes fit this congregation?
- What themes fit this season?
- What themes haven't been preached recently?
- What themes speak to current moment?

### Step 4: Preachability Assessment
- Can this be clearly stated?
- Can this be illustrated?
- Can this be applied?
- Will this make a difference?

## Theme Categories

### God's Nature
- Grace (prevenient, justifying, sanctifying)
- Love (steadfast, unconditional, pursuing)
- Faithfulness (covenant keeping, reliable)
- Holiness (other, pure, calling us higher)
- Presence (with us, Emmanuel, accessible)

### Human Condition
- Sin and brokenness
- Searching and longing
- Pride and self-reliance
- Fear and anxiety
- Need for grace

### Gospel Response
- Faith and trust
- Repentance and turning
- Transformation and sanctification
- Community and belonging
- Mission and sending

### Kingdom Living
- Justice and mercy
- Compassion and service
- Hospitality and welcome
- Sacrifice and generosity
- Hope and perseverance

## Constraints and Guidelines

### Do's
- Let the text speak (don't impose themes)
- Consider multiple valid themes
- Connect to Wesleyan distinctives when natural
- Consider seasonal and contextual factors
- Identify themes that make a difference
- Look for what's surprising in the text

### Don'ts
- Don't force themes onto unwilling texts
- Don't miss the obvious for the clever
- Don't choose themes just because they're familiar
- Don't ignore the text's original meaning
- Don't choose themes that don't lead to application
- Don't repeat recent sermon themes unnecessarily

## Example Output
```json
{
  "passage_overview": {
    "reference": "Luke 15:11-32",
    "genre": "Parable/Narrative",
    "context": "Jesus responding to Pharisees' criticism of his table fellowship with sinners"
  },
  "primary_themes": [
    {
      "theme": "Prevenient Grace",
      "description": "God's grace that goes before us, seeking us before we seek God",
      "textual_basis": "The father watching for the son, running to meet him before son can finish his speech",
      "big_idea_possibility": "God's grace runs to meet us before we can earn our way home",
      "relevance_score": "high",
      "preachability": "Excellent—visual image, clear application, Wesleyan distinctiveness",
      "wesleyan_connection": "Core Wesleyan doctrine; Wesley's emphasis on grace that enables response"
    },
    {
      "theme": "Radical Forgiveness",
      "description": "Forgiveness that exceeds what is deserved or expected",
      "textual_basis": "Father's lavish restoration without conditions or probation",
      "big_idea_possibility": "God's forgiveness is lavish, not transactional",
      "relevance_score": "high",
      "preachability": "Good—emotionally powerful, but need to avoid sentiment without substance"
    },
    {
      "theme": "Religious Resentment",
      "description": "The danger of religious people resisting grace for 'unworthy' others",
      "textual_basis": "Elder brother's refusal to celebrate; Pharisee context",
      "big_idea_possibility": "Our greatest barrier to grace might be our own righteousness",
      "relevance_score": "high",
      "preachability": "Challenging—might make religious people uncomfortable (which may be good)"
    }
  ],
  "secondary_themes": [
    {
      "theme": "Consequences of Sin",
      "description": "Choices have real consequences even when forgiveness comes",
      "notes": "Present in the text but not the focus; could be over-moralized"
    },
    {
      "theme": "Coming to Yourself",
      "description": "The moment of self-awareness and return",
      "notes": "Interesting entry point, but small part of the story"
    }
  ],
  "recommended_focus": {
    "theme": "Prevenient Grace",
    "big_idea": "God's grace runs to meet us before we can earn our way home",
    "rationale": "Distinctive Wesleyan emphasis, vivid imagery (father running), immediate application (stop trying to earn it), and addresses both those far from God and those long in church",
    "alternative": "Religious Resentment could work if congregation tends toward older-brother syndrome"
  }
}
```

## Context for UUMC
- Wesleyan themes resonate with this congregation
- Educated laity appreciate nuanced theme development
- "Purple" congregation—choose themes that unite, not divide
- Balance comfort and challenge
- Consider who's in the room and what they need
