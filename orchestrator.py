"""Orchestrator module for multi-agent sermon generation.

Coordinates skill invocation, manages workflow state, and tracks execution history.
Uses real skill files and CLI bridge - NO MOCKS.
"""
import os
import json
import concurrent.futures
from datetime import datetime


# Exception classes
class SkillNotFoundError(Exception):
    """Raised when a skill file cannot be found."""
    pass


class SkillExecutionError(Exception):
    """Raised when CLI bridge encounters an error during skill execution."""
    pass


class SkillParseError(Exception):
    """Raised when a skill file cannot be parsed."""
    pass


class SkillTimeoutError(Exception):
    """Raised when a skill execution exceeds the timeout limit."""
    pass


class SkillChainError(Exception):
    """Raised when an error occurs during skill chaining."""
    pass


def parse_skill_result(output):
    """Parse skill output to structured result.

    Attempts to parse as JSON first, falls back to text format.

    Args:
        output: Raw output string from skill execution.

    Returns:
        dict: Parsed result with either JSON content or text wrapper.
    """
    if not output:
        return {'output': '', 'text': ''}

    output = output.strip()

    # Try to parse as JSON
    try:
        result = json.loads(output)
        if isinstance(result, dict):
            return result
        return {'output': result, 'result': result}
    except (json.JSONDecodeError, TypeError):
        pass

    # Return as text/output wrapper
    return {'output': output, 'text': output}


class Orchestrator:
    """Orchestrator for multi-agent sermon generation.

    Coordinates skill invocation, manages workflow state, and integrates
    with database for execution history tracking.
    """

    DEFAULT_SKILLS_DIR = 'agents/skills/'
    DEFAULT_TIMEOUT = 300  # 5 minutes

    def __init__(self, cli_bridge, skills_dir=None, timeout=None, db_conn=None):
        """Initialize orchestrator.

        Args:
            cli_bridge: CLIBridge instance for executing skills.
            skills_dir: Path to skills directory. Defaults to 'agents/skills/'.
            timeout: Timeout in seconds for skill execution. Defaults to 300.
            db_conn: Optional database connection for history tracking.
        """
        self.cli_bridge = cli_bridge
        self.skills_dir = skills_dir if skills_dir is not None else self.DEFAULT_SKILLS_DIR
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self.db_conn = db_conn

        self._state = 'idle'
        self.current_skill = None
        self._history = {}  # In-memory history: {skill_name: [results]}

        # Initialize database table if connection provided
        if self.db_conn:
            self._init_skill_history_table()

    def _init_skill_history_table(self):
        """Create skill execution history table if it doesn't exist."""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skill_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL,
                    params TEXT,
                    result TEXT,
                    success BOOLEAN,
                    duration REAL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.db_conn.commit()
        except Exception:
            # Table may already exist or DB doesn't support this
            pass

    def get_state(self):
        """Get current orchestrator state.

        Returns:
            str: One of 'idle', 'running', 'completed', 'error'.
        """
        return self._state

    def _set_state(self, state):
        """Set orchestrator state."""
        self._state = state

    def _get_skill_path(self, skill_name):
        """Get the full path to a skill file.

        Args:
            skill_name: Name of the skill (without .md extension).

        Returns:
            str: Full path to skill file.

        Raises:
            SkillNotFoundError: If skill file doesn't exist.
        """
        skill_path = os.path.join(self.skills_dir, f'{skill_name}.md')

        if not os.path.exists(skill_path):
            self._set_state('error')
            raise SkillNotFoundError(f"Skill not found: {skill_name}")

        return skill_path

    def _read_skill_prompt(self, skill_path):
        """Read and validate skill prompt from file.

        Args:
            skill_path: Path to skill file.

        Returns:
            str: Skill prompt content.

        Raises:
            SkillParseError: If skill file cannot be read or is invalid.
        """
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Validate content is readable text
            if not content or not content.strip():
                raise SkillParseError(f"Skill file is empty: {skill_path}")

            return content

        except UnicodeDecodeError:
            self._set_state('error')
            raise SkillParseError(f"Skill file contains invalid content: {skill_path}")
        except Exception as e:
            if isinstance(e, SkillParseError):
                raise
            self._set_state('error')
            raise SkillParseError(f"Error reading skill file: {skill_path}: {e}")

    def _execute_skill(self, skill_prompt, params):
        """Execute a skill using the CLI bridge.

        Args:
            skill_prompt: The skill prompt text.
            params: Parameters to pass to the skill.

        Returns:
            dict: Parsed skill result.

        Raises:
            SkillExecutionError: If CLI bridge encounters an error.
            SkillTimeoutError: If execution times out.
        """
        # Format the prompt with parameters
        prompt_text = skill_prompt
        if params:
            params_json = json.dumps(params, indent=2)
            prompt_text = f"{skill_prompt}\n\n## Input Parameters\n```json\n{params_json}\n```"

        try:
            result = self.cli_bridge.run(prompt_text)

            if not result.success:
                raise SkillExecutionError(f"Skill execution failed: {result.stderr}")

            return parse_skill_result(result.output)

        except Exception as e:
            if 'timeout' in str(e).lower() or 'TimeoutError' in type(e).__name__:
                raise SkillTimeoutError(f"Skill execution timed out: {e}")
            if isinstance(e, (SkillExecutionError, SkillTimeoutError)):
                raise
            raise SkillExecutionError(f"Skill execution error: {e}")

    def _store_result(self, skill_name, params, result, success, duration=0.0):
        """Store skill execution result in history.

        Args:
            skill_name: Name of the skill.
            params: Parameters used.
            result: Execution result.
            success: Whether execution succeeded.
            duration: Execution duration in seconds.
        """
        # Store in memory
        if skill_name not in self._history:
            self._history[skill_name] = []

        record = {
            'skill_name': skill_name,
            'params': params,
            'result': result,
            'success': success,
            'duration': duration,
            'executed_at': datetime.now().isoformat()
        }
        self._history[skill_name].append(record)

        # Store in database if available
        if self.db_conn:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    INSERT INTO skill_executions (skill_name, params, result, success, duration)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    skill_name,
                    json.dumps(params) if params else None,
                    json.dumps(result) if result else None,
                    success,
                    duration
                ))
                self.db_conn.commit()
            except Exception:
                # Database storage is optional
                pass

    def invoke_skill(self, skill_name, params):
        """Invoke a single skill.

        Args:
            skill_name: Name of the skill to invoke.
            params: Parameters to pass to the skill.

        Returns:
            dict: Skill execution result.

        Raises:
            SkillNotFoundError: If skill file doesn't exist.
            SkillParseError: If skill file is invalid.
            SkillExecutionError: If execution fails.
            SkillTimeoutError: If execution times out.
        """
        self._set_state('running')
        self.current_skill = skill_name

        start_time = datetime.now()

        try:
            # Get and read skill
            skill_path = self._get_skill_path(skill_name)
            skill_prompt = self._read_skill_prompt(skill_path)

            # Execute skill
            result = self._execute_skill(skill_prompt, params)

            duration = (datetime.now() - start_time).total_seconds()
            self._store_result(skill_name, params, result, True, duration)

            self._set_state('completed')
            return result

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self._store_result(skill_name, params, {'error': str(e)}, False, duration)
            self._set_state('error')
            raise

    def invoke_parallel(self, skills, fail_fast=True):
        """Invoke multiple skills in parallel.

        Args:
            skills: List of (skill_name, params) tuples.
            fail_fast: If True, raise on first error. If False, collect all results.

        Returns:
            list: List of results in same order as input skills.
        """
        self._set_state('running')
        results = [None] * len(skills)

        def execute_one(index, skill_name, params):
            try:
                skill_path = self._get_skill_path(skill_name)
                skill_prompt = self._read_skill_prompt(skill_path)
                result = self._execute_skill(skill_prompt, params)
                self._store_result(skill_name, params, result, True)
                return index, result, None
            except Exception as e:
                self._store_result(skill_name, params, {'error': str(e)}, False)
                return index, {'error': str(e)}, e

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(execute_one, i, skill_name, params)
                for i, (skill_name, params) in enumerate(skills)
            ]

            for future in concurrent.futures.as_completed(futures):
                index, result, error = future.result()
                results[index] = result

                if error and fail_fast:
                    self._set_state('error')
                    raise error

        self._set_state('completed')
        return results

    def chain_skills(self, skill_sequence):
        """Chain skills sequentially, passing output from one to the next.

        Args:
            skill_sequence: List of (skill_name, params) tuples.

        Returns:
            dict: Final skill result.

        Raises:
            SkillChainError: If any skill in the chain fails.
        """
        self._set_state('running')
        previous_result = None

        for i, (skill_name, params) in enumerate(skill_sequence):
            self.current_skill = skill_name

            try:
                # Merge previous result into params for subsequent skills
                if previous_result and i > 0:
                    merged_params = {**params, 'previous_output': previous_result}
                else:
                    merged_params = params

                skill_path = self._get_skill_path(skill_name)
                skill_prompt = self._read_skill_prompt(skill_path)
                previous_result = self._execute_skill(skill_prompt, merged_params)

                self._store_result(skill_name, merged_params, previous_result, True)

            except Exception as e:
                self._set_state('error')
                self._store_result(skill_name, params, {'error': str(e)}, False)
                raise SkillChainError(f"Chain failed at skill '{skill_name}': {e}")

        self._set_state('completed')
        return previous_result

    def get_skill_history(self, skill_name):
        """Get execution history for a skill.

        Args:
            skill_name: Name of the skill.

        Returns:
            list: List of execution records.
        """
        # Try database first
        if self.db_conn:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    SELECT skill_name, params, result, success, duration, executed_at
                    FROM skill_executions
                    WHERE skill_name = ?
                    ORDER BY executed_at DESC
                """, (skill_name,))

                rows = cursor.fetchall()
                if rows:
                    return [dict(row) for row in rows]
            except Exception:
                pass

        # Fall back to in-memory history
        return self._history.get(skill_name, [])
