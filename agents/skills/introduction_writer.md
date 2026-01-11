# Introduction Writer Skill

## Purpose
Write compelling sermon introductions that hook the congregation, establish the sermon's direction, and create anticipation for what's to come. First impressions matter—the introduction sets the tone for everything that follows.

## Input Expectations
```json
{
  "scripture": "The passage being preached",
  "big_idea": "The one main point of the sermon",
  "sermon_title": "Optional title",
  "tone": "hopeful | challenging | pastoral | provocative | reflective",
  "hook_type": "question | story | observation | quote | contrast | surprise",
  "target_length": "150-250 words"
}
```

## Output Format
```json
{
  "introduction": {
    "hook": "Opening sentences that grab attention",
    "transition": "Bridge from hook to biblical text",
    "text_introduction": "Brief setup for the scripture",
    "thesis_preview": "Where we're going (without giving away the ending)",
    "full_text": "Complete introduction ready for sermon"
  },
  "alternatives": [
    {
      "approach": "Different style or angle",
      "text": "Alternative introduction"
    }
  ],
  "notes": {
    "delivery_suggestions": "How to deliver this effectively",
    "timing": "Approximate spoken time",
    "connections": "How this sets up later sermon elements"
  }
}
```

## Constraints and Guidelines

### Do's
- Start with energy and intentionality
- Create genuine curiosity about the text
- Connect to lived experience
- Make the scripture sound fresh and relevant
- Establish Katie's authentic voice
- Give people a reason to keep listening
- Set up the tension the sermon will resolve

### Don'ts
- Don't start with "Today's scripture is..."
- Don't give away the main point too early
- Don't start with apologies or disclaimers
- Don't use tired sermon clichés
- Don't be gimmicky or manipulative
- Don't start with personal/family anecdotes
- Don't over-promise what the sermon will deliver
- Don't make the introduction too long (get to the text)

### Hook Types

**Question Hook**
Start with a compelling question the text will address.
"Have you ever wondered why forgiveness feels so much harder than it sounds?"

**Story Hook**
Open with a brief story (not personal) that illuminates the theme.
"In 1940, as Nazi forces approached Paris, the curators of the Louvre faced an impossible decision..."

**Observation Hook**
Make an observation about life that the text speaks to.
"We live in a world of constant self-improvement—new apps, new habits, new versions of ourselves. And yet..."

**Quote Hook**
Begin with a provocative quote that sets up the sermon's tension.
"'The opposite of faith is not doubt,' Anne Lamott writes, 'the opposite of faith is certainty.'"

**Contrast Hook**
Set up a tension or paradox the sermon will explore.
"The most dangerous thing about comfort zones is how comfortable they are."

**Surprise Hook**
Open with something unexpected that reframes the familiar.
"What if the prodigal son story isn't really about the son at all?"

## Quality Standards
- First sentence should be memorable
- Introduction should take 1-2 minutes spoken
- Must set up the specific biblical text
- Should make people curious about what's next
- Must match Katie's intellectual but accessible style
- Should feel fresh, not formulaic

## Example Output
```json
{
  "introduction": {
    "full_text": "There's a moment in every GPS navigation when the screen says something both obvious and profound: 'Recalculating.' You missed a turn. You went a different way than planned. And instead of judgment, instead of giving up on you, the system simply adjusts. It finds you where you are and plots a new path forward.\n\nI've been thinking about that word—recalculating—as I've sat with today's reading from Luke 15. Because the story we're about to hear isn't really about a wayward son, though he's in it. It's not primarily about a resentful brother, though he's important too. This story is about a father who never stops recalculating—who never stops looking down the road, hoping, waiting, ready to run.\n\nLuke tells us Jesus shared this parable with tax collectors and sinners drawing near—and Pharisees and scribes grumbling about the company he was keeping. And in response, Jesus tells a story about a father whose love looks a lot like that GPS: no matter how far you've gone, no matter how lost you are, there's always a way home.",
    "hook": "GPS 'recalculating' moment",
    "transition": "Connection from GPS patience to the father's love",
    "thesis_preview": "This story is about a father who never stops recalculating"
  },
  "notes": {
    "delivery_suggestions": "Pause after 'recalculating' the first time. Let it land. The GPS image is familiar enough that people will track immediately.",
    "timing": "Approximately 1:30 spoken"
  }
}
```

## Context for UUMC
- Congregation appreciates intellectual hooks
- Avoid overly sentimental openings
- Pop culture references should be current and accessible
- Can assume biblical literacy but don't require it
- Set up the scripture to sound intriguing, not obligatory
