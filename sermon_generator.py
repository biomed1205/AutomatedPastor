"""Single-agent sermon generation module.

Provides sermon generation using CLI bridge to interact with Claude,
with prompt building, output parsing, and database storage.
"""
import re
import json


class GenerationError(Exception):
    """Raised when sermon generation fails."""
    pass


class InvalidParamsError(Exception):
    """Raised when generation parameters are invalid."""
    pass


class SermonGenerator:
    """Generates sermons using CLI bridge.

    Attributes:
        cli_bridge: The CLI bridge for executing commands.
        status: Current generation status ('idle', 'generating', 'complete', 'error').
    """

    def __init__(self, cli_bridge):
        """Initialize with a CLI bridge.

        Args:
            cli_bridge: CLIBridge instance for command execution.
        """
        self.cli_bridge = cli_bridge
        self._status = 'idle'

    def get_status(self):
        """Get current generation status.

        Returns:
            str: One of 'idle', 'generating', 'complete', 'error'.
        """
        return self._status

    def generate(self, params):
        """Generate a sermon from parameters.

        Args:
            params: Dictionary with sermon parameters:
                - scripture (required): Scripture reference
                - title (optional): Sermon title
                - theme (optional): Main theme
                - main_point (optional): Central message
                - notes (optional): Reference notes
                - liturgical_season (optional): Liturgical season
                - special_occasion (optional): Special occasion

        Returns:
            dict: Parsed sermon result with manuscript, outline, etc.

        Raises:
            InvalidParamsError: If parameters are invalid or missing scripture.
            GenerationError: If generation fails.
        """
        # Validate parameters
        if not params:
            raise InvalidParamsError("Parameters cannot be empty")

        if 'scripture' not in params or not params['scripture']:
            raise InvalidParamsError("Scripture is required")

        self._status = 'generating'

        try:
            # Build prompt
            prompt = build_sermon_prompt(params)

            # Run through CLI bridge
            result = self.cli_bridge.run(prompt)

            if not result.success:
                self._status = 'error'
                raise GenerationError(f"CLI bridge failed: {result.stderr}")

            # Parse output
            parsed = parse_sermon_output(result.output)

            self._status = 'complete'
            return parsed

        except GenerationError:
            self._status = 'error'
            raise
        except Exception as e:
            self._status = 'error'
            raise GenerationError(str(e))


def build_sermon_prompt(params):
    """Build a sermon generation prompt from parameters.

    Args:
        params: Dictionary with sermon parameters.

    Returns:
        str: The complete prompt for Claude.
    """
    scripture = params.get('scripture', '')
    title = params.get('title', '')
    theme = params.get('theme', '')
    main_point = params.get('main_point', '')
    notes = params.get('notes', '')
    liturgical_season = params.get('liturgical_season', '')
    special_occasion = params.get('special_occasion', '')

    prompt_parts = []

    prompt_parts.append("Generate a sermon with the following requirements:")
    prompt_parts.append("")
    prompt_parts.append(f"Scripture: {scripture}")

    if title:
        prompt_parts.append(f"Title: {title}")

    if theme:
        prompt_parts.append(f"Theme: {theme}")

    if main_point:
        prompt_parts.append(f"Main Point: {main_point}")

    if liturgical_season:
        prompt_parts.append(f"Liturgical Season: {liturgical_season}")

    if special_occasion:
        prompt_parts.append(f"Special Occasion: {special_occasion}")

    if notes:
        prompt_parts.append(f"Additional Notes: {notes}")

    prompt_parts.append("")
    prompt_parts.append("Requirements:")
    prompt_parts.append("- Length: 2000-2500 words (approximately 15 minutes)")
    prompt_parts.append("- Theology: Wesleyan/United Methodist")
    prompt_parts.append("- Structure: Clear 3-point outline")
    prompt_parts.append("- Include: Scripture engagement, contemporary illustrations, practical application")
    prompt_parts.append("- Avoid: Personal stories, political content")
    prompt_parts.append("")
    prompt_parts.append("Format the output with:")
    prompt_parts.append("# [Title]")
    prompt_parts.append("## Outline")
    prompt_parts.append("[numbered outline]")
    prompt_parts.append("## Manuscript")
    prompt_parts.append("[full sermon text]")

    return '\n'.join(prompt_parts)


def parse_sermon_output(output):
    """Parse Claude's output into structured sermon data.

    Args:
        output: Raw text output from Claude.

    Returns:
        dict: Parsed sermon with keys:
            - title: Sermon title
            - outline: Sermon outline
            - manuscript: Full sermon text
            - word_count: Word count of manuscript
            - estimated_minutes: Estimated reading time
    """
    result = {
        'title': '',
        'outline': '',
        'manuscript': '',
        'word_count': 0,
        'estimated_minutes': 0
    }

    # Extract title (first # heading, may have leading whitespace)
    title_match = re.search(r'^\s*#\s+(.+?)$', output, re.MULTILINE)
    if title_match:
        result['title'] = title_match.group(1).strip()

    # Extract outline (between ## Outline and ## Manuscript)
    outline_match = re.search(r'##\s*Outline\s*\n(.*?)(?=##\s*Manuscript|$)', output, re.DOTALL | re.IGNORECASE)
    if outline_match:
        result['outline'] = outline_match.group(1).strip()

    # Extract manuscript (after ## Manuscript)
    manuscript_match = re.search(r'##\s*Manuscript\s*\n(.+?)$', output, re.DOTALL | re.IGNORECASE)
    if manuscript_match:
        result['manuscript'] = manuscript_match.group(1).strip()
    elif not result['manuscript']:
        # If no markdown structure, use entire output as manuscript
        result['manuscript'] = output.strip()
        result['content'] = output.strip()

    # Calculate word count
    if result['manuscript']:
        words = result['manuscript'].split()
        result['word_count'] = len(words)

        # Calculate estimated minutes (150 words/minute average)
        result['estimated_minutes'] = round(result['word_count'] / 150, 1)

    return result


def generate_sermon(params, cli_bridge, db_conn):
    """Generate and save a sermon to the database.

    Args:
        params: Dictionary with sermon parameters.
        cli_bridge: CLIBridge instance.
        db_conn: Database connection.

    Returns:
        dict: Result with sermon_id and generated content.
    """
    from database import init_db

    # Ensure database is initialized
    init_db(db_conn)

    # Generate sermon
    generator = SermonGenerator(cli_bridge)
    result = generator.generate(params)

    # Get values from params and result
    title = params.get('title', result.get('title', 'Untitled Sermon'))
    scripture = params.get('scripture', '')
    theme = params.get('theme', '')
    main_point = params.get('main_point', '')
    manuscript = result.get('manuscript', '')
    outline = result.get('outline', '')
    word_count = result.get('word_count', 0)
    estimated_minutes = result.get('estimated_minutes', 0)
    liturgical_season = params.get('liturgical_season', '')
    special_occasion = params.get('special_occasion', '')

    # Store research data as JSON
    research_data = json.dumps({
        'prompt_params': params,
        'raw_output': manuscript[:500] if manuscript else ''
    })

    # Save to database
    cursor = db_conn.cursor()
    cursor.execute("""
        INSERT INTO sermons (
            title, scripture, theme, main_point, manuscript, outline,
            word_count, estimated_minutes, liturgical_season, special_occasion,
            research_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title, scripture, theme, main_point, manuscript, outline,
        word_count, estimated_minutes, liturgical_season, special_occasion,
        research_data
    ))
    db_conn.commit()

    sermon_id = cursor.lastrowid

    result['id'] = sermon_id
    result['sermon_id'] = sermon_id

    return result
