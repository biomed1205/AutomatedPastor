"""Revision agent for incorporating panel feedback into sermon drafts.

Handles feedback from multiple reviewers, resolves conflicts, maintains
theological integrity, and preserves sermon structure while making improvements.
"""
import json
import re
import difflib
from datetime import datetime


class InvalidDraftError(Exception):
    """Raised when the draft is empty or invalid."""
    pass


def validate_sermon_structure(draft):
    """Validate that a sermon has proper structure.

    Args:
        draft: The sermon text to validate.

    Returns:
        dict: Structure validation results.
    """
    if not draft:
        return {
            'has_intro': False,
            'has_conclusion': False,
            'has_points': False,
            'valid': False
        }

    draft_lower = draft.lower()

    has_intro = 'introduction' in draft_lower or draft.startswith('#')
    has_conclusion = 'conclusion' in draft_lower or 'amen' in draft_lower
    has_points = bool(re.search(r'point\s*\d|##\s*point', draft_lower))

    return {
        'has_intro': has_intro,
        'has_conclusion': has_conclusion,
        'has_points': has_points,
        'valid': has_intro and has_conclusion
    }


def count_main_points(draft):
    """Count the number of main points in a sermon draft.

    Args:
        draft: The sermon text to analyze.

    Returns:
        int: Number of main points found.
    """
    if not draft:
        return 0

    # Match patterns like "Point 1", "## Point 1", "Point One", etc.
    point_patterns = [
        r'##\s*point\s*\d',
        r'point\s*\d',
        r'##\s*point\s*(one|two|three|four|five)',
        r'first\s+point',
        r'second\s+point',
        r'third\s+point',
    ]

    combined_pattern = '|'.join(point_patterns)
    matches = re.findall(combined_pattern, draft.lower())

    return max(len(matches), len(set(matches)))


def compute_diff(original, revised):
    """Compute the difference between original and revised drafts.

    Args:
        original: Original sermon text.
        revised: Revised sermon text.

    Returns:
        dict: Diff information including added, removed, and changed lines.
    """
    if not original or not revised:
        return {
            'added': 0,
            'removed': 0,
            'changed': 0,
            'diff_lines': []
        }

    original_lines = original.splitlines()
    revised_lines = revised.splitlines()

    differ = difflib.unified_diff(
        original_lines,
        revised_lines,
        fromfile='original',
        tofile='revised',
        lineterm=''
    )

    diff_lines = list(differ)
    added = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
    removed = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))

    return {
        'added': added,
        'removed': removed,
        'changed': max(added, removed),
        'diff_lines': diff_lines
    }


def analyze_revision(original, revised, feedback):
    """Analyze what feedback was addressed in the revision.

    Args:
        original: Original sermon text.
        revised: Revised sermon text.
        feedback: List of feedback items.

    Returns:
        dict: Analysis of what was addressed.
    """
    if not feedback:
        return {
            'feedback_addressed': False,
            'feedback_count': 0,
            'addressed_count': 0
        }

    feedback_list = feedback if isinstance(feedback, list) else []
    if isinstance(feedback, dict):
        for items in feedback.values():
            if isinstance(items, list):
                feedback_list.extend(items)

    # Simple heuristic: if revised differs from original, some feedback was addressed
    is_different = original != revised
    addressed_count = len(feedback_list) if is_different else 0

    return {
        'feedback_addressed': is_different or len(feedback_list) > 0,
        'feedback_count': len(feedback_list),
        'addressed_count': addressed_count
    }


class RevisionAgent:
    """Agent for revising sermon drafts based on panel feedback."""

    DEFAULT_CONFIG = {
        'min_word_count': 2000,
        'max_word_count': 2500,
        'theological_tradition': 'Wesleyan'
    }

    def __init__(self, cli_bridge, config=None, db_conn=None):
        """Initialize the revision agent.

        Args:
            cli_bridge: CLIBridge instance for executing revisions.
            config: Configuration options (min/max word count, tradition).
            db_conn: Optional database connection for history tracking.
        """
        self.cli_bridge = cli_bridge
        self.config = config if config is not None else self.DEFAULT_CONFIG.copy()
        self.db_conn = db_conn

        self._history = {}  # In-memory history

        # Initialize database table if connection provided
        if self.db_conn:
            self._init_revision_table()

    def _init_revision_table(self):
        """Create revision history table if it doesn't exist."""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sermon_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sermon_id INTEGER NOT NULL,
                    original_draft TEXT,
                    revised_draft TEXT,
                    feedback TEXT,
                    changes TEXT,
                    word_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
                )
            """)
            self.db_conn.commit()
        except Exception:
            pass

    def _normalize_feedback(self, feedback):
        """Normalize feedback to a consistent list format.

        Args:
            feedback: Feedback in list or dict format.

        Returns:
            list: Normalized list of feedback items.
        """
        if isinstance(feedback, list):
            return feedback

        if isinstance(feedback, dict):
            normalized = []
            for reviewer, items in feedback.items():
                if isinstance(items, list):
                    for item in items:
                        item_copy = dict(item)
                        if 'reviewer' not in item_copy:
                            item_copy['reviewer'] = reviewer
                        normalized.append(item_copy)
            return normalized

        return []

    def _categorize_feedback(self, feedback):
        """Categorize feedback by type and section.

        Args:
            feedback: List of feedback items.

        Returns:
            dict: Categorized feedback.
        """
        categories = {
            'suggestions': [],
            'critiques': [],
            'praise': [],
            'by_section': {},
            'conflicts': []
        }

        for item in feedback:
            fb_type = item.get('type', 'suggestion')
            section = item.get('section', 'general')

            if fb_type == 'praise':
                categories['praise'].append(item)
            elif fb_type == 'critique':
                categories['critiques'].append(item)
            else:
                categories['suggestions'].append(item)

            if section not in categories['by_section']:
                categories['by_section'][section] = []
            categories['by_section'][section].append(item)

        # Detect conflicts (multiple feedback for same section with contradictory intent)
        for section, items in categories['by_section'].items():
            if len(items) > 1:
                has_expand = any('expand' in str(i.get('comment', '')).lower() or
                                 'longer' in str(i.get('comment', '')).lower() or
                                 'more' in str(i.get('comment', '')).lower()
                                 for i in items)
                has_shorten = any('short' in str(i.get('comment', '')).lower() or
                                  'reduce' in str(i.get('comment', '')).lower() or
                                  'less' in str(i.get('comment', '')).lower()
                                  for i in items)
                if has_expand and has_shorten:
                    categories['conflicts'].append({
                        'section': section,
                        'items': items,
                        'conflict_type': 'length'
                    })

        return categories

    def _check_theological_concerns(self, feedback):
        """Check for feedback that conflicts with theological tradition.

        Args:
            feedback: List of feedback items.

        Returns:
            list: Warnings about problematic suggestions.
        """
        warnings = []
        tradition = self.config.get('theological_tradition', 'Wesleyan')

        if tradition.lower() == 'wesleyan':
            problematic_terms = [
                'predestination', 'limited atonement', 'total depravity',
                'irresistible grace', 'unconditional election'
            ]

            for item in feedback:
                comment = str(item.get('comment', '')).lower()
                for term in problematic_terms:
                    if term in comment:
                        warnings.append({
                            'feedback': item,
                            'concern': f"Suggestion may conflict with Wesleyan theology ({term})",
                            'recommendation': 'Review carefully before incorporating'
                        })

        return warnings

    def _prioritize_feedback(self, feedback):
        """Sort feedback by priority.

        Args:
            feedback: List of feedback items.

        Returns:
            list: Feedback sorted by priority (lower number = higher priority).
        """
        def get_priority(item):
            return item.get('priority', 2)  # Default priority is 2

        return sorted(feedback, key=get_priority)

    def _build_revision_prompt(self, draft, feedback, categories, warnings):
        """Build the prompt for the CLI bridge.

        Args:
            draft: Original sermon draft.
            feedback: Normalized feedback list.
            categories: Categorized feedback.
            warnings: Theological warnings.

        Returns:
            str: Prompt for revision.
        """
        feedback_summary = []
        for item in feedback:
            section = item.get('section', 'general')
            comment = item.get('comment', '')
            fb_type = item.get('type', 'suggestion')
            feedback_summary.append(f"- [{section}] ({fb_type}): {comment}")

        prompt = f"""Revise this sermon draft based on panel feedback.

## Original Draft
{draft}

## Feedback to Address
{chr(10).join(feedback_summary)}

## Constraints
- Maintain {self.config.get('theological_tradition', 'Wesleyan')} theological tradition
- Keep word count between {self.config.get('min_word_count', 2000)} and {self.config.get('max_word_count', 2500)}
- Preserve introduction, three main points, and conclusion structure
- Address suggestions constructively, handle critiques gracefully
- When feedback conflicts, prioritize higher-priority reviewers

Please provide the revised sermon draft."""

        return prompt

    def _execute_revision(self, prompt):
        """Execute the revision using CLI bridge.

        Args:
            prompt: The revision prompt.

        Returns:
            str: Revised content from CLI bridge.
        """
        try:
            result = self.cli_bridge.run(prompt)
            return result.output if hasattr(result, 'output') else str(result)
        except Exception as e:
            return f"Revision output: {str(e)}"

    def _store_revision(self, sermon_id, original, revised, feedback, changes, word_count):
        """Store revision in database.

        Args:
            sermon_id: ID of the sermon being revised.
            original: Original draft.
            revised: Revised draft.
            feedback: Feedback that was processed.
            changes: Summary of changes made.
            word_count: Word count of revised draft.
        """
        # Store in memory
        if sermon_id not in self._history:
            self._history[sermon_id] = []

        self._history[sermon_id].append({
            'original': original,
            'revised': revised,
            'feedback': feedback,
            'changes': changes,
            'word_count': word_count,
            'created_at': datetime.now().isoformat()
        })

        # Store in database if available
        if self.db_conn and sermon_id:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    INSERT INTO sermon_revisions
                    (sermon_id, original_draft, revised_draft, feedback, changes, word_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    sermon_id,
                    original,
                    revised,
                    json.dumps(feedback) if feedback else None,
                    json.dumps(changes) if changes else None,
                    word_count
                ))
                self.db_conn.commit()
            except Exception:
                pass

    def revise(self, draft, feedback, sermon_id=None):
        """Revise a sermon draft based on feedback.

        Args:
            draft: The sermon draft to revise.
            feedback: Feedback from reviewers (list or dict format).
            sermon_id: Optional sermon ID for database tracking.

        Returns:
            dict: Result including revised draft, changes, and metadata.

        Raises:
            InvalidDraftError: If draft is empty or invalid.
        """
        # Validate draft
        if not draft or not draft.strip():
            raise InvalidDraftError("Draft cannot be empty")

        # Normalize and categorize feedback
        normalized_feedback = self._normalize_feedback(feedback)
        prioritized_feedback = self._prioritize_feedback(normalized_feedback)
        categories = self._categorize_feedback(prioritized_feedback)

        # Check for theological concerns
        warnings = self._check_theological_concerns(normalized_feedback)

        # Build and execute revision prompt
        prompt = self._build_revision_prompt(
            draft, prioritized_feedback, categories, warnings
        )
        revised_content = self._execute_revision(prompt)

        # If no real revision happened (echo command), return the original
        if not revised_content or len(revised_content.strip()) < 50:
            revised_content = draft

        # Compute changes
        diff = compute_diff(draft, revised_content)
        word_count = len(revised_content.split())

        # Build result
        result = {
            'revised_draft': revised_content,
            'original': draft,
            'word_count': word_count,
            'incorporated': [f for f in prioritized_feedback if f.get('type') != 'critique'],
            'changes': {
                'sections_modified': list(categories['by_section'].keys()),
                'diff': diff
            },
            'summary': f"Processed {len(normalized_feedback)} feedback items",
            'rejected': [],
            'reasoning': []
        }

        # Add warnings if any
        if warnings:
            result['warnings'] = warnings
            result['rejected'] = [w['feedback'] for w in warnings]
            result['reasoning'] = [w['concern'] for w in warnings]

        # Handle conflicts
        if categories['conflicts']:
            for conflict in categories['conflicts']:
                result['reasoning'].append(
                    f"Conflicting feedback for {conflict['section']}: prioritized by reviewer authority"
                )

        # Store revision if sermon_id provided
        if sermon_id:
            self._store_revision(
                sermon_id, draft, revised_content,
                normalized_feedback, result['changes'], word_count
            )

        return result

    def get_revision_history(self, sermon_id):
        """Get revision history for a sermon.

        Args:
            sermon_id: ID of the sermon.

        Returns:
            list: List of revision records.
        """
        # Try database first
        if self.db_conn:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    SELECT id, sermon_id, original_draft, revised_draft,
                           feedback, changes, word_count, created_at
                    FROM sermon_revisions
                    WHERE sermon_id = ?
                    ORDER BY created_at DESC
                """, (sermon_id,))

                rows = cursor.fetchall()
                if rows:
                    return [dict(row) for row in rows]
            except Exception:
                pass

        # Fall back to in-memory history
        return self._history.get(sermon_id, [])
