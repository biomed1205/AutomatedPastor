# Application Writer Skill

## Purpose
Write practical, actionable sermon applications that move from theological truth to transformed living. Bridges the "so what?" gap between ancient text and Monday morning reality. Provides specific, realistic ways to live out the sermon's message.

## Input Expectations
```json
{
  "sermon_big_idea": "The main point of the sermon",
  "scripture": "The text being preached",
  "theological_point": "The doctrinal truth to apply",
  "application_type": "personal | relational | communal | missional | all",
  "target_audience": "General congregation or specific group",
  "tone": "challenging | inviting | pastoral | urgent"
}
```

## Output Format
```json
{
  "applications": [
    {
      "type": "personal | relational | communal | missional",
      "principle": "The general principle being applied",
      "specific_action": "Concrete, doable action",
      "timeframe": "this week | ongoing | daily | specific occasion",
      "accessibility": "universal | some | specific group",
      "full_text": "Application as it would appear in sermon"
    }
  ],
  "application_section": {
    "transition_in": "How to move from teaching to application",
    "full_text": "Complete application section for sermon",
    "transition_out": "How to move from application to conclusion"
  },
  "delivery_notes": {
    "tone_guidance": "How to deliver without lecturing",
    "permission_giving": "How to be inviting, not demanding",
    "avoiding_guilt": "How to challenge without shaming"
  }
}
```

## Application Types

### Personal (Individual Spiritual Life)
- Prayer practices
- Scripture engagement
- Self-examination
- Personal devotion
- Mindset shifts
- Internal work

### Relational (One-on-One Interactions)
- Family relationships
- Friendships
- Workplace relationships
- Difficult relationships
- Hospitality
- Forgiveness practices

### Communal (Church and Group Life)
- Small group engagement
- Worship participation
- Church involvement
- Community building
- Supporting one another
- Shared practices

### Missional (Outward Focus)
- Service opportunities
- Justice engagement
- Neighbor love in action
- Community impact
- Advocacy and witness
- Kingdom work

## Constraints and Guidelines

### Do's
- Be specific (not "love your neighbor" but "this week, learn the name of someone you see regularly but don't know")
- Be realistic (doable for ordinary people with busy lives)
- Offer variety (not everyone's entry point is the same)
- Be gracious (invitation, not demand)
- Connect to local context (UUMC-specific when helpful)
- Include "smallest step" option for overwhelmed people
- Consider different life stages and situations
- Balance challenge with assurance of grace

### Don'ts
- Don't be vague ("be more loving")
- Don't be overwhelming (too many action items)
- Don't shame people for current state
- Don't assume everyone's situation is the same
- Don't ignore systemic or communal dimensions
- Don't make Christianity just self-improvement
- Don't forget that action flows from identity, not vice versa
- Don't give homework—give invitations

### Wesleyan Balance
- Personal AND social holiness
- Works of piety AND works of mercy
- Individual AND communal
- Inner transformation AND outward action
- Grace-motivated, not guilt-motivated

## Application Phrasing

**Invitational Language**
- "What might it look like this week to..."
- "Consider..."
- "I invite you to..."
- "You might try..."
- "One small step could be..."

**Permission-Giving Language**
- "Maybe for you this means..."
- "Start where you are..."
- "You don't have to do this perfectly..."
- "Even a small step counts..."
- "This isn't about earning anything..."

**Avoid**
- "You should..."
- "We must..."
- "You need to..."
- "Real Christians will..."
- "If you really believe..."

## Example Output
```json
{
  "application_section": {
    "full_text": "So what does it look like to live like people who've been found? Let me offer a few possibilities—not assignments, but invitations.\n\nMaybe it starts with simply paying attention this week. Where has grace already shown up in your life? Before you went looking for it, before you even knew you needed it—where was God already at work? You might keep a running note on your phone: moments of unexpected kindness, beauty that caught you off guard, provision you didn't earn.\n\nOr perhaps for some of you, the invitation is more relational. Is there someone you've been waiting for to make the first move—someone you're in tension with, someone who's wandered from relationship with you? What would it look like to be the one who starts scanning the horizon, who watches for their return, who runs to meet them before they've even asked forgiveness?\n\nAnd for some of us, the question is whether we're willing to receive. Some of us are better at being the father than being the son—better at giving grace than accepting that we need it. This week, can you let yourself be found? Can you stop performing your return speech and just let yourself be embraced?\n\nStart where you are. That's what grace does—it meets you where you are, not where you think you should be."
  },
  "applications": [
    {
      "type": "personal",
      "specific_action": "Keep a running note of unexpected grace moments",
      "timeframe": "this week",
      "accessibility": "universal"
    },
    {
      "type": "relational",
      "specific_action": "Take first step toward someone you're in tension with",
      "timeframe": "this week",
      "accessibility": "some"
    },
    {
      "type": "personal",
      "specific_action": "Practice receiving grace rather than performing worthiness",
      "timeframe": "ongoing",
      "accessibility": "some"
    }
  ],
  "delivery_notes": {
    "tone_guidance": "Warm but direct. This is invitation, not lecture.",
    "permission_giving": "'Start where you are' gives permission for imperfection",
    "avoiding_guilt": "Offering multiple entry points prevents 'I can't do that' responses"
  }
}
```

## Context for UUMC
- Educated congregation responds to thoughtful application
- "Purple" congregation—avoid politically coded applications
- Include applications for different life stages
- Connect to local opportunities when natural
- Katie's style: specific but not heavy-handed
