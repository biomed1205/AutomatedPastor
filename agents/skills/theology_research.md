# Theology Research Skill

## Purpose
Research Wesleyan/United Methodist theological perspectives for sermon content. Ensures theological accuracy while making doctrine accessible and practical for contemporary preaching.

## Input Expectations
```json
{
  "theological_topic": "Doctrine or concept to research",
  "scripture_connection": "How this connects to the sermon text",
  "specific_questions": ["Optional questions to address"],
  "depth_level": "overview | moderate | deep"
}
```

## Output Format
```json
{
  "topic": "Theological concept researched",
  "definition": {
    "simple": "One-sentence accessible definition",
    "fuller": "More complete theological definition",
    "technical": "Academic/doctrinal language if needed"
  },
  "wesleyan_perspective": {
    "wesleys_teaching": "What John Wesley taught",
    "key_texts": ["Wesley's writings on this topic"],
    "quadrilateral_emphasis": "How Wesley approached this through Scripture, tradition, reason, experience"
  },
  "methodist_distinctives": {
    "what_makes_this_methodist": "How Methodist view differs from other traditions",
    "comparison": {
      "calvinist_view": "Brief comparison if relevant",
      "catholic_view": "Brief comparison if relevant",
      "other": "Other relevant comparisons"
    },
    "contemporary_umc": "Current United Methodist teaching"
  },
  "scripture_connections": [
    {
      "reference": "Scripture passage",
      "connection": "How this supports/illustrates the doctrine"
    }
  ],
  "practical_implications": [
    {
      "doctrine": "Theological point",
      "so_what": "What this means for daily life",
      "sermon_angle": "How to present this in preaching"
    }
  ],
  "accessible_explanations": [
    {
      "concept": "Complex theological idea",
      "analogy": "Accessible way to explain it",
      "caution": "What the analogy doesn't capture"
    }
  ],
  "common_misunderstandings": [
    {
      "error": "What people often get wrong",
      "correction": "The accurate understanding",
      "gentle_approach": "How to correct without condescension"
    }
  ],
  "hymn_connections": [
    {
      "hymn": "Hymn title and author",
      "line": "Relevant lyric",
      "connection": "How it expresses this theology"
    }
  ]
}
```

## Constraints and Guidelines
- Always ground in Wesleyan/Methodist tradition
- Make doctrine accessible without dumbing down
- Connect head knowledge to heart and hands
- Use the Wesleyan Quadrilateral as framework
- Reference United Methodist doctrinal standards
- Include hymn connections when appropriate (Methodist heritage)
- Avoid partisan political applications
- Note areas of ongoing theological discussion in UMC
- Consider post-2024 General Conference context for UMC

## Core Wesleyan Doctrines to Know
- **Prevenient Grace** - God's grace that goes before, enabling response
- **Justifying Grace** - Forgiveness and new relationship with God
- **Sanctifying Grace** - Growth in holiness, "going on to perfection"
- **Christian Perfection** - Perfect love, not sinlessness
- **Personal & Social Holiness** - Individual and communal transformation
- **The Wesleyan Quadrilateral** - Scripture, tradition, reason, experience
- **Means of Grace** - Practices that convey grace (Lord's Supper, prayer, etc.)
- **Universal Atonement** - Christ died for all, not just elect
- **Free Will** - Human capacity to respond to grace
- **Assurance** - The witness of the Spirit

## Doctrinal Resources
- Wesley's Sermons (especially the Standard 44)
- Wesley's Notes on the New Testament
- United Methodist Book of Discipline
- United Methodist Articles of Religion
- Confession of Faith (EUB)
- This Holy Mystery (UMC Communion theology)
- By Water and the Spirit (UMC Baptism theology)

## Example Output Snippet
```json
{
  "topic": "Prevenient Grace",
  "definition": {
    "simple": "God's love reaching us before we even know to look for God.",
    "fuller": "The grace that 'comes before' our awareness or response, enabling us to hear and respond to the gospel. God's initiative that makes human response possible."
  },
  "wesleyan_perspective": {
    "wesleys_teaching": "Wesley taught that all people receive prevenient grace, which restores enough free will to respond to God. This is how Wesley navigated between Calvinist predestination and Pelagian self-salvation.",
    "key_texts": ["Sermon 85: 'On Working Out Our Own Salvation'", "Sermon 43: 'The Scripture Way of Salvation'"]
  },
  "accessible_explanations": [
    {
      "concept": "Prevenient grace enables free will",
      "analogy": "Like a lifeguard swimming out to a drowning person. The person can't save themselves, but once the lifeguard reaches them, they can choose to grab hold or resist. The lifeguard's action (prevenient grace) makes the choice possible.",
      "caution": "Doesn't fully capture that grace continues throughout—not just initial rescue"
    }
  ]
}
```

## Context for UUMC
- Congregation includes theological diversity
- Some members deeply versed in Methodist tradition
- Some newer to Methodist theology
- University context appreciates intellectual rigor
- Post-2024 UMC—remaining in denomination
- "Purple" congregation—theology must not feel partisan
