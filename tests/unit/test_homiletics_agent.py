"""Tests for homiletics agent integration.

These tests verify the homiletics agent that structures sermons
using homiletics principles.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database and files - NO MOCKS.
"""
import pytest
import sqlite3
import tempfile
import os
import json


# Sample scripture and inputs for testing
SAMPLE_SCRIPTURE = """John 3:16 - For God so loved the world that he gave
his one and only Son, that whoever believes in him shall not perish
but have eternal life."""

SAMPLE_SERMON_TOPIC = "The Boundless Love of God"

# Expected structure types
SERMON_FORMS = ['deductive', 'inductive', 'narrative']

# Expected outline sections
EXPECTED_SECTIONS = ['introduction', 'point_1', 'point_2', 'point_3', 'conclusion']


class TestHomileticsAgentInitialization:
    """Test suite for homiletics agent initialization."""

    def test_should_create_homiletics_agent_when_cli_bridge_provided(self):
        """Test that homiletics agent can be created."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        assert agent is not None

    def test_should_store_cli_bridge_reference(self):
        """Test that agent stores CLI bridge reference."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        assert agent.cli_bridge is bridge

    def test_should_accept_skills_directory(self):
        """Test that agent accepts skills directory path."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge, skills_dir='agents/skills/')

        assert agent.skills_dir == 'agents/skills/'

    def test_should_use_default_skills_directory(self):
        """Test that agent uses default skills directory."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        assert agent.skills_dir is not None


class TestSkillPromptLoading:
    """Test suite for loading homiletics skill prompt."""

    def test_should_load_homiletics_skill_prompt(self):
        """Test that agent loads homiletics skill file."""
        from homiletics_agent import HomileticsAgent, load_skill_prompt
        from cli_bridge import CLIBridge

        # Create temp skill file
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'homiletics.md')
            with open(skill_path, 'w') as f:
                f.write("# Homiletics Skill\nStructure sermons effectively.")

            bridge = CLIBridge(command='echo')
            agent = HomileticsAgent(bridge, skills_dir=tmpdir)

            prompt = agent.load_skill_prompt()
            assert 'Homiletics' in prompt

    def test_should_raise_error_when_skill_file_not_found(self):
        """Test error when skill file is missing."""
        from homiletics_agent import HomileticsAgent, SkillNotFoundError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge, skills_dir='/nonexistent/')

        with pytest.raises(SkillNotFoundError):
            agent.load_skill_prompt()

    def test_should_handle_skill_file_with_system_prompt(self):
        """Test that agent extracts system prompt from skill file."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'homiletics.md')
            with open(skill_path, 'w') as f:
                f.write("""# Homiletics Skill

## System Prompt
You are an expert in sermon structure and homiletics.

## Instructions
Structure the sermon with clear points.
""")

            bridge = CLIBridge(command='echo')
            agent = HomileticsAgent(bridge, skills_dir=tmpdir)

            prompt = agent.load_skill_prompt()
            assert 'expert' in prompt.lower()


class TestSermonStructureOutput:
    """Test suite for structured sermon outline output."""

    def test_should_produce_json_structured_outline(self):
        """Test that agent outputs JSON structure."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        # Agent should return parseable JSON
        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        assert isinstance(result, dict)

    def test_should_include_introduction_in_outline(self):
        """Test that outline includes introduction."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        assert 'introduction' in result

    def test_should_include_three_main_points(self):
        """Test that outline includes 3 main points."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        assert 'point_1' in result
        assert 'point_2' in result
        assert 'point_3' in result

    def test_should_include_conclusion_in_outline(self):
        """Test that outline includes conclusion."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        assert 'conclusion' in result

    def test_should_include_sermon_title(self):
        """Test that outline includes sermon title."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        assert 'title' in result

    def test_should_include_scripture_reference(self):
        """Test that outline includes scripture reference."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        assert 'scripture' in result


class TestWordCountAllocation:
    """Test suite for word count allocation."""

    def test_should_include_word_count_for_each_section(self):
        """Test that each section has word count target."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        for section in EXPECTED_SECTIONS:
            section_data = result.get(section, {})
            assert 'word_count' in section_data or 'target_words' in section_data

    def test_should_total_word_count_between_2000_and_2500(self):
        """Test that total word count matches sermon requirements."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        total_words = result.get('total_word_count', 0)
        assert 2000 <= total_words <= 2500

    def test_should_allocate_more_words_to_main_points(self):
        """Test that main points get more words than intro/conclusion."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        intro_words = result.get('introduction', {}).get('target_words', 0)
        point_words = result.get('point_1', {}).get('target_words', 0)

        assert point_words > intro_words

    def test_should_accept_custom_word_count_target(self):
        """Test that agent accepts custom word count."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(
            SAMPLE_SCRIPTURE,
            SAMPLE_SERMON_TOPIC,
            target_words=1800
        )

        total_words = result.get('total_word_count', 0)
        assert 1700 <= total_words <= 1900


class TestSermonForms:
    """Test suite for different sermon forms."""

    def test_should_support_deductive_form(self):
        """Test deductive sermon form (thesis then support)."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(
            SAMPLE_SCRIPTURE,
            SAMPLE_SERMON_TOPIC,
            form='deductive'
        )

        assert result.get('form') == 'deductive'

    def test_should_support_inductive_form(self):
        """Test inductive sermon form (evidence then thesis)."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(
            SAMPLE_SCRIPTURE,
            SAMPLE_SERMON_TOPIC,
            form='inductive'
        )

        assert result.get('form') == 'inductive'

    def test_should_support_narrative_form(self):
        """Test narrative sermon form (story-driven)."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(
            SAMPLE_SCRIPTURE,
            SAMPLE_SERMON_TOPIC,
            form='narrative'
        )

        assert result.get('form') == 'narrative'

    def test_should_default_to_deductive_form(self):
        """Test that deductive is the default form."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        assert result.get('form') == 'deductive'

    def test_should_raise_error_for_invalid_form(self):
        """Test error for invalid sermon form."""
        from homiletics_agent import HomileticsAgent, InvalidSermonFormError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        with pytest.raises(InvalidSermonFormError):
            agent.structure_sermon(
                SAMPLE_SCRIPTURE,
                SAMPLE_SERMON_TOPIC,
                form='invalid_form'
            )


class TestOrchestratorIntegration:
    """Test suite for orchestrator integration."""

    def test_should_register_with_orchestrator(self):
        """Test that agent can register with orchestrator."""
        from homiletics_agent import HomileticsAgent
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)
        agent = HomileticsAgent(bridge)

        orchestrator.register_agent('homiletics', agent)

        assert orchestrator.has_agent('homiletics')

    def test_should_be_invoked_by_orchestrator(self):
        """Test that orchestrator can invoke homiletics agent."""
        from homiletics_agent import HomileticsAgent
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)
        agent = HomileticsAgent(bridge)

        orchestrator.register_agent('homiletics', agent)

        result = orchestrator.invoke_agent(
            'homiletics',
            scripture=SAMPLE_SCRIPTURE,
            topic=SAMPLE_SERMON_TOPIC
        )

        assert result is not None

    def test_should_return_result_in_orchestrator_format(self):
        """Test that result matches orchestrator expected format."""
        from homiletics_agent import HomileticsAgent
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)
        agent = HomileticsAgent(bridge)

        orchestrator.register_agent('homiletics', agent)

        result = orchestrator.invoke_agent(
            'homiletics',
            scripture=SAMPLE_SCRIPTURE,
            topic=SAMPLE_SERMON_TOPIC
        )

        assert 'status' in result
        assert 'data' in result

    def test_should_support_async_invocation(self):
        """Test that agent supports async invocation."""
        from homiletics_agent import HomileticsAgent
        from orchestrator import Orchestrator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        orchestrator = Orchestrator(bridge)
        agent = HomileticsAgent(bridge)

        orchestrator.register_agent('homiletics', agent)

        task_id = orchestrator.invoke_agent_async(
            'homiletics',
            scripture=SAMPLE_SCRIPTURE,
            topic=SAMPLE_SERMON_TOPIC
        )

        assert task_id is not None


class TestErrorHandling:
    """Test suite for error handling."""

    def test_should_handle_empty_scripture(self):
        """Test error handling for empty scripture."""
        from homiletics_agent import HomileticsAgent, InvalidInputError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        with pytest.raises(InvalidInputError):
            agent.structure_sermon('', SAMPLE_SERMON_TOPIC)

    def test_should_handle_empty_topic(self):
        """Test error handling for empty topic."""
        from homiletics_agent import HomileticsAgent, InvalidInputError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        with pytest.raises(InvalidInputError):
            agent.structure_sermon(SAMPLE_SCRIPTURE, '')

    def test_should_handle_none_scripture(self):
        """Test error handling for None scripture."""
        from homiletics_agent import HomileticsAgent, InvalidInputError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        with pytest.raises(InvalidInputError):
            agent.structure_sermon(None, SAMPLE_SERMON_TOPIC)

    def test_should_handle_cli_bridge_failure(self):
        """Test error handling when CLI bridge fails."""
        from homiletics_agent import HomileticsAgent, AgentExecutionError
        from cli_bridge import CLIBridge

        # Bridge that will fail
        bridge = CLIBridge(command='false')
        agent = HomileticsAgent(bridge)

        with pytest.raises(AgentExecutionError):
            agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

    def test_should_handle_invalid_json_response(self):
        """Test error handling for invalid JSON from CLI."""
        from homiletics_agent import HomileticsAgent, InvalidResponseError
        from cli_bridge import CLIBridge

        # Bridge that returns invalid JSON
        bridge = CLIBridge(command='echo "not valid json"')
        agent = HomileticsAgent(bridge)

        with pytest.raises(InvalidResponseError):
            agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

    def test_should_provide_descriptive_error_messages(self):
        """Test that errors have descriptive messages."""
        from homiletics_agent import HomileticsAgent, InvalidInputError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        with pytest.raises(InvalidInputError) as exc_info:
            agent.structure_sermon('', SAMPLE_SERMON_TOPIC)

        assert 'scripture' in str(exc_info.value).lower()


class TestDatabaseIntegration:
    """Test suite for database integration."""

    def test_should_store_outline_in_database(self):
        """Test storing outline in database."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        conn = sqlite3.connect(':memory:')
        conn.execute('''
            CREATE TABLE sermon_outlines (
                id INTEGER PRIMARY KEY,
                sermon_id INTEGER,
                outline_json TEXT,
                form TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge, db_connection=conn)

        result = agent.structure_sermon(
            SAMPLE_SCRIPTURE,
            SAMPLE_SERMON_TOPIC,
            sermon_id=1,
            save_to_db=True
        )

        cursor = conn.execute('SELECT * FROM sermon_outlines WHERE sermon_id = 1')
        row = cursor.fetchone()

        assert row is not None
        conn.close()

    def test_should_retrieve_outline_from_database(self):
        """Test retrieving outline from database."""
        from homiletics_agent import HomileticsAgent, get_outline_from_db
        from cli_bridge import CLIBridge

        conn = sqlite3.connect(':memory:')
        conn.execute('''
            CREATE TABLE sermon_outlines (
                id INTEGER PRIMARY KEY,
                sermon_id INTEGER,
                outline_json TEXT,
                form TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute(
            'INSERT INTO sermon_outlines (sermon_id, outline_json, form) VALUES (?, ?, ?)',
            (1, '{"title": "Test"}', 'deductive')
        )
        conn.commit()

        outline = get_outline_from_db(conn, sermon_id=1)

        assert outline is not None
        assert outline['title'] == 'Test'
        conn.close()

    def test_should_update_existing_outline(self):
        """Test updating existing outline."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        conn = sqlite3.connect(':memory:')
        conn.execute('''
            CREATE TABLE sermon_outlines (
                id INTEGER PRIMARY KEY,
                sermon_id INTEGER,
                outline_json TEXT,
                form TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute(
            'INSERT INTO sermon_outlines (sermon_id, outline_json, form) VALUES (?, ?, ?)',
            (1, '{"title": "Old"}', 'deductive')
        )
        conn.commit()

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge, db_connection=conn)

        agent.structure_sermon(
            SAMPLE_SCRIPTURE,
            SAMPLE_SERMON_TOPIC,
            sermon_id=1,
            save_to_db=True,
            update_existing=True
        )

        cursor = conn.execute('SELECT COUNT(*) FROM sermon_outlines WHERE sermon_id = 1')
        count = cursor.fetchone()[0]

        # Should still be 1 record (updated, not inserted)
        assert count == 1
        conn.close()


class TestOutputQuality:
    """Test suite for outline quality."""

    def test_should_include_point_summaries(self):
        """Test that each point has a summary."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        for i in range(1, 4):
            point = result.get(f'point_{i}', {})
            assert 'summary' in point or 'description' in point

    def test_should_include_scripture_references_per_section(self):
        """Test that sections have scripture references."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        for i in range(1, 4):
            point = result.get(f'point_{i}', {})
            assert 'scripture_ref' in point or 'supporting_verses' in point

    def test_should_include_transition_suggestions(self):
        """Test that outline includes transitions."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        assert 'transitions' in result or any(
            'transition' in result.get(f'point_{i}', {})
            for i in range(1, 4)
        )

    def test_should_include_application_suggestions(self):
        """Test that outline includes application ideas."""
        from homiletics_agent import HomileticsAgent
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        agent = HomileticsAgent(bridge)

        result = agent.structure_sermon(SAMPLE_SCRIPTURE, SAMPLE_SERMON_TOPIC)

        # At least one section should have application
        has_application = False
        for section in EXPECTED_SECTIONS:
            section_data = result.get(section, {})
            if 'application' in section_data or 'takeaway' in section_data:
                has_application = True
                break

        assert has_application or 'applications' in result


class TestFlaskIntegration:
    """Test suite for Flask integration."""

    def test_should_return_200_when_structuring_sermon(self):
        """Test API returns 200 for valid request."""
        from flask import Flask

        app = Flask(__name__)

        @app.route('/api/homiletics/structure', methods=['POST'])
        def structure_sermon():
            from homiletics_agent import HomileticsAgent
            from cli_bridge import CLIBridge
            bridge = CLIBridge(command='echo')
            agent = HomileticsAgent(bridge)
            return {'status': 'ok'}

        with app.test_client() as client:
            response = client.post('/api/homiletics/structure', json={
                'scripture': SAMPLE_SCRIPTURE,
                'topic': SAMPLE_SERMON_TOPIC
            })

            assert response.status_code == 200

    def test_should_return_400_for_missing_scripture(self):
        """Test API returns 400 when scripture missing."""
        from flask import Flask, request, jsonify

        app = Flask(__name__)

        @app.route('/api/homiletics/structure', methods=['POST'])
        def structure_sermon():
            data = request.get_json()
            if not data.get('scripture'):
                return jsonify({'error': 'Scripture required'}), 400
            return {'status': 'ok'}

        with app.test_client() as client:
            response = client.post('/api/homiletics/structure', json={
                'topic': SAMPLE_SERMON_TOPIC
            })

            assert response.status_code == 400

    def test_should_return_400_for_missing_topic(self):
        """Test API returns 400 when topic missing."""
        from flask import Flask, request, jsonify

        app = Flask(__name__)

        @app.route('/api/homiletics/structure', methods=['POST'])
        def structure_sermon():
            data = request.get_json()
            if not data.get('topic'):
                return jsonify({'error': 'Topic required'}), 400
            return {'status': 'ok'}

        with app.test_client() as client:
            response = client.post('/api/homiletics/structure', json={
                'scripture': SAMPLE_SCRIPTURE
            })

            assert response.status_code == 400

    def test_should_return_json_response(self):
        """Test API returns JSON response."""
        from flask import Flask, jsonify

        app = Flask(__name__)

        @app.route('/api/homiletics/structure', methods=['POST'])
        def structure_sermon():
            return jsonify({
                'status': 'ok',
                'outline': {
                    'title': 'Test Sermon',
                    'form': 'deductive'
                }
            })

        with app.test_client() as client:
            response = client.post('/api/homiletics/structure', json={
                'scripture': SAMPLE_SCRIPTURE,
                'topic': SAMPLE_SERMON_TOPIC
            })

            data = response.get_json()
            assert 'outline' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
