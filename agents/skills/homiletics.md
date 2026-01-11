# Homiletics Skill

## Purpose
Design sermon structure and outline. Determines the overall architecture of the sermon—how to move from introduction through main points to conclusion. Ensures the sermon has clear organization, logical flow, and appropriate form for the content.

## Input Expectations
```json
{
  "scripture": "The passage being preached",
  "big_idea": "The one main point of the sermon",
  "research_insights": "Key findings from bible/theology research",
  "sermon_occasion": "Regular Sunday | liturgical season | special occasion",
  "time_target": "Target sermon length in minutes (typically 15)",
  "preacher_notes": "Any specific structural requests"
}
```

## Output Format
```json
{
  "structure_recommendation": {
    "form": "deductive | inductive | narrative | textual | topical",
    "rationale": "Why this form suits this sermon"
  },
  "outline": {
    "title": "Sermon title (optional)",
    "big_idea": "One-sentence summary",
    "introduction": {
      "hook_approach": "How to open",
      "transition_to_text": "How to get to scripture",
      "thesis_preview": "What to preview (if anything)"
    },
    "body": [
      {
        "point_number": 1,
        "point_statement": "Main point in one sentence",
        "scripture_anchor": "Specific verses for this point",
        "development_approach": "How to unpack this",
        "illustration_need": "What kind of illustration might work",
        "application_angle": "Practical implication"
      }
    ],
    "conclusion": {
      "summary_approach": "How to crystallize the message",
      "callback": "Connection to opening (if used)",
      "commission": "How to send them out"
    }
  },
  "flow_diagram": "Visual representation of sermon movement",
  "word_allocation": {
    "introduction": "Suggested word count",
    "point_1": "Suggested word count",
    "point_2": "Suggested word count",
    "point_3": "Suggested word count (if applicable)",
    "conclusion": "Suggested word count",
    "total": "Total word count"
  },
  "structural_notes": {
    "tension_build": "Where tension rises",
    "resolution": "Where resolution comes",
    "emotional_arc": "How feeling should move",
    "pacing": "Faster/slower sections"
  }
}
```

## Sermon Forms

### Deductive (Point-First)
- State the big idea early
- Spend sermon proving/unpacking it
- Works for: Clear teaching, complex doctrine
- Example: "Today we're going to see that grace comes before we ask for it. Let me show you from the text..."

### Inductive (Discovery)
- Big idea emerges at the end
- Sermon builds toward revelation
- Works for: Narrative texts, surprising conclusions
- Example: Walk through the text, let the "aha" come at the end

### Narrative (Story-Following)
- Follow the text's story structure
- Sermon moves as narrative moves
- Works for: Gospel stories, Old Testament narratives
- Example: Prodigal Son—move through the story

### Textual (Verse-by-Verse)
- Work through the passage sequentially
- Each point from sequential sections
- Works for: Epistles, structured passages
- Example: Romans 8:28-30—three verses, three points

### Topical (Theme-Based)
- Organize around a topic, not a single text
- Multiple scriptures supporting theme
- Works for: Doctrine series, thematic preaching
- Caution: Still anchor in primary text

## Standard Three-Point Structure

### Point 1: What does the text say?
- Exposition and explanation
- Get the content clear
- Answer: What did this mean then?

### Point 2: What does it mean?
- Theological significance
- Deeper implications
- Answer: Why does this matter?

### Point 3: What do we do about it?
- Application and response
- Practical transformation
- Answer: How do we live this?

## Alternative Structures

### Two-Point Structure
- Tension/Resolution
- Problem/Gospel
- Then/Now

### Four Movements (Eugene Lowry)
1. Oops (upset equilibrium)
2. Ugh (analyze the discrepancy)
3. Aha (disclose the gospel)
4. Whee (anticipate the future)

### Image-Based
- One central image that recurs
- All points refract through that image
- Example: "GPS recalculating" image throughout

## Constraints and Guidelines

### Do's
- Let the text shape the structure
- Ensure clear logical flow
- Include tension and resolution
- Plan illustration placement
- Build toward conclusion
- Make points memorable (parallel structure helps)
- Consider how it sounds spoken

### Don'ts
- Don't force every sermon into three points
- Don't let structure override scripture
- Don't make points so parallel they're artificial
- Don't frontload all the content
- Don't make structure visible but meaning invisible
- Don't end each point identically

## Word Count Guidelines (15-minute sermon = 2000-2500 words)

| Section | Words | Time |
|---------|-------|------|
| Introduction | 200-300 | 1:30-2:00 |
| Point 1 | 500-600 | 4:00-5:00 |
| Point 2 | 500-600 | 4:00-5:00 |
| Point 3 | 400-500 | 3:00-4:00 |
| Conclusion | 200-300 | 1:30-2:00 |
| **Total** | **2000-2500** | **15:00** |

## Example Output
```json
{
  "structure_recommendation": {
    "form": "narrative",
    "rationale": "Luke 15:11-32 is a story; let the sermon follow the story's movements rather than imposing external structure"
  },
  "outline": {
    "title": "Recalculating",
    "big_idea": "God's grace runs to meet us before we can earn our way home",
    "introduction": {
      "hook_approach": "GPS 'recalculating' moment—technology that finds you where you are",
      "transition_to_text": "Jesus tells a story about a Father who never stops recalculating",
      "thesis_preview": "Subtle—we're going to follow a family drama"
    },
    "body": [
      {
        "point_number": 1,
        "point_statement": "The father gives freedom even knowing it will be misused",
        "scripture_anchor": "vv. 11-12",
        "development_approach": "Explore the scandal of early inheritance (as if father were dead)",
        "illustration_need": "Freedom with painful consequences",
        "application_angle": "God doesn't coerce"
      },
      {
        "point_number": 2,
        "point_statement": "Grace runs to meet us before we can finish our speech",
        "scripture_anchor": "vv. 17-24",
        "development_approach": "The father's response—running, embracing, interrupting",
        "illustration_need": "Prevenient grace example",
        "application_angle": "Stop rehearsing your worthiness"
      },
      {
        "point_number": 3,
        "point_statement": "The older brother reveals our resistance to grace for others",
        "scripture_anchor": "vv. 25-32",
        "development_approach": "The brother's complaint reveals transactional view of love",
        "illustration_need": "Religious resentment of grace",
        "application_angle": "Are we running to meet others?"
      }
    ],
    "conclusion": {
      "summary_approach": "You are sought, not seeking",
      "callback": "GPS recalculating—God plots new course wherever you are",
      "commission": "Go as people who have been found"
    }
  },
  "word_allocation": {
    "introduction": 250,
    "point_1": 550,
    "point_2": 600,
    "point_3": 500,
    "conclusion": 250,
    "total": 2150
  }
}
```

## Context for UUMC
- Congregation follows complex structures well
- Don't over-signal structure ("my first point is...")
- Can use more literary/artistic forms
- Katie's style: clear but not mechanical
- Trust listeners to track sophisticated movement
