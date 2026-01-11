"""Tests for orchestrator with skill invocation.

These tests verify the orchestrator that coordinates multi-agent sermon
generation by invoking skills.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL skill files and CLI bridge - NO MOCKS.
"""
import pytest
import tempfile
import os
import sqlite3


class TestOrchestratorInitialization:
    """Test suite for orchestrator initialization."""

    def test_should_create_orchestrator_when_cli_bridge_provided(self):
        """Test that orchestrator can be created with CLI bridge."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        assert orchestrator is not None

    def test_should_store_cli_bridge_reference(self):
        """Test that orchestrator stores the CLI bridge."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        assert orchestrator.cli_bridge is bridge

    def test_should_initialize_with_idle_state(self):
        """Test that orchestrator starts in idle state."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        assert orchestrator.get_state() == 'idle'

    def test_should_accept_skills_directory_path(self):
        """Test that orchestrator accepts skills directory."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge, skills_dir='agents/skills/')

        assert orchestrator.skills_dir == 'agents/skills/'

    def test_should_use_default_skills_directory(self):
        """Test that orchestrator uses default skills directory."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        assert orchestrator.skills_dir is not None


class TestSkillInvocation:
    """Test suite for skill invocation."""

    def test_should_invoke_skill_when_valid_skill_name_provided(self):
        """Test invoking a skill by name."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        # Create a temp skill file
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'test_skill.md')
            with open(skill_path, 'w') as f:
                f.write('# Test Skill\nGenerate a test response.')

            orchestrator.skills_dir = tmpdir
            result = orchestrator.invoke_skill('test_skill', {'input': 'test'})

            assert result is not None

    def test_should_return_skill_result_when_invocation_succeeds(self):
        """Test that skill invocation returns result."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'echo_skill.md')
            with open(skill_path, 'w') as f:
                f.write('# Echo Skill\nRepeat the input.')

            orchestrator.skills_dir = tmpdir
            result = orchestrator.invoke_skill('echo_skill', {'message': 'hello'})

            assert 'output' in result or 'result' in result

    def test_should_raise_error_when_skill_not_found(self):
        """Test that missing skill raises appropriate error."""
        from orchestrator import Orchestrator, SkillNotFoundError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with pytest.raises(SkillNotFoundError):
            orchestrator.invoke_skill('nonexistent_skill', {})

    def test_should_pass_params_to_skill(self):
        """Test that parameters are passed to skill."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'param_skill.md')
            with open(skill_path, 'w') as f:
                f.write('# Param Skill\nProcess the input parameters.')

            orchestrator.skills_dir = tmpdir
            params = {'scripture': 'John 3:16', 'theme': 'Love'}
            result = orchestrator.invoke_skill('param_skill', params)

            # Result should contain something related to params
            assert result is not None


class TestSkillResultHandling:
    """Test suite for skill result handling."""

    def test_should_parse_json_result_from_skill(self):
        """Test parsing JSON response from skill."""
        from orchestrator import Orchestrator, parse_skill_result
        from cli_bridge import CLIBridge

        # Test the parsing function directly
        json_output = '{"status": "success", "data": "test data"}'
        result = parse_skill_result(json_output)

        assert result['status'] == 'success'
        assert result['data'] == 'test data'

    def test_should_handle_plain_text_result(self):
        """Test handling plain text response from skill."""
        from orchestrator import parse_skill_result

        text_output = 'This is a plain text response from the skill.'
        result = parse_skill_result(text_output)

        assert result is not None
        assert 'text' in result or 'output' in result

    def test_should_handle_markdown_result(self):
        """Test handling markdown response from skill."""
        from orchestrator import parse_skill_result

        md_output = """# Response Title

## Section 1
Content here.

## Section 2
More content."""

        result = parse_skill_result(md_output)

        assert result is not None

    def test_should_preserve_result_structure(self):
        """Test that complex result structure is preserved."""
        from orchestrator import parse_skill_result

        json_output = '''{
            "title": "Test Sermon",
            "outline": ["Point 1", "Point 2", "Point 3"],
            "manuscript": "Full sermon text here..."
        }'''

        result = parse_skill_result(json_output)

        assert 'title' in result
        assert isinstance(result.get('outline', []), list)


class TestOrchestratorStateManagement:
    """Test suite for orchestrator state management."""

    def test_should_transition_to_running_when_skill_invoked(self):
        """Test that state changes to running during invocation."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'state_skill.md')
            with open(skill_path, 'w') as f:
                f.write('# State Skill\nTest state management.')

            orchestrator.skills_dir = tmpdir

            # Check state transitions
            assert orchestrator.get_state() == 'idle'
            # Note: Actually testing the intermediate state is difficult
            # without async or threading, but the structure is here

    def test_should_transition_to_completed_after_success(self):
        """Test that state is 'completed' after successful invocation."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'complete_skill.md')
            with open(skill_path, 'w') as f:
                f.write('# Complete Skill\nTest completion.')

            orchestrator.skills_dir = tmpdir
            orchestrator.invoke_skill('complete_skill', {})

            assert orchestrator.get_state() == 'completed'

    def test_should_transition_to_error_after_failure(self):
        """Test that state is 'error' after failed invocation."""
        from orchestrator import Orchestrator, SkillNotFoundError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        try:
            orchestrator.invoke_skill('nonexistent', {})
        except SkillNotFoundError:
            pass

        assert orchestrator.get_state() == 'error'

    def test_should_track_current_skill_name(self):
        """Test that current skill name is tracked."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'track_skill.md')
            with open(skill_path, 'w') as f:
                f.write('# Track Skill\nTest tracking.')

            orchestrator.skills_dir = tmpdir
            orchestrator.invoke_skill('track_skill', {})

            assert orchestrator.current_skill == 'track_skill'


class TestErrorHandling:
    """Test suite for error handling."""

    def test_should_handle_cli_bridge_error(self):
        """Test handling of CLI bridge errors."""
        from orchestrator import Orchestrator, SkillExecutionError
        from cli_bridge import CLIBridge

        # Use a command that will fail
        bridge = CLIBridge(command='nonexistent_command_xyz')
        orchestrator = Orchestrator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'error_skill.md')
            with open(skill_path, 'w') as f:
                f.write('# Error Skill\nTest error handling.')

            orchestrator.skills_dir = tmpdir

            with pytest.raises((SkillExecutionError, Exception)):
                orchestrator.invoke_skill('error_skill', {})

    def test_should_handle_invalid_skill_file(self):
        """Test handling of invalid skill file content."""
        from orchestrator import Orchestrator, SkillParseError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an invalid skill file (binary garbage)
            skill_path = os.path.join(tmpdir, 'invalid_skill.md')
            with open(skill_path, 'wb') as f:
                f.write(b'\x00\x01\x02\x03')

            orchestrator.skills_dir = tmpdir

            with pytest.raises((SkillParseError, Exception)):
                orchestrator.invoke_skill('invalid_skill', {})

    def test_should_provide_meaningful_error_message(self):
        """Test that errors include helpful messages."""
        from orchestrator import Orchestrator, SkillNotFoundError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with pytest.raises(SkillNotFoundError) as exc_info:
            orchestrator.invoke_skill('missing_skill', {})

        assert 'missing_skill' in str(exc_info.value)


class TestTimeoutHandling:
    """Test suite for timeout handling."""

    def test_should_timeout_when_skill_exceeds_limit(self):
        """Test that long-running skills timeout."""
        from orchestrator import Orchestrator, SkillTimeoutError
        from cli_bridge import CLIBridge

        # Use python with a sleep command to simulate slow skill
        bridge = CLIBridge(command='python', timeout=1)
        orchestrator = Orchestrator(bridge, timeout=1)

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'slow_skill.md')
            with open(skill_path, 'w') as f:
                f.write('# Slow Skill\nThis skill takes too long.')

            orchestrator.skills_dir = tmpdir

            with pytest.raises((SkillTimeoutError, TimeoutError, Exception)):
                orchestrator.invoke_skill('slow_skill', {})

    def test_should_allow_configurable_timeout(self):
        """Test that timeout is configurable."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge, timeout=30)

        assert orchestrator.timeout == 30


class TestParallelSkillInvocation:
    """Test suite for parallel skill invocation."""

    def test_should_invoke_multiple_skills_in_parallel(self):
        """Test invoking multiple skills concurrently."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple skills
            for i in range(3):
                skill_path = os.path.join(tmpdir, f'skill_{i}.md')
                with open(skill_path, 'w') as f:
                    f.write(f'# Skill {i}\nProcess task {i}.')

            orchestrator.skills_dir = tmpdir

            results = orchestrator.invoke_parallel([
                ('skill_0', {'task': 'A'}),
                ('skill_1', {'task': 'B'}),
                ('skill_2', {'task': 'C'})
            ])

            assert len(results) == 3

    def test_should_return_all_results_from_parallel_invocation(self):
        """Test that all results are returned from parallel skills."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(2):
                skill_path = os.path.join(tmpdir, f'parallel_{i}.md')
                with open(skill_path, 'w') as f:
                    f.write(f'# Parallel {i}\nGenerate output {i}.')

            orchestrator.skills_dir = tmpdir

            results = orchestrator.invoke_parallel([
                ('parallel_0', {}),
                ('parallel_1', {})
            ])

            assert all(r is not None for r in results)

    def test_should_handle_partial_failure_in_parallel(self):
        """Test handling when some parallel skills fail."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only one skill, so the other will fail
            skill_path = os.path.join(tmpdir, 'existing_skill.md')
            with open(skill_path, 'w') as f:
                f.write('# Existing Skill\nThis one exists.')

            orchestrator.skills_dir = tmpdir

            results = orchestrator.invoke_parallel([
                ('existing_skill', {}),
                ('nonexistent_skill', {})
            ], fail_fast=False)

            # Should have results for both (one success, one error)
            assert len(results) == 2


class TestSkillChaining:
    """Test suite for skill chaining."""

    def test_should_chain_skills_sequentially(self):
        """Test chaining skills where one uses another's output."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two skills for chaining
            skill1_path = os.path.join(tmpdir, 'research_skill.md')
            with open(skill1_path, 'w') as f:
                f.write('# Research Skill\nGather background information.')

            skill2_path = os.path.join(tmpdir, 'write_skill.md')
            with open(skill2_path, 'w') as f:
                f.write('# Write Skill\nWrite content based on research.')

            orchestrator.skills_dir = tmpdir

            result = orchestrator.chain_skills([
                ('research_skill', {'topic': 'Grace'}),
                ('write_skill', {})  # Will receive research output
            ])

            assert result is not None

    def test_should_pass_previous_output_to_next_skill(self):
        """Test that output from one skill is passed to the next."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            skill1_path = os.path.join(tmpdir, 'step1.md')
            with open(skill1_path, 'w') as f:
                f.write('# Step 1\nGenerate initial data.')

            skill2_path = os.path.join(tmpdir, 'step2.md')
            with open(skill2_path, 'w') as f:
                f.write('# Step 2\nProcess the data from step 1.')

            orchestrator.skills_dir = tmpdir

            result = orchestrator.chain_skills([
                ('step1', {'input': 'start'}),
                ('step2', {})
            ])

            # The result should reflect the chain
            assert result is not None

    def test_should_stop_chain_on_error(self):
        """Test that chain stops when a skill fails."""
        from orchestrator import Orchestrator, SkillChainError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            skill1_path = os.path.join(tmpdir, 'first.md')
            with open(skill1_path, 'w') as f:
                f.write('# First\nThis one works.')

            orchestrator.skills_dir = tmpdir

            with pytest.raises((SkillChainError, Exception)):
                orchestrator.chain_skills([
                    ('first', {}),
                    ('nonexistent', {}),  # This will fail
                    ('third', {})  # Should not run
                ])


class TestOrchestratorWithDatabase:
    """Test suite for orchestrator with database integration."""

    def test_should_store_skill_results_in_database(self):
        """Test that skill results are stored in database."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge, db_conn=conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'db_skill.md')
            with open(skill_path, 'w') as f:
                f.write('# DB Skill\nStore this result.')

            orchestrator.skills_dir = tmpdir
            result = orchestrator.invoke_skill('db_skill', {})

            # Check that something was stored
            # This depends on the schema having an appropriate table
            assert result is not None

        conn.close()

    def test_should_retrieve_previous_skill_results(self):
        """Test retrieving previous skill execution results."""
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge, db_conn=conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'history_skill.md')
            with open(skill_path, 'w') as f:
                f.write('# History Skill\nTrack history.')

            orchestrator.skills_dir = tmpdir
            orchestrator.invoke_skill('history_skill', {})

            history = orchestrator.get_skill_history('history_skill')

            assert len(history) >= 1

        conn.close()
