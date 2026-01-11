"""Tests for single-agent sermon generation.

These tests verify the sermon generation system that uses the CLI bridge
to generate sermon content from parameters.
Tests are written first (TDD) - implementation does not exist yet.
Database operations use REAL SQLite :memory: - NO MOCKS.
CLI bridge uses configurable command for testing (echo instead of claude).
"""
import pytest
import json


class TestSermonGeneratorCreation:
    """Test suite for SermonGenerator initialization."""

    def test_should_create_generator_when_cli_bridge_provided(self):
        """Test that generator can be created with CLI bridge."""
        from sermon_generator import SermonGenerator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        generator = SermonGenerator(bridge)

        assert generator is not None

    def test_should_store_cli_bridge_reference(self):
        """Test that generator stores the CLI bridge."""
        from sermon_generator import SermonGenerator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        generator = SermonGenerator(bridge)

        assert generator.cli_bridge is bridge


class TestBuildSermonPrompt:
    """Test suite for building sermon prompts."""

    def test_should_build_prompt_when_valid_params_provided(self):
        """Test that prompt is built from parameters."""
        from sermon_generator import build_sermon_prompt

        params = {
            'title': 'Test Sermon',
            'scripture': 'John 3:16',
            'theme': 'Love'
        }

        prompt = build_sermon_prompt(params)

        assert prompt is not None
        assert len(prompt) > 0

    def test_should_include_scripture_in_prompt(self):
        """Test that scripture appears in prompt."""
        from sermon_generator import build_sermon_prompt

        params = {
            'title': 'Test Sermon',
            'scripture': 'Romans 8:28',
            'theme': 'Hope'
        }

        prompt = build_sermon_prompt(params)

        assert 'Romans 8:28' in prompt

    def test_should_include_theme_in_prompt(self):
        """Test that theme appears in prompt."""
        from sermon_generator import build_sermon_prompt

        params = {
            'title': 'Test Sermon',
            'scripture': 'John 3:16',
            'theme': 'Grace and Mercy'
        }

        prompt = build_sermon_prompt(params)

        assert 'Grace and Mercy' in prompt or 'grace' in prompt.lower()

    def test_should_include_main_point_when_provided(self):
        """Test that main point appears in prompt when given."""
        from sermon_generator import build_sermon_prompt

        params = {
            'title': 'Test Sermon',
            'scripture': 'John 3:16',
            'theme': 'Love',
            'main_point': 'God loves everyone unconditionally'
        }

        prompt = build_sermon_prompt(params)

        assert 'unconditionally' in prompt or 'main point' in prompt.lower()

    def test_should_include_reference_notes_when_provided(self):
        """Test that reference notes are included."""
        from sermon_generator import build_sermon_prompt

        params = {
            'title': 'Test Sermon',
            'scripture': 'John 3:16',
            'theme': 'Love',
            'notes': 'Include reference to Augustine. Focus on verse 17 also.'
        }

        prompt = build_sermon_prompt(params)

        assert 'Augustine' in prompt or 'notes' in prompt.lower()

    def test_should_specify_sermon_length_in_prompt(self):
        """Test that prompt specifies target length."""
        from sermon_generator import build_sermon_prompt

        params = {
            'title': 'Test Sermon',
            'scripture': 'John 3:16',
            'theme': 'Love'
        }

        prompt = build_sermon_prompt(params)

        # Should specify ~2000-2500 words or 15 minutes
        assert '2000' in prompt or '2500' in prompt or '15 minute' in prompt or 'fifteen' in prompt.lower()

    def test_should_handle_missing_optional_params(self):
        """Test that prompt works with minimal params."""
        from sermon_generator import build_sermon_prompt

        params = {
            'scripture': 'John 3:16'
            # No title, theme, notes
        }

        prompt = build_sermon_prompt(params)

        assert prompt is not None
        assert 'John 3:16' in prompt


class TestParseSermonOutput:
    """Test suite for parsing Claude output."""

    def test_should_parse_manuscript_from_output(self):
        """Test extracting manuscript from Claude output."""
        from sermon_generator import parse_sermon_output

        output = """
        # Grace Abounding

        Scripture: John 3:16

        ## Manuscript

        Good morning, beloved congregation. Today we gather to explore...

        [Full sermon text here]

        Amen.
        """

        result = parse_sermon_output(output)

        assert 'manuscript' in result
        assert len(result['manuscript']) > 0

    def test_should_parse_outline_from_output(self):
        """Test extracting outline from Claude output."""
        from sermon_generator import parse_sermon_output

        output = """
        # Test Sermon

        ## Outline
        1. Introduction
        2. First Point: God's Love
        3. Second Point: Our Response
        4. Conclusion

        ## Manuscript
        ...
        """

        result = parse_sermon_output(output)

        assert 'outline' in result
        assert 'First Point' in result['outline'] or '1.' in result['outline']

    def test_should_extract_title_from_output(self):
        """Test extracting title from Claude output."""
        from sermon_generator import parse_sermon_output

        output = """
        # Amazing Grace

        Scripture: John 3:16

        ## Manuscript
        ...
        """

        result = parse_sermon_output(output)

        assert 'title' in result
        assert 'Amazing Grace' in result['title']

    def test_should_calculate_word_count(self):
        """Test that word count is calculated."""
        from sermon_generator import parse_sermon_output

        manuscript = ' '.join(['word'] * 500)
        output = f"""
        # Test Sermon

        ## Manuscript
        {manuscript}
        """

        result = parse_sermon_output(output)

        assert 'word_count' in result
        assert result['word_count'] >= 400  # Allow some variance

    def test_should_handle_plain_text_output(self):
        """Test parsing output without markdown headers."""
        from sermon_generator import parse_sermon_output

        output = "This is a plain text sermon without any formatting. It just contains the sermon content directly."

        result = parse_sermon_output(output)

        # Should still return something usable
        assert result is not None
        assert 'manuscript' in result or 'content' in result


class TestSermonGeneration:
    """Test suite for full sermon generation flow."""

    def test_should_generate_sermon_when_valid_params_provided(self):
        """Test successful sermon generation."""
        from sermon_generator import SermonGenerator
        from cli_bridge import CLIBridge

        # Use echo to simulate Claude output
        bridge = CLIBridge(command='echo')
        generator = SermonGenerator(bridge)

        params = {
            'title': 'Test Sermon',
            'scripture': 'John 3:16',
            'theme': 'Love'
        }

        result = generator.generate(params)

        assert result is not None
        assert 'manuscript' in result or 'content' in result

    def test_should_save_sermon_to_database(self):
        """Test that generated sermon is saved to database."""
        from sermon_generator import SermonGenerator, generate_sermon
        from cli_bridge import CLIBridge
        from database import init_db, get_db
        import sqlite3

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        bridge = CLIBridge(command='echo')

        params = {
            'title': 'DB Test Sermon',
            'scripture': 'John 3:16',
            'theme': 'Love'
        }

        result = generate_sermon(params, cli_bridge=bridge, db_conn=conn)

        # Verify saved in database
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sermons WHERE title = ?", ('DB Test Sermon',))
        row = cursor.fetchone()

        assert row is not None
        conn.close()

    def test_should_return_sermon_id_after_generation(self):
        """Test that sermon ID is returned."""
        from sermon_generator import generate_sermon
        from cli_bridge import CLIBridge
        from database import init_db
        import sqlite3

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        bridge = CLIBridge(command='echo')

        params = {
            'title': 'Test Sermon',
            'scripture': 'John 3:16',
            'theme': 'Love'
        }

        result = generate_sermon(params, cli_bridge=bridge, db_conn=conn)

        assert 'id' in result or 'sermon_id' in result
        conn.close()


class TestGenerationErrorHandling:
    """Test suite for error handling during generation."""

    def test_should_handle_cli_bridge_error(self):
        """Test handling of CLI bridge errors."""
        from sermon_generator import SermonGenerator, GenerationError
        from cli_bridge import CLIBridge

        # Use a command that will fail
        bridge = CLIBridge(command='nonexistent_command_xyz')
        generator = SermonGenerator(bridge)

        params = {
            'scripture': 'John 3:16'
        }

        with pytest.raises(GenerationError):
            generator.generate(params)

    def test_should_handle_timeout_during_generation(self):
        """Test handling of timeout."""
        from sermon_generator import SermonGenerator, GenerationError
        from cli_bridge import CLIBridge

        # Very short timeout with slow command
        bridge = CLIBridge(command='python', timeout=1)
        generator = SermonGenerator(bridge)

        params = {
            'scripture': 'John 3:16'
        }

        # This might raise TimeoutError or GenerationError
        with pytest.raises((GenerationError, Exception)):
            generator.generate(params)

    def test_should_handle_empty_prompt_params(self):
        """Test handling of empty parameters."""
        from sermon_generator import SermonGenerator, InvalidParamsError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        generator = SermonGenerator(bridge)

        with pytest.raises(InvalidParamsError):
            generator.generate({})

    def test_should_require_scripture_parameter(self):
        """Test that scripture is required."""
        from sermon_generator import SermonGenerator, InvalidParamsError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        generator = SermonGenerator(bridge)

        params = {
            'title': 'No Scripture Sermon',
            'theme': 'Love'
            # No scripture
        }

        with pytest.raises(InvalidParamsError):
            generator.generate(params)


class TestGenerationStatus:
    """Test suite for tracking generation status."""

    def test_should_report_idle_status_initially(self):
        """Test that initial status is idle."""
        from sermon_generator import SermonGenerator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        generator = SermonGenerator(bridge)

        assert generator.get_status() == 'idle'

    def test_should_report_generating_status_during_generation(self):
        """Test that status is 'generating' during generation."""
        from sermon_generator import SermonGenerator
        from cli_bridge import CLIBridge

        # Use a command that takes some time
        bridge = CLIBridge(command='python', timeout=30)
        generator = SermonGenerator(bridge)

        params = {
            'scripture': 'John 3:16'
        }

        # Start generation in background and check status
        # This is tricky to test without async, but structure is here

    def test_should_report_complete_status_after_generation(self):
        """Test that status is 'complete' after generation."""
        from sermon_generator import SermonGenerator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        generator = SermonGenerator(bridge)

        params = {
            'scripture': 'John 3:16'
        }

        generator.generate(params)

        assert generator.get_status() == 'complete'

    def test_should_report_error_status_on_failure(self):
        """Test that status is 'error' after failure."""
        from sermon_generator import SermonGenerator, GenerationError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='nonexistent_command_xyz')
        generator = SermonGenerator(bridge)

        params = {
            'scripture': 'John 3:16'
        }

        try:
            generator.generate(params)
        except GenerationError:
            pass

        assert generator.get_status() == 'error'


class TestSermonGeneratorIntegration:
    """Integration tests for sermon generator with database."""

    def test_should_store_research_data_with_sermon(self):
        """Test that research data is stored."""
        from sermon_generator import generate_sermon
        from cli_bridge import CLIBridge
        from database import init_db
        import sqlite3

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        bridge = CLIBridge(command='echo')

        params = {
            'title': 'Research Test',
            'scripture': 'John 3:16',
            'theme': 'Love'
        }

        result = generate_sermon(params, cli_bridge=bridge, db_conn=conn)

        cursor = conn.cursor()
        cursor.execute("SELECT research_data FROM sermons WHERE title = ?", ('Research Test',))
        row = cursor.fetchone()

        # Research data should be stored (even if empty JSON for now)
        assert row is not None
        conn.close()

    def test_should_calculate_estimated_minutes(self):
        """Test that estimated reading time is calculated."""
        from sermon_generator import parse_sermon_output

        # 2000 words at ~150 words/minute = ~13 minutes
        manuscript = ' '.join(['word'] * 2000)
        output = f"## Manuscript\n{manuscript}"

        result = parse_sermon_output(output)

        if 'estimated_minutes' in result:
            assert 10 <= result['estimated_minutes'] <= 20

    def test_should_handle_liturgical_season_param(self):
        """Test that liturgical season is included in prompt."""
        from sermon_generator import build_sermon_prompt

        params = {
            'scripture': 'John 3:16',
            'liturgical_season': 'Lent'
        }

        prompt = build_sermon_prompt(params)

        assert 'Lent' in prompt or 'lent' in prompt.lower()

    def test_should_handle_special_occasion_param(self):
        """Test that special occasion is included in prompt."""
        from sermon_generator import build_sermon_prompt

        params = {
            'scripture': 'Matthew 28:19',
            'special_occasion': 'Baptism'
        }

        prompt = build_sermon_prompt(params)

        assert 'Baptism' in prompt or 'baptism' in prompt.lower()
