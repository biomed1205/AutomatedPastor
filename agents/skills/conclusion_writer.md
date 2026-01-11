# Conclusion Writer Skill

## Purpose
Write sermon conclusions that land the message, call for response, and send the congregation with hope. The conclusion is where everything comes together—where the seeds planted throughout the sermon bear fruit and the congregation is commissioned to live differently.

## Input Expectations
```json
{
  "sermon_big_idea": "The one main point of the sermon",
  "scripture": "The text that was preached",
  "main_points": ["List of the main points developed"],
  "introduction_hook": "What opened the sermon (for callback)",
  "tone": "hopeful | challenging | tender | triumphant | reflective",
  "call_to_action": "Primary response invited",
  "target_length": "200-300 words"
}
```

## Output Format
```json
{
  "conclusion": {
    "summary": "Brief restatement of the core message",
    "callback": "Connection to opening illustration or hook",
    "culmination": "The 'aha' moment or emotional peak",
    "commission": "Sending words for the week ahead",
    "final_sentence": "The last words (make them count)",
    "full_text": "Complete conclusion ready for sermon"
  },
  "alternatives": {
    "different_ending": "Alternative approach to closing"
  },
  "notes": {
    "delivery_guidance": "How to land this effectively",
    "timing": "Approximate spoken time",
    "what_NOT_to_add": "Keep it tight—don't keep going"
  }
}
```

## Conclusion Elements

### 1. Summary (Brief, Not Repetitive)
- Distill sermon to one clear takeaway
- Don't re-preach—crystallize
- Use fresh language, not repetition
- One to two sentences maximum

### 2. Callback (Connect to Opening)
- Return to opening illustration or question
- Show how it's been answered or transformed
- Creates satisfying narrative arc
- "Remember when we said...? Now we see..."

### 3. Culmination (Emotional/Spiritual Peak)
- The moment everything lands
- Can be quiet or triumphant
- Where head meets heart
- Where truth becomes beautiful

### 4. Commission (Send Them Out)
- Not just "go do this" but "go BE this"
- Gospel-fueled, not guilt-fueled
- Identity before action
- This week, this life, this world

### 5. Final Sentence (Make It Count)
- Memorable, quotable, holdable
- Could be a prayer, a blessing, a declaration
- Something they'll carry into the week
- Land the plane

## Constraints and Guidelines

### Do's
- End with strength and clarity
- Make the last line count
- Connect to what opened the sermon
- Send them with hope
- Trust what you've already said
- Stop when you're done

### Don'ts
- Don't introduce new material
- Don't apologize or qualify
- Don't keep preaching after you've finished
- Don't end with announcements or logistics
- Don't trail off—land confidently
- Don't let the conclusion be too long
- Don't moralize or scold at the end

### Ending Approaches

**The Callback Close**
Return to opening image with new understanding.
"Remember that father, scanning the horizon? That's God. And God is still watching. Still running. Still ready to meet you wherever you are."

**The Commissioning Close**
Send them with purpose.
"So go. Not as people who have to earn love, but as people who have already been found. Go knowing that grace went before you and will follow after you. Go and live like loved people."

**The Quiet Landing**
Let truth settle gently.
"You are sought. You are found. You are home."

**The Blessing Close**
End with benediction.
"May you know yourself held. May you trust grace to meet you. And may the God who never stops running toward you give you peace. Amen."

**The Challenge Close**
Leave them with something to wrestle with.
"The question isn't whether grace is available. It's whether you're willing to be found."

## Example Output
```json
{
  "conclusion": {
    "full_text": "Here's what I want you to hold as we close: You are not looking for a God who is hiding. You are being found by a God who is seeking.\n\nRemember that GPS recalculating? Here's what I love about it: the GPS doesn't give up on you when you take a wrong turn. It doesn't shame you for missing the exit. It simply finds you where you are and plots a new course home.\n\nThat's the God we meet in this text. A father who never stops watching. A grace that goes before us. A love that runs to meet us while we're still far off.\n\nMaybe you came here this morning feeling lost. Maybe you're carrying the weight of wrong turns and missed exits. Maybe you've rehearsed your speech about why you're not good enough, not faithful enough, not worthy of welcome.\n\nHear this: Grace has already run to meet you. Before you could take a step, before you could explain yourself, before you even looked up—Love was already on its way.\n\nYou are sought. You are found. You are home. Amen.",
    "summary": "You are not seeking a hiding God—you are being found by a seeking God",
    "callback": "GPS recalculating metaphor resolved",
    "culmination": "Grace has already run to meet you",
    "commission": "Implicit—rest in being found",
    "final_sentence": "You are sought. You are found. You are home. Amen."
  },
  "notes": {
    "delivery_guidance": "Slow down for the final three sentences. Each one deserves space. End with 'Amen' but let it ring—don't rush to sit down.",
    "timing": "Approximately 2 minutes spoken",
    "what_NOT_to_add": "Don't add a final application list. The 'home' metaphor IS the application."
  }
}
```

## Context for UUMC
- Conclusions should respect the intelligence of the congregation
- Avoid sentimental over-emotional endings
- Can end with confidence—congregation handles challenge
- Katie's style: strong but warm, clear but not simplistic
- UUMC appreciates being trusted with substantial endings
