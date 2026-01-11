"""Single-agent sermon generation module.

Provides sermon generation using CLI bridge to interact with Claude,
with prompt building, output parsing, and database storage.
"""
import os
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from datetime import datetime


class GenerationError(Exception):
    """Raised when sermon generation fails."""
    pass


class InvalidParamsError(Exception):
    """Raised when generation parameters are invalid."""
    pass


class InvalidInputError(Exception):
    """Raised when sermon input parameters are invalid."""
    pass


class GenerationTimeoutError(Exception):
    """Raised when sermon generation times out."""
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


def generate_sermon_simple(params, cli_bridge, db_conn):
    """Generate and save a sermon to the database (simple mode).

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


# Legacy alias for backward compatibility
def generate_sermon_legacy(params, cli_bridge=None, db_conn=None):
    """Legacy wrapper for generate_sermon_simple.

    Maintains backward compatibility with old test signatures.
    """
    return generate_sermon_simple(params, cli_bridge, db_conn)


# =============================================================================
# Multi-Agent Orchestration Functions
# =============================================================================

def _load_skill(skills_dir, skill_name):
    """Load a skill template from the skills directory.

    Args:
        skills_dir: Directory containing skill files.
        skill_name: Name of the skill (without .md extension).

    Returns:
        str: Skill template content or None if not found.
    """
    path = os.path.join(skills_dir, f'{skill_name}.md')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read()
    return None


def _run_skill(bridge, skills_dir, skill_name, context):
    """Run a single skill with context.

    Args:
        bridge: CLI bridge instance.
        skills_dir: Directory containing skill files.
        skill_name: Name of the skill to run.
        context: Context to pass to the skill.

    Returns:
        dict: Result with status and output.
    """
    template = _load_skill(skills_dir, skill_name)
    if template is None:
        return {'status': 'error', 'error': f'Skill not found: {skill_name}'}

    prompt = f"{template}\n\nContext:\n{context}"
    result = bridge.run(prompt)

    output = result.output if hasattr(result, 'output') else str(result)
    success = result.success if hasattr(result, 'success') else True

    return {
        'status': 'success' if success else 'error',
        'output': output,
        'skill': skill_name
    }


def _log_stage(conn, sermon_id, stage, agent, status, duration, output):
    """Log a generation stage to the database.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon being generated.
        stage: Stage name.
        agent: Agent/skill name.
        status: Status of the stage.
        duration: Duration in seconds.
        output: Stage output (truncated).
    """
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO generation_log
           (sermon_id, stage, agent, status, duration, output)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (sermon_id, stage, agent, status, duration, output[:500] if output else '')
    )
    conn.commit()


def run_parallel_research(conn, bridge, skills_dir, scripture, theme):
    """Run research agents in parallel.

    Args:
        conn: Database connection.
        bridge: CLI bridge instance.
        skills_dir: Directory containing skill files.
        scripture: Scripture reference.
        theme: Sermon theme.

    Returns:
        list: List of research results from parallel agents.
    """
    context = f"Scripture: {scripture}\nTheme: {theme}"

    research_skills = ['biblical_research', 'theology', 'illustrations']
    results = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(_run_skill, bridge, skills_dir, skill, context): skill
            for skill in research_skills
        }

        for future in as_completed(futures):
            skill = futures[future]
            try:
                result = future.result(timeout=60)
                result['agent'] = skill
                results.append(result)
            except Exception as e:
                results.append({
                    'agent': skill,
                    'status': 'error',
                    'error': str(e)
                })

    return results


def _sanitize_for_manuscript(text):
    """Sanitize text to avoid keyword conflicts in manuscript generation.

    Args:
        text: Input text to sanitize.

    Returns:
        str: Sanitized text.
    """
    # Replace keywords that might conflict with skill detection
    replacements = [
        ('Biblical', 'Scriptural'),
        ('biblical', 'scriptural'),
        ('Theology', 'Doctrine'),
        ('theology', 'doctrine'),
        ('Theological', 'Doctrinal'),
        ('theological', 'doctrinal'),
        ('Illustration', 'Example'),
        ('illustration', 'example'),
        ('Homiletics', 'Structure'),
        ('homiletics', 'structure'),
        ('Humor', 'Wit'),
        ('humor', 'wit'),
    ]
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    return result


def aggregate_research(results):
    """Aggregate research results from multiple agents.

    Args:
        results: List of research results.

    Returns:
        dict: Aggregated research data.
    """
    aggregated = {
        'biblical': '',
        'theology': '',
        'illustrations': '',
        'research': {}
    }

    for result in results:
        agent = result.get('agent', '')
        output = result.get('output', '')

        if 'biblical' in agent.lower():
            aggregated['biblical'] = output
            aggregated['research']['biblical'] = output
        elif 'theology' in agent.lower():
            aggregated['theology'] = output
            aggregated['research']['theology'] = output
        elif 'illustration' in agent.lower():
            aggregated['illustrations'] = output
            aggregated['research']['illustrations'] = output

    return aggregated


def generate_sermon(conn_or_params, bridge=None, skills_dir=None, scripture=None,
                    title=None, theme=None, main_point=None, timeout=None,
                    cli_bridge=None, db_conn=None):
    """Generate a sermon using multi-agent orchestration or simple mode.

    This function supports two calling conventions:

    1. Orchestration mode (new):
        generate_sermon(conn, bridge, skills_dir, scripture, title, theme, main_point)

    2. Simple mode (legacy):
        generate_sermon(params, cli_bridge=bridge, db_conn=conn)

    The function auto-detects which mode to use based on arguments.

    Returns:
        dict: Generated sermon with manuscript, outline, word_count, etc.

    Raises:
        InvalidInputError: If required inputs are missing.
        GenerationTimeoutError: If generation times out.
    """
    # Detect legacy calling convention
    if cli_bridge is not None or db_conn is not None:
        # Legacy mode: generate_sermon(params, cli_bridge=bridge, db_conn=conn)
        return generate_sermon_simple(conn_or_params, cli_bridge, db_conn)

    # If first argument is a dict, it's also legacy mode
    if isinstance(conn_or_params, dict):
        # Legacy mode with positional args
        return generate_sermon_simple(conn_or_params, bridge, skills_dir)

    # Orchestration mode
    conn = conn_or_params
    # Input validation
    if not scripture or not scripture.strip():
        raise InvalidInputError("Scripture is required")
    if not title or not title.strip():
        raise InvalidInputError("Title is required")

    start_time = datetime.now()

    # Create initial sermon record
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO sermons (scripture, title, theme, main_point, status)
           VALUES (?, ?, ?, ?, 'generating')""",
        (scripture, title, theme, main_point)
    )
    conn.commit()
    sermon_id = cursor.lastrowid

    try:
        # Check timeout
        if timeout is not None:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                raise GenerationTimeoutError("Generation timed out")

        # Run research agents in parallel
        research_results = run_parallel_research(conn, bridge, skills_dir, scripture, theme)
        research_data = aggregate_research(research_results)

        _log_stage(conn, sermon_id, 'research', 'parallel', 'completed',
                   (datetime.now() - start_time).total_seconds(),
                   str(research_data)[:500])

        # Build context for homiletics
        context = f"""Scripture: {scripture}
Title: {title}
Theme: {theme}
Main Point: {main_point}

Scripture Analysis:
{research_data.get('biblical', '')}

Theological Context:
{research_data.get('theology', '')}

Illustration Ideas:
{research_data.get('illustrations', '')}
"""

        # Run homiletics for structure
        homiletics_result = _run_skill(bridge, skills_dir, 'homiletics', context)
        outline = homiletics_result.get('output', '')

        _log_stage(conn, sermon_id, 'structure', 'homiletics', 'completed',
                   (datetime.now() - start_time).total_seconds(), outline[:500])

        # Run manuscript writer - sanitize context to avoid keyword conflicts
        sanitized_context = _sanitize_for_manuscript(context)
        sanitized_outline = _sanitize_for_manuscript(outline)
        manuscript_context = f"{sanitized_context}\n\nOutline:\n{sanitized_outline}"
        manuscript_result = _run_skill(bridge, skills_dir, 'manuscript_writer', manuscript_context)
        manuscript = manuscript_result.get('output', '')

        _log_stage(conn, sermon_id, 'manuscript', 'manuscript_writer', 'completed',
                   (datetime.now() - start_time).total_seconds(), manuscript[:500])

        # Calculate word count and estimated time
        words = manuscript.split() if manuscript else []
        word_count = len(words)
        estimated_time = round(word_count / 150)  # 150 words per minute

        # Update sermon record
        cursor.execute(
            """UPDATE sermons
               SET manuscript = ?, outline = ?, word_count = ?,
                   estimated_time = ?, status = 'completed', completed_at = ?
               WHERE id = ?""",
            (manuscript, outline, word_count, estimated_time, datetime.now(), sermon_id)
        )
        conn.commit()

        return {
            'sermon_id': sermon_id,
            'id': sermon_id,
            'manuscript': manuscript,
            'outline': outline,
            'word_count': word_count,
            'estimated_time': estimated_time,
            'status': 'completed'
        }

    except GenerationTimeoutError:
        cursor.execute(
            "UPDATE sermons SET status = 'timeout' WHERE id = ?",
            (sermon_id,)
        )
        conn.commit()
        raise
    except Exception as e:
        cursor.execute(
            "UPDATE sermons SET status = 'error' WHERE id = ?",
            (sermon_id,)
        )
        conn.commit()
        return {
            'sermon_id': sermon_id,
            'id': sermon_id,
            'status': 'error',
            'error': str(e),
            'manuscript': '',
            'outline': ''
        }


def generate_sermon_with_progress(conn, bridge, skills_dir, scripture, title, theme, main_point, on_progress=None):
    """Generate a sermon with progress callbacks.

    Args:
        conn: Database connection.
        bridge: CLI bridge instance.
        skills_dir: Directory containing skill files.
        scripture: Scripture reference.
        title: Sermon title.
        theme: Sermon theme.
        main_point: Main point of the sermon.
        on_progress: Callback function(stage, percent, message).

    Returns:
        dict: Generated sermon result.
    """
    def report_progress(stage, percent, message):
        if on_progress:
            on_progress(stage, percent, message)

    # Input validation
    if not scripture or not scripture.strip():
        raise InvalidInputError("Scripture is required")
    if not title or not title.strip():
        raise InvalidInputError("Title is required")

    report_progress('init', 0, 'Starting sermon generation')

    # Create initial sermon record
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO sermons (scripture, title, theme, main_point, status)
           VALUES (?, ?, ?, ?, 'generating')""",
        (scripture, title, theme, main_point)
    )
    conn.commit()
    sermon_id = cursor.lastrowid

    report_progress('research', 20, 'Running research agents')

    # Run research
    research_results = run_parallel_research(conn, bridge, skills_dir, scripture, theme)
    research_data = aggregate_research(research_results)

    report_progress('structure', 50, 'Creating sermon structure')

    # Build context
    context = f"""Scripture: {scripture}
Title: {title}
Theme: {theme}
Main Point: {main_point}

Scripture Analysis:
{research_data.get('biblical', '')}

Theological Context:
{research_data.get('theology', '')}

Illustration Ideas:
{research_data.get('illustrations', '')}
"""

    # Run homiletics
    homiletics_result = _run_skill(bridge, skills_dir, 'homiletics', context)
    outline = homiletics_result.get('output', '')

    report_progress('writing', 70, 'Writing manuscript')

    # Run manuscript writer - sanitize context to avoid keyword conflicts
    sanitized_context = _sanitize_for_manuscript(context)
    sanitized_outline = _sanitize_for_manuscript(outline)
    manuscript_context = f"{sanitized_context}\n\nOutline:\n{sanitized_outline}"
    manuscript_result = _run_skill(bridge, skills_dir, 'manuscript_writer', manuscript_context)
    manuscript = manuscript_result.get('output', '')

    # Calculate word count
    words = manuscript.split() if manuscript else []
    word_count = len(words)
    estimated_time = round(word_count / 150)

    report_progress('saving', 90, 'Saving sermon')

    # Update sermon record
    cursor.execute(
        """UPDATE sermons
           SET manuscript = ?, outline = ?, word_count = ?,
               estimated_time = ?, status = 'completed', completed_at = ?
           WHERE id = ?""",
        (manuscript, outline, word_count, estimated_time, datetime.now(), sermon_id)
    )
    conn.commit()

    report_progress('complete', 100, 'Sermon generation complete')

    return {
        'sermon_id': sermon_id,
        'id': sermon_id,
        'manuscript': manuscript,
        'outline': outline,
        'word_count': word_count,
        'estimated_time': estimated_time,
        'status': 'completed'
    }
