# Theological Reviewer Skill

## Purpose
Review sermon content for theological accuracy, especially alignment with Wesleyan/United Methodist doctrine. Identifies theological errors, missed opportunities, and areas needing clarification while honoring the sermon's pastoral purpose.

## Input Expectations
```json
{
  "sermon_content": "The sermon draft to review",
  "scripture": "The text being preached",
  "stated_theme": "The sermon's intended big idea",
  "review_depth": "light | standard | thorough",
  "specific_concerns": ["Optional specific areas to check"]
}
```

## Output Format
```json
{
  "overall_assessment": {
    "theological_soundness": "strong | adequate | concerns | problematic",
    "wesleyan_alignment": "strong | adequate | needs_attention",
    "scriptural_faithfulness": "strong | adequate | concerns",
    "summary": "Brief overall assessment"
  },
  "commendations": [
    {
      "location": "Where in sermon",
      "observation": "What's theologically strong",
      "why_it_matters": "Significance"
    }
  ],
  "concerns": [
    {
      "severity": "critical | significant | minor",
      "location": "Where in sermon",
      "issue": "What the concern is",
      "theological_basis": "Why this is a concern",
      "suggestion": "How to address it"
    }
  ],
  "missed_opportunities": [
    {
      "area": "What could be enhanced",
      "suggestion": "How to strengthen theologically",
      "benefit": "What this would add"
    }
  ],
  "wesleyan_check": {
    "grace_emphasized": "Assessment of grace theology",
    "quadrilateral_balance": "Scripture, tradition, reason, experience",
    "personal_social_holiness": "Both dimensions present?",
    "methodist_distinctives": "Any missed opportunities for Methodist emphasis"
  }
}
```

## Theological Review Categories

### Scripture Interpretation
- Does the sermon reflect the text's actual meaning?
- Is the text used in context?
- Are difficult passages handled responsibly?
- Is the interpretation scholarly defensible?
- Are there problematic proof-texting issues?

### Doctrine of God
- Is God portrayed accurately (loving, just, holy, present)?
- Is the Trinity honored where relevant?
- Is God's sovereignty balanced with human agency?
- Is God's love not made sentimental?
- Is God's justice not made harsh?

### Christology
- Is Jesus portrayed accurately?
- Is the incarnation honored?
- Is the atonement handled responsibly?
- Is the resurrection appropriately central?
- Is Jesus as present Lord, not just historical figure?

### Soteriology (Salvation)
- Is grace emphasized appropriately?
- Is the Wesleyan order of salvation respected?
- Is works-righteousness avoided?
- Is cheap grace avoided?
- Is universal atonement implied (Methodist distinctive)?

### Anthropology
- Is human sinfulness acknowledged?
- Is human worth affirmed?
- Is human agency honored (vs. fatalism)?
- Is the image of God emphasized?
- Are generalizations about "all people" warranted?

### Ecclesiology
- Is the church portrayed positively?
- Is community emphasized appropriately?
- Is Methodist tradition honored where relevant?
- Is the church's mission reflected?

### Eschatology
- Is hope present and grounded?
- Is the kingdom already/not-yet balanced?
- Are death and resurrection handled pastorally?
- Is triumphalism avoided?

## Wesleyan Distinctives to Check

### The Order of Salvation
1. **Prevenient Grace** - God's grace that goes before
2. **Convincing Grace** - Awareness of sin and need
3. **Justifying Grace** - Forgiveness and new relationship
4. **Sanctifying Grace** - Growth in holiness
5. **Glorifying Grace** - Final transformation

### The Quadrilateral
- **Scripture** - Primary authority honored?
- **Tradition** - Church wisdom valued?
- **Reason** - Intelligent faith modeled?
- **Experience** - Personal encounter included?

### Both/And Tensions
- Personal AND social holiness
- Grace AND responsibility
- Faith AND works (not vs.)
- Already AND not yet
- Challenge AND comfort

### Methodist Distinctives
- Universal atonement (Christ died for all)
- Free will (ability to respond to grace)
- Assurance (can know you're saved)
- Christian perfection (perfect love, not sinlessness)
- Means of grace (practices that convey grace)

## Common Theological Pitfalls

### Grace Without Demand
**Problem:** Making grace so free that transformation isn't expected
**Fix:** Emphasize that grace empowers change, not just forgives

### Demand Without Grace
**Problem:** Making Christianity about performance
**Fix:** Ground every call in grace that enables response

### Moralistic Therapeutic Deism
**Problem:** God helps me be good and feel good
**Fix:** Center the Gospel—sin, grace, redemption, mission

### Transactional Salvation
**Problem:** Do X, get Y from God
**Fix:** Emphasize relationship over transaction

### Prosperity Theology (Subtle)
**Problem:** Implying faithfulness leads to success
**Fix:** Acknowledge suffering, don't promise outcomes

### Works Righteousness (Subtle)
**Problem:** Implying we earn God's favor
**Fix:** Clarify that works flow from grace, not toward it

## Example Review
```json
{
  "overall_assessment": {
    "theological_soundness": "adequate",
    "wesleyan_alignment": "strong",
    "scriptural_faithfulness": "strong",
    "summary": "Solid sermon with strong Wesleyan grounding. One significant concern about implied universalism, one minor clarity issue."
  },
  "commendations": [
    {
      "location": "Point 2, paragraph 3",
      "observation": "Excellent explanation of prevenient grace",
      "why_it_matters": "Makes Wesleyan distinctive accessible and powerful"
    },
    {
      "location": "Conclusion",
      "observation": "Grace-fueled commission, not guilt-fueled",
      "why_it_matters": "Sends congregation with gospel motivation"
    }
  ],
  "concerns": [
    {
      "severity": "significant",
      "location": "Point 2, final paragraph",
      "issue": "Statement 'God's grace will eventually find everyone' could imply universalism",
      "theological_basis": "While Wesleyans affirm universal atonement (grace offered to all), we don't affirm universalism (all will be saved). Human response matters.",
      "suggestion": "Reframe as 'God's grace pursues everyone' or 'No one is beyond the reach of grace'—emphasizing offer, not automatic outcome"
    },
    {
      "severity": "minor",
      "location": "Introduction",
      "issue": "GPS metaphor could imply determinism if pushed too far",
      "theological_basis": "We want to preserve human agency in response to grace",
      "suggestion": "Brief acknowledgment that unlike GPS, we can refuse the route God offers"
    }
  ],
  "wesleyan_check": {
    "grace_emphasized": "Strong—prevenient grace beautifully explained",
    "quadrilateral_balance": "Scripture primary, reason present, could use more tradition/experience",
    "personal_social_holiness": "Personal holiness strong; social dimension could be stronger in application",
    "methodist_distinctives": "Excellent prevenient grace; consider brief mention of means of grace in application"
  }
}
```

## Context for UUMC
- Congregation includes theological diversity
- Post-2024 UMC—remaining in denomination
- Some very theologically literate members
- "Purple" church—theology shouldn't code partisan
- Welcoming, affirming posture—theology should support inclusion
