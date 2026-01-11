"""Panel feedback system for reviewer personas.

Provides a panel of reviewers that analyze sermon drafts and provide
focused feedback from different perspectives.
"""
import os
import json
import concurrent.futures
from datetime import datetime


class EmptySermonError(Exception):
    """Raised when the sermon is empty or None."""
    pass


class ReviewerNotFoundError(Exception):
    """Raised when the requested reviewer type is not found."""
    pass


# Default reviewer types and their mappings to reviewer files
DEFAULT_REVIEWER_TYPES = {
    'theological': {
        'file': 'theological_scholar.md',
        'focus': 'Theological accuracy and doctrinal soundness',
        'description': 'Reviews for Wesleyan theological integrity'
    },
    'pastoral': {
        'file': 'pastoral_mentor.md',
        'focus': 'Pastoral application and care',
        'description': 'Reviews for pastoral sensitivity and sustainability'
    },
    'structural': {
        'file': 'homiletics_professor.md',
        'focus': 'Sermon structure and outline',
        'description': 'Reviews sermon organization and flow'
    },
    'engagement': {
        'file': 'congregation_member.md',
        'focus': 'Audience engagement and relevance',
        'description': 'Reviews from engaged layperson perspective'
    },
    'illustration': {
        'file': 'visitor_perspective.md',
        'focus': 'Illustration quality and accessibility',
        'description': 'Reviews illustrations for clarity and impact'
    },
    'scripture': {
        'file': 'elder_voice.md',
        'focus': 'Scripture handling and interpretation',
        'description': 'Reviews scriptural engagement and faithfulness'
    },
    'language': {
        'file': 'youth_leader.md',
        'focus': 'Language clarity and accessibility',
        'description': 'Reviews for clarity and contemporary relevance'
    }
}


def get_reviewer_focus(reviewer_type):
    """Get the focus area for a reviewer type.

    Args:
        reviewer_type: Type of reviewer.

    Returns:
        str: Focus area description.
    """
    if reviewer_type in DEFAULT_REVIEWER_TYPES:
        return DEFAULT_REVIEWER_TYPES[reviewer_type]['focus']
    return f"General review for {reviewer_type}"


def get_reviewer_feedback(reviewer_type, sermon):
    """Get feedback structure for a reviewer type.

    Args:
        reviewer_type: Type of reviewer.
        sermon: Sermon text to review.

    Returns:
        dict: Feedback structure.
    """
    focus = get_reviewer_focus(reviewer_type)
    return {
        'reviewer': reviewer_type,
        'type': reviewer_type,
        'focus': focus,
        'comments': [],
        'suggestions': [],
        'rating': 'good',
        'score': 4
    }


def create_custom_reviewer(name, focus, prompt):
    """Create a custom reviewer definition.

    Args:
        name: Name/identifier for the reviewer.
        focus: Focus area description.
        prompt: Review prompt template.

    Returns:
        dict: Custom reviewer definition.
    """
    return {
        'name': name,
        'focus': focus,
        'prompt': prompt,
        'type': 'custom'
    }


def save_reviewer(reviewer, directory):
    """Save a custom reviewer to a markdown file.

    Args:
        reviewer: Reviewer definition dict.
        directory: Directory to save to.
    """
    name = reviewer.get('name', 'custom')
    filepath = os.path.join(directory, f'{name}.md')

    content = f"""# {name.replace('_', ' ').title()} Reviewer

## Focus Area
{reviewer.get('focus', 'General review')}

## Review Prompt
{reviewer.get('prompt', 'Review this sermon.')}
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def store_feedback(conn, sermon_id, reviewer_type, feedback):
    """Store feedback in the database.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        reviewer_type: Type of reviewer.
        feedback: Feedback dict.
    """
    # Ensure panel_feedback table exists
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS panel_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            reviewer_type TEXT NOT NULL,
            feedback TEXT,
            rating TEXT,
            score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        INSERT INTO panel_feedback (sermon_id, reviewer_type, feedback, rating, score)
        VALUES (?, ?, ?, ?, ?)
    """, (
        sermon_id,
        reviewer_type,
        json.dumps(feedback) if feedback else None,
        feedback.get('rating') if feedback else None,
        feedback.get('score') if feedback else None
    ))
    conn.commit()


def get_stored_feedback(conn, sermon_id, reviewer_type):
    """Retrieve stored feedback from database.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        reviewer_type: Type of reviewer.

    Returns:
        dict: Stored feedback or None.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT feedback, rating, score, created_at
            FROM panel_feedback
            WHERE sermon_id = ? AND reviewer_type = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (sermon_id, reviewer_type))

        row = cursor.fetchone()
        if row:
            feedback_data = json.loads(row[0]) if row[0] else {}
            feedback_data['rating'] = row[1]
            feedback_data['score'] = row[2]
            feedback_data['created_at'] = row[3]
            return feedback_data
    except Exception:
        # Table may not exist yet
        pass
    return None


def aggregate_panel_feedback(feedbacks):
    """Aggregate feedback from multiple reviewers.

    Args:
        feedbacks: List of feedback dicts.

    Returns:
        dict: Aggregated feedback summary.
    """
    if not feedbacks:
        return {'items': [], 'feedback': [], 'summary': 'No feedback collected'}

    items = []
    total_score = 0
    count = 0

    for fb in feedbacks:
        if isinstance(fb, dict):
            items.append({
                'reviewer': fb.get('reviewer', fb.get('type', 'unknown')),
                'focus': fb.get('focus', ''),
                'rating': fb.get('rating', 'good'),
                'score': fb.get('score', 4)
            })
            if fb.get('score'):
                total_score += fb.get('score', 0)
                count += 1

    avg_score = total_score / count if count > 0 else 0

    return {
        'items': items,
        'feedback': feedbacks,
        'summary': f"Collected feedback from {len(feedbacks)} reviewers",
        'average_score': round(avg_score, 1),
        'reviewer_count': len(feedbacks)
    }


class FeedbackPanel:
    """Panel of reviewers for sermon feedback."""

    DEFAULT_REVIEWERS_DIR = 'agents/reviewers/'

    def __init__(self, cli_bridge, reviewers_dir=None, db_conn=None):
        """Initialize the feedback panel.

        Args:
            cli_bridge: CLIBridge for executing review prompts.
            reviewers_dir: Directory containing reviewer prompt files.
            db_conn: Optional database connection.
        """
        self.cli_bridge = cli_bridge
        self._reviewers_dir = reviewers_dir if reviewers_dir is not None else self.DEFAULT_REVIEWERS_DIR
        self.db_conn = db_conn

        # Load default reviewers
        self._reviewers = {}
        self._load_default_reviewers()
        self._load_reviewers_from_directory()

    @property
    def reviewers_dir(self):
        """Get the reviewers directory path."""
        return self._reviewers_dir

    @property
    def reviewers(self):
        """Get list of available reviewer types."""
        return list(self._reviewers.keys())

    def _load_default_reviewers(self):
        """Load default reviewer configurations."""
        for reviewer_type, config in DEFAULT_REVIEWER_TYPES.items():
            self._reviewers[reviewer_type] = {
                'name': reviewer_type,
                'focus': config['focus'],
                'description': config['description'],
                'file': config['file'],
                'type': 'default'
            }

    def _load_reviewers_from_directory(self):
        """Load reviewer prompts from the reviewers directory."""
        if not os.path.isdir(self._reviewers_dir):
            return

        for filename in os.listdir(self._reviewers_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(self._reviewers_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    name = filename.replace('.md', '')
                    if name not in self._reviewers:
                        self._reviewers[name] = {
                            'name': name,
                            'focus': f'Review from {name} perspective',
                            'content': content,
                            'type': 'file'
                        }
                except (UnicodeDecodeError, IOError):
                    # Skip corrupted files
                    pass

    def _get_reviewer_prompt(self, reviewer_type):
        """Get the review prompt for a reviewer type.

        Args:
            reviewer_type: Type of reviewer.

        Returns:
            str: Review prompt content.
        """
        reviewer = self._reviewers.get(reviewer_type)
        if not reviewer:
            raise ReviewerNotFoundError(f"Reviewer not found: {reviewer_type}")

        if 'content' in reviewer:
            return reviewer['content']

        # Try to load from file
        if 'file' in reviewer:
            filepath = os.path.join(self._reviewers_dir, reviewer['file'])
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        return f.read()
                except (UnicodeDecodeError, IOError):
                    pass

        # Return a generic prompt
        return f"""# {reviewer_type.title()} Review

Focus: {reviewer.get('focus', 'General review')}

Please review the sermon and provide feedback focusing on: {reviewer.get('focus', 'overall quality')}
"""

    def _execute_review(self, reviewer_type, sermon, prompt):
        """Execute a review using the CLI bridge.

        Args:
            reviewer_type: Type of reviewer.
            sermon: Sermon text to review.
            prompt: Review prompt.

        Returns:
            dict: Review feedback.
        """
        full_prompt = f"""{prompt}

## Sermon to Review
{sermon}

Provide feedback in JSON format with: reviewer, focus, rating, score (1-5), comments, and suggestions.
"""

        try:
            result = self.cli_bridge.run(full_prompt)
            output = result.output if hasattr(result, 'output') else str(result)

            # Try to parse as JSON
            try:
                feedback = json.loads(output)
                if isinstance(feedback, dict):
                    feedback['reviewer'] = reviewer_type
                    feedback['type'] = reviewer_type
                    return feedback
            except (json.JSONDecodeError, TypeError):
                pass

            # Return structured feedback
            return {
                'reviewer': reviewer_type,
                'type': reviewer_type,
                'focus': get_reviewer_focus(reviewer_type),
                'output': output,
                'rating': 'good',
                'score': 4,
                'comments': [output] if output else [],
                'suggestions': [],
                'sections': [],
                'points': []
            }

        except Exception as e:
            return {
                'reviewer': reviewer_type,
                'type': reviewer_type,
                'focus': get_reviewer_focus(reviewer_type),
                'error': str(e),
                'rating': 'unknown',
                'score': 0
            }

    def add_reviewer(self, reviewer):
        """Add a custom reviewer to the panel.

        Args:
            reviewer: Reviewer definition dict.
        """
        name = reviewer.get('name', f'custom_{len(self._reviewers)}')
        self._reviewers[name] = {
            'name': name,
            'focus': reviewer.get('focus', 'Custom review'),
            'prompt': reviewer.get('prompt', ''),
            'type': 'custom',
            'content': reviewer.get('prompt', '')
        }

    def get_feedback(self, reviewer_type, sermon):
        """Get feedback from a specific reviewer.

        Args:
            reviewer_type: Type of reviewer to use.
            sermon: Sermon text to review.

        Returns:
            dict: Feedback from the reviewer.

        Raises:
            EmptySermonError: If sermon is empty.
            ReviewerNotFoundError: If reviewer type not found.
        """
        if not sermon or not sermon.strip():
            raise EmptySermonError("Sermon cannot be empty")

        if reviewer_type not in self._reviewers:
            raise ReviewerNotFoundError(f"Reviewer not found: {reviewer_type}")

        prompt = self._get_reviewer_prompt(reviewer_type)
        feedback = self._execute_review(reviewer_type, sermon, prompt)

        return feedback

    def get_all_feedback(self, sermon, reviewers=None, sermon_id=None, parallel=False):
        """Get feedback from all or specified reviewers.

        Args:
            sermon: Sermon text to review.
            reviewers: Optional list of specific reviewer types.
            sermon_id: Optional sermon ID for database storage.
            parallel: Whether to run reviews in parallel.

        Returns:
            list: List of feedback from all reviewers.
        """
        if not sermon or not sermon.strip():
            raise EmptySermonError("Sermon cannot be empty")

        if reviewers:
            reviewer_types = reviewers
        else:
            # Include default and any added custom reviewers
            reviewer_types = list(self._reviewers.keys())
        feedbacks = []

        if parallel:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(self.get_feedback, rt, sermon): rt
                    for rt in reviewer_types
                }
                for future in concurrent.futures.as_completed(futures):
                    try:
                        feedback = future.result()
                        feedbacks.append(feedback)
                        if sermon_id and self.db_conn:
                            store_feedback(self.db_conn, sermon_id, feedback.get('reviewer'), feedback)
                    except Exception:
                        pass
        else:
            for reviewer_type in reviewer_types:
                try:
                    feedback = self.get_feedback(reviewer_type, sermon)
                    feedbacks.append(feedback)
                    if sermon_id and self.db_conn:
                        store_feedback(self.db_conn, sermon_id, reviewer_type, feedback)
                except ReviewerNotFoundError:
                    pass

        return feedbacks

    def add_custom_reviewer(self, reviewer):
        """Add a custom reviewer to the panel.

        Args:
            reviewer: CustomReviewer instance or dict with identifier, name, focus_area.
        """
        if hasattr(reviewer, 'identifier'):
            identifier = reviewer.identifier
            self._reviewers[identifier] = {
                'name': reviewer.name,
                'identifier': identifier,
                'focus': reviewer.focus_area,
                'prompt': reviewer.prompt_template or '',
                'type': 'custom'
            }
        else:
            identifier = reviewer.get('identifier', reviewer.get('name', '').lower().replace(' ', '_'))
            self._reviewers[identifier] = {
                'name': reviewer.get('name', identifier),
                'identifier': identifier,
                'focus': reviewer.get('focus_area', reviewer.get('focus', '')),
                'prompt': reviewer.get('prompt_template', reviewer.get('prompt', '')),
                'type': 'custom'
            }

    def has_reviewer(self, identifier):
        """Check if a reviewer exists.

        Args:
            identifier: Reviewer identifier.

        Returns:
            bool: True if reviewer exists.
        """
        return identifier in self._reviewers

    def list_all_reviewers(self):
        """List all reviewers including custom ones.

        Returns:
            list: List of reviewer info dicts.
        """
        return [
            {
                'identifier': key,
                'name': value.get('name', key),
                'focus': value.get('focus', ''),
                'type': value.get('type', 'default')
            }
            for key, value in self._reviewers.items()
        ]
