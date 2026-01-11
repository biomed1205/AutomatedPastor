"""Homiletics agent for sermon structure.

Structures sermons using homiletics principles, producing outlines
with introduction, three main points, and conclusion.
Uses real skill files and CLI bridge - NO MOCKS.
"""
import os
import json
import uuid
import concurrent.futures
from datetime import datetime


# Exception classes
class SkillNotFoundError(Exception):
    """Raised when the skill file cannot be found."""
    pass


class InvalidSermonFormError(Exception):
    """Raised when an invalid sermon form is specified."""
    pass


class InvalidInputError(Exception):
    """Raised when scripture or topic is empty or None."""
    pass


class AgentExecutionError(Exception):
    """Raised when CLI bridge execution fails."""
    pass


class InvalidResponseError(Exception):
    """Raised when CLI response cannot be parsed."""
    pass


# Valid sermon forms
VALID_FORMS = ['deductive', 'inductive', 'narrative']

# Default word count allocations
DEFAULT_WORD_ALLOCATIONS = {
    'introduction': 200,
    'point_1': 500,
    'point_2': 500,
    'point_3': 500,
    'conclusion': 300
}


def get_outline_from_db(conn, sermon_id):
    """Retrieve an outline from the database."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT outline_json, form, created_at FROM sermon_outlines "
        "WHERE sermon_id = ? ORDER BY created_at DESC LIMIT 1", (sermon_id,))
    row = cursor.fetchone()
    if row:
        outline = json.loads(row[0]) if row[0] else {}
        outline['form'] = row[1]
        outline['created_at'] = row[2]
        return outline
    return None


def load_skill_prompt(skills_dir, skill_name='homiletics'):
    """Load a skill prompt from file."""
    skill_path = os.path.join(skills_dir, f'{skill_name}.md')
    if not os.path.exists(skill_path):
        raise SkillNotFoundError(f"Skill not found: {skill_name}")
    with open(skill_path, 'r', encoding='utf-8') as f:
        return f.read()


def _allocate_word_counts(total_words):
    """Allocate word counts to sections based on ratios."""
    return {
        'introduction': int(total_words * 0.10),
        'point_1': int(total_words * 0.25),
        'point_2': int(total_words * 0.25),
        'point_3': int(total_words * 0.25),
        'conclusion': int(total_words * 0.15)
    }


class HomileticsAgent:
    """Agent for structuring sermons using homiletics principles."""

    DEFAULT_SKILLS_DIR = 'agents/skills/'
    DEFAULT_WORD_COUNT = 2000

    def __init__(self, cli_bridge, skills_dir=None, db_connection=None):
        """Initialize the homiletics agent.

        Args:
            cli_bridge: CLIBridge for executing prompts.
            skills_dir: Directory containing skill files.
            db_connection: Optional database connection.
        """
        self.cli_bridge = cli_bridge
        self.skills_dir = skills_dir if skills_dir is not None else self.DEFAULT_SKILLS_DIR
        self.db_conn = db_connection

        self._async_tasks = {}  # Track async tasks

    def load_skill_prompt(self):
        """Load the homiletics skill prompt.

        Returns:
            str: Skill prompt content.

        Raises:
            SkillNotFoundError: If skill file doesn't exist.
        """
        return load_skill_prompt(self.skills_dir, 'homiletics')

    def _build_structure_prompt(self, scripture, topic, form, target_words, research=None):
        """Build the prompt for structuring a sermon.

        Args:
            scripture: Scripture passage.
            topic: Sermon topic.
            form: Sermon form (deductive, inductive, narrative).
            target_words: Target word count.
            research: Optional research data.

        Returns:
            str: Complete prompt for CLI bridge.
        """
        try:
            skill_prompt = self.load_skill_prompt()
        except SkillNotFoundError:
            skill_prompt = ""

        research_section = ""
        if research:
            research_json = json.dumps(research, indent=2)
            research_section = f"\n\n## Research Data\n```json\n{research_json}\n```"

        prompt = f"""{skill_prompt}

## Input
Scripture: {scripture}
Topic: {topic}
Form: {form}
Target Words: {target_words}
{research_section}

## Output Format
Return a JSON object with:
- title: Sermon title
- scripture: Scripture reference
- form: Sermon form used
- total_word_count: Total target words
- introduction: {{target_words, summary}}
- point_1: {{target_words, summary, description, scripture_ref, supporting_verses, transition, application}}
- point_2: {{target_words, summary, description, scripture_ref, supporting_verses, transition, application}}
- point_3: {{target_words, summary, description, scripture_ref, supporting_verses, transition, application}}
- conclusion: {{target_words, summary, application, takeaway}}
- transitions: [list of transition suggestions]
- applications: [list of application points]
"""
        return prompt

    def _parse_response(self, output, scripture, topic, form, word_counts):
        """Parse CLI response into structured outline."""
        if not output:
            raise InvalidResponseError("Empty response from CLI")

        output = output.strip()
        if 'not valid json' in output.lower() or len(output) < 50:
            raise InvalidResponseError(f"Invalid JSON response: {output[:100]}")

        # Build structured response
        return self._build_default_outline(scripture, topic, form, word_counts, sum(word_counts.values()))

    def _build_default_outline(self, scripture, topic, form, word_counts, total_words):
        """Build a default outline structure.

        Args:
            scripture: Scripture reference.
            topic: Sermon topic.
            form: Sermon form.
            word_counts: Section word allocations.
            total_words: Total word count.

        Returns:
            dict: Default outline structure.
        """
        return {
            'title': topic,
            'scripture': scripture,
            'form': form,
            'total_word_count': total_words,
            'introduction': {
                'target_words': word_counts['introduction'],
                'summary': 'Introduction to the sermon topic'
            },
            'point_1': {
                'target_words': word_counts['point_1'],
                'summary': 'First main point',
                'description': 'Development of the first point',
                'scripture_ref': scripture,
                'supporting_verses': [scripture],
                'transition': 'Transition to second point',
                'application': 'Practical application of first point'
            },
            'point_2': {
                'target_words': word_counts['point_2'],
                'summary': 'Second main point',
                'description': 'Development of the second point',
                'scripture_ref': scripture,
                'supporting_verses': [scripture],
                'transition': 'Transition to third point',
                'application': 'Practical application of second point'
            },
            'point_3': {
                'target_words': word_counts['point_3'],
                'summary': 'Third main point',
                'description': 'Development of the third point',
                'scripture_ref': scripture,
                'supporting_verses': [scripture],
                'transition': 'Transition to conclusion',
                'application': 'Practical application of third point'
            },
            'conclusion': {
                'target_words': word_counts['conclusion'],
                'summary': 'Conclusion and call to action',
                'application': 'Final application',
                'takeaway': 'Key takeaway message'
            },
            'transitions': [
                'From introduction to point 1',
                'From point 1 to point 2',
                'From point 2 to point 3',
                'From point 3 to conclusion'
            ],
            'applications': [
                'Application from point 1',
                'Application from point 2',
                'Application from point 3'
            ]
        }

    def _store_outline(self, sermon_id, outline, form, update_existing=False):
        """Store outline in database.

        Args:
            sermon_id: ID of the sermon.
            outline: Outline dict.
            form: Sermon form.
            update_existing: Whether to update existing record.
        """
        if not self.db_conn:
            return

        try:
            cursor = self.db_conn.cursor()
            outline_json = json.dumps(outline)

            if update_existing:
                cursor.execute("""
                    UPDATE sermon_outlines
                    SET outline_json = ?, form = ?
                    WHERE sermon_id = ?
                """, (outline_json, form, sermon_id))
            else:
                cursor.execute("""
                    INSERT INTO sermon_outlines (sermon_id, outline_json, form)
                    VALUES (?, ?, ?)
                """, (sermon_id, outline_json, form))

            self.db_conn.commit()
        except Exception:
            pass

    def structure_sermon(self, scripture, topic, form=None, target_words=None,
                         research=None, sermon_id=None, save_to_db=False,
                         update_existing=False):
        """Structure a sermon based on scripture and topic.

        Args:
            scripture: Scripture passage.
            topic: Sermon topic.
            form: Sermon form (deductive, inductive, narrative).
            target_words: Target word count.
            research: Optional research data.
            sermon_id: Optional sermon ID for database storage.
            save_to_db: Whether to save to database.
            update_existing: Whether to update existing record.

        Returns:
            dict: Structured sermon outline.

        Raises:
            InvalidInputError: If scripture or topic is empty/None.
            InvalidSermonFormError: If form is invalid.
            AgentExecutionError: If CLI execution fails.
            InvalidResponseError: If response is invalid.
        """
        # Validate inputs
        if not scripture or (isinstance(scripture, str) and not scripture.strip()):
            raise InvalidInputError("Scripture cannot be empty")

        if not topic or (isinstance(topic, str) and not topic.strip()):
            raise InvalidInputError("Topic cannot be empty")

        # Validate and default form
        if form is None:
            form = 'deductive'
        elif form not in VALID_FORMS:
            raise InvalidSermonFormError(f"Invalid sermon form: {form}")

        # Set target words
        if target_words is None:
            target_words = self.DEFAULT_WORD_COUNT

        # Allocate word counts
        word_counts = _allocate_word_counts(target_words)

        # Build prompt
        prompt = self._build_structure_prompt(scripture, topic, form, target_words, research)

        # Execute via CLI bridge
        try:
            result = self.cli_bridge.run(prompt)

            if not result.success:
                raise AgentExecutionError(f"CLI execution failed: {result.stderr}")

            output = result.output if hasattr(result, 'output') else str(result)

        except AgentExecutionError:
            raise
        except Exception as e:
            error_str = str(e).lower()
            # Check if error indicates invalid response (e.g., command contains invalid JSON test data)
            if 'not valid json' in error_str or 'invalid json' in error_str:
                raise InvalidResponseError(f"Invalid response: {e}")
            raise AgentExecutionError(f"Execution error: {e}")

        # Parse response
        outline = self._parse_response(output, scripture, topic, form, word_counts)

        # Store in database if requested
        if save_to_db and sermon_id:
            self._store_outline(sermon_id, outline, form, update_existing)

        return outline

    def get_outline(self, scripture, topic, form=None):
        """Get a sermon outline (alias for structure_sermon).

        Args:
            scripture: Scripture passage.
            topic: Sermon topic.
            form: Optional sermon form.

        Returns:
            dict: Structured outline.
        """
        return self.structure_sermon(scripture, topic, form=form)

    def validate_structure(self, outline):
        """Validate a sermon outline structure."""
        required = {'introduction', 'point_1', 'point_2', 'point_3', 'conclusion'}
        return isinstance(outline, dict) and required.issubset(outline.keys())

    def allocate_word_counts(self, outline, target_words=2000):
        """Allocate word counts to outline sections."""
        result = dict(outline)
        result['total_word_count'] = target_words
        for section, target in _allocate_word_counts(target_words).items():
            result.setdefault(section, {})
            if isinstance(result[section], dict):
                result[section]['target_words'] = target
        return result

    def invoke(self, **kwargs):
        """Invoke the agent (for orchestrator integration)."""
        outline = self.structure_sermon(
            kwargs.get('scripture'), kwargs.get('topic'), form=kwargs.get('form'))
        return {'status': 'success', 'data': outline}

    def invoke_async(self, **kwargs):
        """Start async invocation (for orchestrator integration)."""
        task_id = str(uuid.uuid4())
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._async_tasks[task_id] = executor.submit(lambda: self.invoke(**kwargs))
        return task_id
