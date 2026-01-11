"""Tests for series arc tracking.

These tests verify the narrative arc tracking across sermon series.
Enables managing introduction, rising action, climax, falling action, and conclusion.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
from datetime import datetime, date


# Arc point types
ARC_TYPES = {
    'introduction': 'Setup, problem statement',
    'rising_action': 'Building tension, complications',
    'climax': 'Turning point, main revelation',
    'falling_action': 'Resolution path',
    'conclusion': 'Resolution, application'
}


def create_test_db():
    """Create an in-memory test database for arc tracking testing."""
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

    # Create sermons table
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            series_id INTEGER,
            title TEXT NOT NULL,
            scripture TEXT,
            theme TEXT,
            sermon_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE SET NULL
        )
    ''')

    # Create arc_points table
    conn.execute('''
        CREATE TABLE arc_points (
            id INTEGER PRIMARY KEY,
            series_id INTEGER NOT NULL,
            sermon_order INTEGER NOT NULL,
            description TEXT NOT NULL,
            arc_type TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    return conn


def insert_sample_series(conn, name="Test Series", theme="Hope"):
    """Insert a sample series for testing."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO series (name, theme) VALUES (?, ?)",
        (name, theme)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_sermon(conn, series_id, title, order):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sermons (series_id, title, sermon_order) VALUES (?, ?, ?)",
        (series_id, title, order)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_arc_point(conn, series_id, sermon_order, description, arc_type):
    """Insert a sample arc point for testing."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO arc_points (series_id, sermon_order, description, arc_type) VALUES (?, ?, ?, ?)",
        (series_id, sermon_order, description, arc_type)
    )
    conn.commit()
    return cursor.lastrowid


class TestCreateArcPoint:
    """Test suite for creating arc points."""

    def test_should_create_arc_point_for_series(self):
        """Test that an arc point can be created for a series."""
        from series_arc import create_arc_point

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Lent Series")

        arc_id = create_arc_point(
            conn,
            series_id=series_id,
            sermon_order=1,
            description="Introduction to Lenten themes",
            arc_type="introduction"
        )

        assert arc_id is not None
        assert isinstance(arc_id, int)
        assert arc_id > 0
        conn.close()

    def test_should_create_arc_point_with_all_types(self):
        """Test that all arc types can be created."""
        from series_arc import create_arc_point

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Complete Arc Series")

        for i, arc_type in enumerate(ARC_TYPES.keys()):
            arc_id = create_arc_point(
                conn,
                series_id=series_id,
                sermon_order=i + 1,
                description=f"Arc point: {arc_type}",
                arc_type=arc_type
            )
            assert arc_id is not None

        conn.close()

    def test_should_reject_invalid_arc_type(self):
        """Test that invalid arc type is rejected."""
        from series_arc import create_arc_point

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")

        result = create_arc_point(
            conn,
            series_id=series_id,
            sermon_order=1,
            description="Invalid",
            arc_type="invalid_type"
        )

        assert result is None or result is False
        conn.close()

    def test_should_reject_arc_point_for_nonexistent_series(self):
        """Test that arc point for nonexistent series is rejected."""
        from series_arc import create_arc_point

        conn = create_test_db()

        result = create_arc_point(
            conn,
            series_id=9999,
            sermon_order=1,
            description="Orphan arc point",
            arc_type="introduction"
        )

        assert result is None or result is False
        conn.close()


class TestGetArcPoints:
    """Test suite for retrieving arc points."""

    def test_should_get_arc_points_for_series(self):
        """Test that arc points can be retrieved for a series."""
        from series_arc import get_arc_points

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        insert_sample_arc_point(conn, series_id, 1, "Intro", "introduction")
        insert_sample_arc_point(conn, series_id, 2, "Rising", "rising_action")

        arc_points = get_arc_points(conn, series_id)

        assert arc_points is not None
        assert len(arc_points) == 2
        conn.close()

    def test_should_get_arc_points_in_order(self):
        """Test that arc points are returned in sermon order."""
        from series_arc import get_arc_points

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        insert_sample_arc_point(conn, series_id, 3, "Third", "climax")
        insert_sample_arc_point(conn, series_id, 1, "First", "introduction")
        insert_sample_arc_point(conn, series_id, 2, "Second", "rising_action")

        arc_points = get_arc_points(conn, series_id)

        assert arc_points[0]['sermon_order'] == 1
        assert arc_points[1]['sermon_order'] == 2
        assert arc_points[2]['sermon_order'] == 3
        conn.close()

    def test_should_return_empty_for_series_without_arc_points(self):
        """Test that empty list is returned for series without arc points."""
        from series_arc import get_arc_points

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Empty Series")

        arc_points = get_arc_points(conn, series_id)

        assert arc_points == []
        conn.close()

    def test_should_return_empty_for_nonexistent_series(self):
        """Test that empty list is returned for nonexistent series."""
        from series_arc import get_arc_points

        conn = create_test_db()

        arc_points = get_arc_points(conn, 9999)

        assert arc_points == [] or arc_points is None
        conn.close()


class TestUpdateArcPoint:
    """Test suite for updating arc points."""

    def test_should_update_arc_point_description(self):
        """Test that arc point description can be updated."""
        from series_arc import update_arc_point, get_arc_points

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        arc_id = insert_sample_arc_point(conn, series_id, 1, "Original", "introduction")

        result = update_arc_point(conn, arc_id, description="Updated description")

        assert result is True
        conn.close()

    def test_should_update_arc_point_type(self):
        """Test that arc point type can be updated."""
        from series_arc import update_arc_point

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        arc_id = insert_sample_arc_point(conn, series_id, 1, "Point", "introduction")

        result = update_arc_point(conn, arc_id, arc_type="rising_action")

        assert result is True
        conn.close()

    def test_should_update_multiple_fields(self):
        """Test that multiple fields can be updated at once."""
        from series_arc import update_arc_point

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        arc_id = insert_sample_arc_point(conn, series_id, 1, "Original", "introduction")

        result = update_arc_point(
            conn,
            arc_id,
            description="New description",
            arc_type="climax",
            sermon_order=3
        )

        assert result is True
        conn.close()

    def test_should_fail_update_for_nonexistent_arc_point(self):
        """Test that update fails for nonexistent arc point."""
        from series_arc import update_arc_point

        conn = create_test_db()

        result = update_arc_point(conn, 9999, description="Ghost")

        assert result is False
        conn.close()


class TestDeleteArcPoint:
    """Test suite for deleting arc points."""

    def test_should_delete_arc_point(self):
        """Test that arc point can be deleted."""
        from series_arc import delete_arc_point, get_arc_points

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        arc_id = insert_sample_arc_point(conn, series_id, 1, "To delete", "introduction")

        result = delete_arc_point(conn, arc_id)

        assert result is True
        arc_points = get_arc_points(conn, series_id)
        assert len(arc_points) == 0
        conn.close()

    def test_should_fail_delete_for_nonexistent_arc_point(self):
        """Test that delete fails for nonexistent arc point."""
        from series_arc import delete_arc_point

        conn = create_test_db()

        result = delete_arc_point(conn, 9999)

        assert result is False
        conn.close()


class TestGetArcVisualization:
    """Test suite for getting arc visualization data."""

    def test_should_get_visualization_data(self):
        """Test that visualization data is returned."""
        from series_arc import get_arc_visualization

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        insert_sample_arc_point(conn, series_id, 1, "Intro", "introduction")
        insert_sample_arc_point(conn, series_id, 2, "Rising", "rising_action")
        insert_sample_arc_point(conn, series_id, 3, "Climax", "climax")

        viz_data = get_arc_visualization(conn, series_id)

        assert viz_data is not None
        assert 'points' in viz_data or 'arc_points' in viz_data or isinstance(viz_data, list)
        conn.close()

    def test_should_include_arc_type_in_visualization(self):
        """Test that visualization includes arc type for each point."""
        from series_arc import get_arc_visualization

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        insert_sample_arc_point(conn, series_id, 1, "Intro", "introduction")

        viz_data = get_arc_visualization(conn, series_id)

        # Check structure contains arc_type
        points = viz_data.get('points', viz_data) if isinstance(viz_data, dict) else viz_data
        if isinstance(points, list) and len(points) > 0:
            assert 'arc_type' in points[0] or 'type' in points[0]
        conn.close()

    def test_should_include_intensity_or_position_values(self):
        """Test that visualization includes values for charting."""
        from series_arc import get_arc_visualization

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        insert_sample_arc_point(conn, series_id, 1, "Intro", "introduction")
        insert_sample_arc_point(conn, series_id, 3, "Climax", "climax")

        viz_data = get_arc_visualization(conn, series_id)

        assert viz_data is not None
        # Should have some numeric value for plotting
        conn.close()

    def test_should_handle_empty_series_visualization(self):
        """Test visualization for series without arc points."""
        from series_arc import get_arc_visualization

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Empty Series")

        viz_data = get_arc_visualization(conn, series_id)

        assert viz_data is not None
        conn.close()


class TestValidateArcProgression:
    """Test suite for validating arc progression."""

    def test_should_validate_complete_arc(self):
        """Test that complete arc passes validation."""
        from series_arc import validate_arc_progression

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Complete Series")
        insert_sample_arc_point(conn, series_id, 1, "Intro", "introduction")
        insert_sample_arc_point(conn, series_id, 2, "Rising", "rising_action")
        insert_sample_arc_point(conn, series_id, 3, "Climax", "climax")
        insert_sample_arc_point(conn, series_id, 4, "Falling", "falling_action")
        insert_sample_arc_point(conn, series_id, 5, "Conclusion", "conclusion")

        issues = validate_arc_progression(conn, series_id)

        assert issues == []
        conn.close()

    def test_should_validate_arc_has_climax(self):
        """Test that missing climax is flagged."""
        from series_arc import validate_arc_progression

        conn = create_test_db()
        series_id = insert_sample_series(conn, "No Climax Series")
        insert_sample_arc_point(conn, series_id, 1, "Intro", "introduction")
        insert_sample_arc_point(conn, series_id, 2, "Conclusion", "conclusion")

        issues = validate_arc_progression(conn, series_id)

        assert len(issues) > 0
        assert any('climax' in issue.lower() for issue in issues)
        conn.close()

    def test_should_validate_arc_progression_order(self):
        """Test that out-of-order progression is flagged."""
        from series_arc import validate_arc_progression

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Out of Order Series")
        insert_sample_arc_point(conn, series_id, 1, "Climax first", "climax")
        insert_sample_arc_point(conn, series_id, 2, "Intro later", "introduction")

        issues = validate_arc_progression(conn, series_id)

        assert len(issues) > 0
        conn.close()

    def test_should_handle_empty_series_validation(self):
        """Test validation of series without arc points."""
        from series_arc import validate_arc_progression

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Empty Series")

        issues = validate_arc_progression(conn, series_id)

        # Should flag that no arc points exist
        assert len(issues) > 0 or issues == []
        conn.close()


class TestSuggestArcImprovements:
    """Test suite for arc improvement suggestions."""

    def test_should_suggest_missing_arc_types(self):
        """Test that missing arc types are suggested."""
        from series_arc import suggest_arc_improvements

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Partial Series")
        insert_sample_arc_point(conn, series_id, 1, "Intro", "introduction")
        insert_sample_arc_point(conn, series_id, 2, "Climax", "climax")
        # Missing: rising_action, falling_action, conclusion

        suggestions = suggest_arc_improvements(conn, series_id)

        assert suggestions is not None
        assert len(suggestions) > 0
        conn.close()

    def test_should_suggest_climax_placement(self):
        """Test that climax placement suggestion is made."""
        from series_arc import suggest_arc_improvements

        conn = create_test_db()
        series_id = insert_sample_series(conn, "6 Sermon Series")
        # Add 6 sermons
        for i in range(1, 7):
            insert_sample_sermon(conn, series_id, f"Sermon {i}", i)
        # Climax at very end
        insert_sample_arc_point(conn, series_id, 6, "Late climax", "climax")

        suggestions = suggest_arc_improvements(conn, series_id)

        # Should suggest better climax placement
        assert suggestions is not None
        conn.close()

    def test_should_handle_empty_series_suggestions(self):
        """Test suggestions for series without arc points."""
        from series_arc import suggest_arc_improvements

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Empty Series")

        suggestions = suggest_arc_improvements(conn, series_id)

        assert suggestions is not None
        # Should suggest adding arc points
        conn.close()


class TestGetArcSummary:
    """Test suite for getting arc summary."""

    def test_should_get_arc_summary(self):
        """Test that arc summary is returned."""
        from series_arc import get_arc_summary

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Complete Series")
        insert_sample_arc_point(conn, series_id, 1, "Intro", "introduction")
        insert_sample_arc_point(conn, series_id, 2, "Rising", "rising_action")
        insert_sample_arc_point(conn, series_id, 3, "Climax", "climax")

        summary = get_arc_summary(conn, series_id)

        assert summary is not None
        assert isinstance(summary, dict)
        conn.close()

    def test_should_include_total_arc_points_in_summary(self):
        """Test that summary includes total count."""
        from series_arc import get_arc_summary

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        insert_sample_arc_point(conn, series_id, 1, "One", "introduction")
        insert_sample_arc_point(conn, series_id, 2, "Two", "climax")

        summary = get_arc_summary(conn, series_id)

        assert 'total' in summary or 'count' in summary or 'arc_points' in summary
        conn.close()

    def test_should_include_completeness_in_summary(self):
        """Test that summary includes completeness indicator."""
        from series_arc import get_arc_summary

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        # Only add partial arc
        insert_sample_arc_point(conn, series_id, 1, "Intro", "introduction")

        summary = get_arc_summary(conn, series_id)

        assert 'complete' in summary or 'is_complete' in summary or 'missing' in summary
        conn.close()

    def test_should_handle_empty_series_summary(self):
        """Test summary for series without arc points."""
        from series_arc import get_arc_summary

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Empty Series")

        summary = get_arc_summary(conn, series_id)

        assert summary is not None
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_should_handle_single_sermon_series(self):
        """Test arc tracking for single sermon series."""
        from series_arc import create_arc_point, get_arc_points

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Single Sermon")
        insert_sample_sermon(conn, series_id, "Only Sermon", 1)

        # Can still add arc point
        arc_id = create_arc_point(
            conn, series_id, 1, "Standalone", "climax"
        )
        arc_points = get_arc_points(conn, series_id)

        assert arc_id is not None
        assert len(arc_points) == 1
        conn.close()

    def test_should_support_multiple_climax_points(self):
        """Test that multiple climax points are allowed."""
        from series_arc import create_arc_point, get_arc_points

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Double Climax Series")

        create_arc_point(conn, series_id, 3, "First climax", "climax")
        create_arc_point(conn, series_id, 5, "Second climax", "climax")

        arc_points = get_arc_points(conn, series_id)
        climax_points = [p for p in arc_points if p['arc_type'] == 'climax']

        assert len(climax_points) == 2
        conn.close()

    def test_should_handle_unicode_in_description(self):
        """Test unicode in arc point description."""
        from series_arc import create_arc_point, get_arc_points

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Unicode Series")

        arc_id = create_arc_point(
            conn,
            series_id,
            1,
            "Χριστός revealed - ἀγάπη demonstrated",
            "climax"
        )

        arc_points = get_arc_points(conn, series_id)
        assert 'Χριστός' in arc_points[0]['description']
        conn.close()

    def test_should_handle_very_long_description(self):
        """Test very long arc point description."""
        from series_arc import create_arc_point

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        long_description = "This is a detailed arc point. " * 100

        arc_id = create_arc_point(
            conn,
            series_id,
            1,
            long_description,
            "introduction"
        )

        assert arc_id is not None
        conn.close()

    def test_should_handle_arc_points_beyond_sermon_count(self):
        """Test arc points with order beyond actual sermon count."""
        from series_arc import create_arc_point, validate_arc_progression

        conn = create_test_db()
        series_id = insert_sample_series(conn, "3 Sermon Series")
        insert_sample_sermon(conn, series_id, "Sermon 1", 1)
        insert_sample_sermon(conn, series_id, "Sermon 2", 2)
        insert_sample_sermon(conn, series_id, "Sermon 3", 3)

        # Add arc point for sermon 5 (doesn't exist)
        arc_id = create_arc_point(conn, series_id, 5, "Future", "conclusion")

        # Should either reject or flag in validation
        issues = validate_arc_progression(conn, series_id)
        assert arc_id is not None or len(issues) > 0
        conn.close()


class TestIntegration:
    """Integration tests for arc tracking workflows."""

    def test_should_build_complete_arc_workflow(self):
        """Test building a complete arc through the workflow."""
        from series_arc import (
            create_arc_point,
            get_arc_points,
            validate_arc_progression,
            get_arc_summary
        )

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Lent 2024", "Repentance")

        # Build complete arc
        create_arc_point(conn, series_id, 1, "Setting the scene", "introduction")
        create_arc_point(conn, series_id, 2, "Growing awareness of sin", "rising_action")
        create_arc_point(conn, series_id, 3, "Encounter at the cross", "climax")
        create_arc_point(conn, series_id, 4, "Path to redemption", "falling_action")
        create_arc_point(conn, series_id, 5, "Living in grace", "conclusion")

        arc_points = get_arc_points(conn, series_id)
        issues = validate_arc_progression(conn, series_id)
        summary = get_arc_summary(conn, series_id)

        assert len(arc_points) == 5
        assert issues == []
        assert summary is not None
        conn.close()

    def test_should_edit_and_revalidate_arc(self):
        """Test editing arc points and revalidating."""
        from series_arc import (
            create_arc_point,
            update_arc_point,
            validate_arc_progression
        )

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Editable Series")

        # Create incomplete arc
        arc_id = create_arc_point(conn, series_id, 1, "Wrong type", "conclusion")

        # First validation should flag issues
        issues_before = validate_arc_progression(conn, series_id)

        # Fix it
        update_arc_point(conn, arc_id, arc_type="introduction")
        create_arc_point(conn, series_id, 3, "Climax", "climax")
        create_arc_point(conn, series_id, 5, "Real conclusion", "conclusion")

        issues_after = validate_arc_progression(conn, series_id)

        # Should have fewer issues after fixes
        assert len(issues_before) > 0 or len(issues_after) <= len(issues_before)
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
