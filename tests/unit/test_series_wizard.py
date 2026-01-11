"""Tests for sermon series creation wizard.

These tests verify the step-by-step wizard workflow for creating sermon series.
Enables guided creation of sermon series with validation at each step.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
import json
from datetime import datetime, date, timedelta


# Wizard steps
WIZARD_STEPS = {
    1: 'name_description',
    2: 'theme_dates',
    3: 'sermon_slots',
    4: 'passage_suggestions',
    5: 'review_create'
}


def create_test_db():
    """Create an in-memory test database for wizard testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row

    # Create series table
    conn.execute('''
        CREATE TABLE series (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            theme TEXT,
            start_date DATE,
            end_date DATE,
            status TEXT DEFAULT 'planning',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create wizard_progress table
    conn.execute('''
        CREATE TABLE wizard_progress (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            wizard_type TEXT NOT NULL DEFAULT 'series',
            current_step INTEGER DEFAULT 1,
            step_data TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, wizard_type)
        )
    ''')

    # Create sermon_slots table for planned sermons
    conn.execute('''
        CREATE TABLE sermon_slots (
            id INTEGER PRIMARY KEY,
            series_id INTEGER NOT NULL,
            slot_number INTEGER NOT NULL,
            title TEXT,
            scripture TEXT,
            notes TEXT,
            planned_date DATE,
            status TEXT DEFAULT 'planned',
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    return conn


class TestValidateStepOne:
    """Test suite for validating Step 1: Name and Description."""

    def test_should_validate_step_one_required_fields(self):
        """Test that step 1 validates required name field."""
        from series_wizard import validate_series_step

        data = {'name': '', 'description': 'Optional description'}

        errors = validate_series_step(1, data)

        assert len(errors) > 0
        assert any('name' in e.lower() for e in errors)

    def test_should_pass_step_one_with_valid_name(self):
        """Test that step 1 passes with valid name."""
        from series_wizard import validate_series_step

        data = {'name': 'Lent 2024', 'description': 'A journey through Lent'}

        errors = validate_series_step(1, data)

        assert errors == []

    def test_should_allow_empty_description_in_step_one(self):
        """Test that description is optional in step 1."""
        from series_wizard import validate_series_step

        data = {'name': 'Advent Series', 'description': ''}

        errors = validate_series_step(1, data)

        assert errors == []

    def test_should_validate_name_minimum_length(self):
        """Test that name must have minimum length."""
        from series_wizard import validate_series_step

        data = {'name': 'AB', 'description': ''}  # Too short

        errors = validate_series_step(1, data)

        assert len(errors) > 0


class TestValidateStepTwo:
    """Test suite for validating Step 2: Theme and Date Range."""

    def test_should_validate_step_two_date_range(self):
        """Test that step 2 validates date range."""
        from series_wizard import validate_series_step

        data = {
            'theme': 'Resurrection',
            'start_date': '2024-04-01',
            'end_date': '2024-03-01'  # End before start
        }

        errors = validate_series_step(2, data)

        assert len(errors) > 0
        assert any('date' in e.lower() for e in errors)

    def test_should_pass_step_two_with_valid_dates(self):
        """Test that step 2 passes with valid date range."""
        from series_wizard import validate_series_step

        data = {
            'theme': 'Hope and Renewal',
            'start_date': '2024-03-01',
            'end_date': '2024-04-15'
        }

        errors = validate_series_step(2, data)

        assert errors == []

    def test_should_allow_empty_theme_in_step_two(self):
        """Test that theme is optional in step 2."""
        from series_wizard import validate_series_step

        data = {
            'theme': '',
            'start_date': '2024-03-01',
            'end_date': '2024-04-15'
        }

        errors = validate_series_step(2, data)

        assert errors == []

    def test_should_validate_date_format(self):
        """Test that dates must be in valid format."""
        from series_wizard import validate_series_step

        data = {
            'theme': 'Test',
            'start_date': 'not-a-date',
            'end_date': '2024-04-15'
        }

        errors = validate_series_step(2, data)

        assert len(errors) > 0


class TestValidateStepThree:
    """Test suite for validating Step 3: Sermon Slots."""

    def test_should_validate_step_three_sermon_count(self):
        """Test that step 3 validates sermon count."""
        from series_wizard import validate_series_step

        data = {'sermon_count': 0}  # Must have at least 1

        errors = validate_series_step(3, data)

        assert len(errors) > 0

    def test_should_pass_step_three_with_valid_count(self):
        """Test that step 3 passes with valid sermon count."""
        from series_wizard import validate_series_step

        data = {'sermon_count': 6}

        errors = validate_series_step(3, data)

        assert errors == []

    def test_should_validate_maximum_sermon_count(self):
        """Test that there's a reasonable maximum sermon count."""
        from series_wizard import validate_series_step

        data = {'sermon_count': 100}  # Too many

        errors = validate_series_step(3, data)

        assert len(errors) > 0

    def test_should_accept_sermon_count_as_string(self):
        """Test that sermon count as string is converted."""
        from series_wizard import validate_series_step

        data = {'sermon_count': '6'}

        errors = validate_series_step(3, data)

        assert errors == []


class TestSaveWizardProgress:
    """Test suite for saving wizard progress."""

    def test_should_save_wizard_progress(self):
        """Test that wizard progress is saved."""
        from series_wizard import save_wizard_progress, load_wizard_progress

        conn = create_test_db()
        user_id = 1
        step = 2
        data = {'name': 'Test Series', 'description': 'Test'}

        result = save_wizard_progress(conn, user_id, step, data)

        assert result is True
        conn.close()

    def test_should_update_existing_progress(self):
        """Test that existing progress is updated."""
        from series_wizard import save_wizard_progress, load_wizard_progress

        conn = create_test_db()
        user_id = 1

        # Save initial progress
        save_wizard_progress(conn, user_id, 1, {'name': 'First'})
        # Update with new step
        save_wizard_progress(conn, user_id, 2, {'name': 'First', 'theme': 'Theme'})

        progress = load_wizard_progress(conn, user_id)
        assert progress['current_step'] == 2
        conn.close()

    def test_should_preserve_data_across_steps(self):
        """Test that data is preserved when moving between steps."""
        from series_wizard import save_wizard_progress, load_wizard_progress

        conn = create_test_db()
        user_id = 1

        # Save step 1 data
        save_wizard_progress(conn, user_id, 1, {'name': 'My Series', 'description': 'Desc'})
        # Save step 2 data (should merge)
        save_wizard_progress(conn, user_id, 2, {'theme': 'Hope', 'start_date': '2024-01-01'})

        progress = load_wizard_progress(conn, user_id)
        step_data = progress.get('step_data', {})

        assert step_data.get('name') == 'My Series'
        assert step_data.get('theme') == 'Hope'
        conn.close()


class TestLoadWizardProgress:
    """Test suite for loading wizard progress."""

    def test_should_load_wizard_progress(self):
        """Test that wizard progress is loaded."""
        from series_wizard import save_wizard_progress, load_wizard_progress

        conn = create_test_db()
        user_id = 1
        save_wizard_progress(conn, user_id, 2, {'name': 'Series', 'theme': 'Hope'})

        progress = load_wizard_progress(conn, user_id)

        assert progress is not None
        assert progress['current_step'] == 2
        conn.close()

    def test_should_return_none_for_new_user(self):
        """Test that None is returned for user without progress."""
        from series_wizard import load_wizard_progress

        conn = create_test_db()

        progress = load_wizard_progress(conn, 999)

        assert progress is None
        conn.close()

    def test_should_include_step_data_in_loaded_progress(self):
        """Test that step data is included in loaded progress."""
        from series_wizard import save_wizard_progress, load_wizard_progress

        conn = create_test_db()
        user_id = 1
        data = {'name': 'Easter Series', 'description': 'Journey to Easter'}
        save_wizard_progress(conn, user_id, 1, data)

        progress = load_wizard_progress(conn, user_id)

        assert 'step_data' in progress
        assert progress['step_data']['name'] == 'Easter Series'
        conn.close()


class TestCompleteWizard:
    """Test suite for completing the wizard."""

    def test_should_complete_wizard_and_create_series(self):
        """Test that completing wizard creates the series."""
        from series_wizard import save_wizard_progress, complete_wizard

        conn = create_test_db()
        user_id = 1

        # Save all required data
        full_data = {
            'name': 'Lent 2024',
            'description': 'A 6-week journey through Lent',
            'theme': 'Repentance and Renewal',
            'start_date': '2024-02-14',
            'end_date': '2024-03-31',
            'sermon_count': 6
        }
        save_wizard_progress(conn, user_id, 5, full_data)

        series_id = complete_wizard(conn, user_id)

        assert series_id is not None
        assert isinstance(series_id, int)
        assert series_id > 0
        conn.close()

    def test_should_require_all_steps_for_completion(self):
        """Test that all steps must be completed."""
        from series_wizard import save_wizard_progress, complete_wizard

        conn = create_test_db()
        user_id = 1

        # Only complete step 1
        save_wizard_progress(conn, user_id, 1, {'name': 'Incomplete'})

        result = complete_wizard(conn, user_id)

        assert result is None or result is False
        conn.close()

    def test_should_create_sermon_slots_on_completion(self):
        """Test that sermon slots are created when wizard completes."""
        from series_wizard import save_wizard_progress, complete_wizard

        conn = create_test_db()
        user_id = 1

        full_data = {
            'name': 'Advent Series',
            'sermon_count': 4,
            'start_date': '2024-12-01',
            'end_date': '2024-12-24'
        }
        save_wizard_progress(conn, user_id, 5, full_data)

        series_id = complete_wizard(conn, user_id)

        # Check sermon slots were created
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM sermon_slots WHERE series_id = ?',
                       (series_id,))
        count = cursor.fetchone()['count']
        assert count == 4
        conn.close()

    def test_should_cleanup_wizard_progress_on_completion(self):
        """Test that wizard progress is cleaned up after completion."""
        from series_wizard import save_wizard_progress, complete_wizard, load_wizard_progress

        conn = create_test_db()
        user_id = 1

        full_data = {
            'name': 'Completed Series',
            'sermon_count': 3,
            'start_date': '2024-01-01',
            'end_date': '2024-01-21'
        }
        save_wizard_progress(conn, user_id, 5, full_data)

        complete_wizard(conn, user_id)

        # Progress should be cleared
        progress = load_wizard_progress(conn, user_id)
        assert progress is None
        conn.close()


class TestCancelWizard:
    """Test suite for canceling the wizard."""

    def test_should_cancel_wizard_and_cleanup(self):
        """Test that canceling wizard cleans up progress."""
        from series_wizard import save_wizard_progress, cancel_wizard, load_wizard_progress

        conn = create_test_db()
        user_id = 1
        save_wizard_progress(conn, user_id, 2, {'name': 'Cancelled'})

        result = cancel_wizard(conn, user_id)

        assert result is True
        progress = load_wizard_progress(conn, user_id)
        assert progress is None
        conn.close()

    def test_should_return_false_for_nonexistent_wizard(self):
        """Test that canceling nonexistent wizard returns False."""
        from series_wizard import cancel_wizard

        conn = create_test_db()

        result = cancel_wizard(conn, 999)

        assert result is False
        conn.close()


class TestStepNavigation:
    """Test suite for wizard step navigation."""

    def test_should_allow_back_navigation(self):
        """Test that navigating back is allowed."""
        from series_wizard import save_wizard_progress, load_wizard_progress

        conn = create_test_db()
        user_id = 1

        # Save step 3
        save_wizard_progress(conn, user_id, 3, {'name': 'Test', 'sermon_count': 5})
        # Go back to step 2
        save_wizard_progress(conn, user_id, 2, {'name': 'Test', 'theme': 'Updated'})

        progress = load_wizard_progress(conn, user_id)
        assert progress['current_step'] == 2
        conn.close()

    def test_should_handle_invalid_step_number(self):
        """Test that invalid step number is rejected."""
        from series_wizard import validate_series_step

        data = {'name': 'Test'}

        errors = validate_series_step(99, data)

        assert len(errors) > 0 or errors is None  # Should indicate invalid step


class TestPassageSuggestions:
    """Test suite for passage suggestions in Step 4."""

    def test_should_generate_passage_suggestions(self):
        """Test that passage suggestions are generated."""
        from series_wizard import generate_passage_suggestions

        context = {
            'theme': 'Hope',
            'sermon_count': 4
        }

        suggestions = generate_passage_suggestions(context)

        assert suggestions is not None
        assert len(suggestions) >= 4
        for suggestion in suggestions:
            assert 'scripture' in suggestion or 'passage' in suggestion

    def test_should_generate_suggestions_based_on_theme(self):
        """Test that suggestions relate to theme."""
        from series_wizard import generate_passage_suggestions

        context = {
            'theme': 'Love',
            'sermon_count': 3
        }

        suggestions = generate_passage_suggestions(context)

        # Should have at least sermon_count suggestions
        assert len(suggestions) >= 3

    def test_should_handle_empty_theme(self):
        """Test that suggestions work without theme."""
        from series_wizard import generate_passage_suggestions

        context = {
            'theme': '',
            'sermon_count': 5
        }

        suggestions = generate_passage_suggestions(context)

        assert suggestions is not None
        assert len(suggestions) >= 5


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_should_handle_unicode_in_wizard_data(self):
        """Test that unicode in data is preserved."""
        from series_wizard import save_wizard_progress, load_wizard_progress

        conn = create_test_db()
        user_id = 1
        data = {
            'name': 'Χριστός Series',
            'theme': 'Greek: ἀγάπη (love)',
            'description': 'Exploring Greek concepts'
        }

        save_wizard_progress(conn, user_id, 1, data)
        progress = load_wizard_progress(conn, user_id)

        assert 'Χριστός' in progress['step_data']['name']
        conn.close()

    def test_should_handle_concurrent_wizard_sessions(self):
        """Test that multiple users can have wizard progress."""
        from series_wizard import save_wizard_progress, load_wizard_progress

        conn = create_test_db()

        save_wizard_progress(conn, 1, 1, {'name': 'User 1 Series'})
        save_wizard_progress(conn, 2, 2, {'name': 'User 2 Series'})

        progress1 = load_wizard_progress(conn, 1)
        progress2 = load_wizard_progress(conn, 2)

        assert progress1['step_data']['name'] == 'User 1 Series'
        assert progress2['step_data']['name'] == 'User 2 Series'
        assert progress1['current_step'] == 1
        assert progress2['current_step'] == 2
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
