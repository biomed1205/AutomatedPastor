# Congregation Context Skill

## Purpose
Research and apply University UMC Baton Rouge specific context to sermon content. Ensures sermons speak directly to this congregation's life, needs, culture, and situation.

## Input Expectations
```json
{
  "sermon_topic": "The topic or theme being addressed",
  "scripture": "The text being preached",
  "questions": ["Specific contextual questions to research"],
  "current_events": "Any timely considerations"
}
```

## Output Format
```json
{
  "congregation_profile": {
    "summary": "Brief reminder of who UUMC is",
    "relevant_demographics": "Aspects relevant to this sermon",
    "current_season": "What the congregation is experiencing now"
  },
  "sermon_application": {
    "direct_connections": [
      {
        "sermon_point": "Point from the sermon",
        "uumc_application": "How this applies specifically here",
        "language_suggestions": "Words/phrases that resonate"
      }
    ],
    "potential_sensitivities": [
      {
        "issue": "Something to be careful about",
        "reason": "Why this needs care",
        "approach": "How to handle it"
      }
    ]
  },
  "local_illustrations": [
    {
      "topic": "Local reference opportunity",
      "details": "Specific Baton Rouge/LSU/Louisiana content",
      "usage": "How to incorporate appropriately"
    }
  ],
  "pastoral_considerations": {
    "who_needs_to_hear_this": ["Groups in congregation this especially speaks to"],
    "who_might_struggle": ["Groups who might find this difficult"],
    "pastoral_adjustments": "How to care for both groups"
  },
  "avoid_for_this_congregation": [
    {
      "what": "Something to avoid",
      "why": "Reason it wouldn't work here"
    }
  ],
  "enhance_for_this_congregation": [
    {
      "what": "Something to emphasize",
      "why": "Reason it would resonate here"
    }
  ]
}
```

## Congregation Profile: University UMC Baton Rouge

### Identity
- **Location:** Baton Rouge, Louisiana, near LSU campus
- **Character:** University-connected, intellectually engaged, welcoming
- **Politics:** "Purple" congregation—diverse political views, averse to partisanship
- **Denomination:** United Methodist, remaining post-2024 General Conference
- **Posture:** Open, welcoming, theologically moderate-to-progressive

### Demographics
- Mix of university-connected and long-time community members
- Range of ages with significant older adult population
- Educated congregation; appreciates intellectual rigor
- Some lifelong Methodists, some from other traditions
- Some exploring faith, some deeply rooted
- LGBTQ+ affirming posture

### Values
- Intellectual integrity in faith
- Hospitality and welcome
- Social justice engagement
- Methodist heritage and tradition
- Community connection
- Musical excellence (strong choir tradition)

### Current Context
- Post-2024 General Conference—chose to remain UMC
- Processing denominational changes while staying focused on mission
- Navigating cultural polarization while maintaining unity
- University community rhythms (semester breaks, football season, etc.)
- Louisiana-specific challenges (hurricanes, economy, environment)

### Pastor Katie
- 43-year-old female senior pastor
- Intellectual, rigorous preaching style
- Values depth over sentiment
- Avoids personal/family anecdotes
- Wesleyan theological grounding
- Committed to accessible excellence

## Constraints and Guidelines
- Always respect the "purple" character—no partisan politics
- Remember this is a welcoming, affirming congregation
- Balance challenge and comfort
- Honor long-time members while welcoming newcomers
- Consider university calendar and culture
- Include but don't over-rely on local references
- Note when something might land differently here than elsewhere
- Consider who's in the room on any given Sunday

## Local Context to Draw From
- LSU and university culture
- Baton Rouge community
- Louisiana culture and history
- Gulf South regional identity
- Hurricane seasons and recovery
- Local Methodist history
- Mississippi River and Louisiana landscape

## Example Output Snippet
```json
{
  "sermon_point": "Finding identity in Christ rather than achievements",
  "uumc_application": "In a university community where achievement is highly valued—publications, tenure, grades, research—this message both challenges and liberates. Many here have built identity on academic or professional success. The gospel offers freedom from that pressure while not dismissing the value of their work.",
  "language_suggestions": "Avoid language that sounds anti-intellectual. Frame it as 'our worth isn't determined by our CV' rather than 'worldly achievements don't matter.' This congregation values excellence—help them see it as offering, not identity.",
  "pastoral_considerations": {
    "who_needs_to_hear_this": ["Tenure-track faculty under pressure", "Students anxious about grades", "Retirees wondering if their value diminished"],
    "who_might_struggle": ["Those whose achievements are their primary source of self-worth", "High achievers who might hear this as criticism"]
  }
}
```

## Seasonal Considerations
- **Fall Semester:** New students, football season, fresh energy
- **Advent/Christmas:** Strong musical traditions, community gatherings
- **Spring Semester:** Mardi Gras (unique Louisiana consideration), Lent, Easter
- **Summer:** Slower pace, smaller attendance, long-time members
- **Hurricane Season:** Anxiety, potential evacuations, community care
