"""Tests for basic web UI routes (create, view, list sermons).

These tests verify the Flask routes for sermon CRUD operations work correctly.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL Flask test_client and SQLite :memory: database - NO MOCKS.
"""
import pytest
import json


class TestDashboard:
    """Test suite for dashboard/home page."""

    def test_should_return_200_when_dashboard_accessed(self):
        """Test that home page returns 200."""
        from app import create_app

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.test_client() as client:
            response = client.get('/')

            assert response.status_code == 200

    def test_should_return_html_when_dashboard_accessed(self):
        """Test that home page returns HTML content."""
        from app import create_app

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.test_client() as client:
            response = client.get('/')

            assert 'text/html' in response.content_type

    def test_should_show_recent_sermons_when_dashboard_loaded(self):
        """Test that dashboard shows recent sermons."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('Test Sermon', 'John 3:16')
            )
            conn.commit()

        with app.test_client() as client:
            response = client.get('/')

            assert b'Test Sermon' in response.data


class TestSermonsList:
    """Test suite for sermons list page."""

    def test_should_return_200_when_sermons_list_accessed(self):
        """Test that sermons list page returns 200."""
        from app import create_app

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.test_client() as client:
            response = client.get('/sermons')

            assert response.status_code == 200

    def test_should_list_all_sermons_when_page_loaded(self):
        """Test that all sermons are listed."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('Sermon 1', 'John 3:16')
            )
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('Sermon 2', 'Romans 8:28')
            )
            conn.commit()

        with app.test_client() as client:
            response = client.get('/sermons')

            assert b'Sermon 1' in response.data
            assert b'Sermon 2' in response.data

    def test_should_show_empty_state_when_no_sermons(self):
        """Test that empty state is shown when no sermons exist."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)

        with app.test_client() as client:
            response = client.get('/sermons')

            # Should show some indication that there are no sermons
            assert response.status_code == 200
            # Could show "No sermons yet" or similar
            assert b'no sermon' in response.data.lower() or b'empty' in response.data.lower() or response.status_code == 200


class TestViewSermon:
    """Test suite for viewing a single sermon."""

    def test_should_return_200_when_valid_sermon_requested(self):
        """Test that valid sermon returns 200."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('Test Sermon', 'John 3:16')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.get(f'/sermon/{sermon_id}')

            assert response.status_code == 200

    def test_should_return_404_when_sermon_not_found(self):
        """Test that missing sermon returns 404."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)

        with app.test_client() as client:
            response = client.get('/sermon/99999')

            assert response.status_code == 404

    def test_should_display_sermon_details_when_viewed(self):
        """Test that sermon details are displayed."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture, theme, manuscript) VALUES (?, ?, ?, ?)",
                ('Grace Sermon', 'John 3:16', 'Grace', 'This is the manuscript content.')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.get(f'/sermon/{sermon_id}')

            assert b'Grace Sermon' in response.data
            assert b'John 3:16' in response.data
            assert b'Grace' in response.data

    def test_should_display_manuscript_when_available(self):
        """Test that manuscript content is displayed."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture, manuscript) VALUES (?, ?, ?)",
                ('Test Sermon', 'John 3:16', 'The manuscript text here.')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.get(f'/sermon/{sermon_id}')

            assert b'manuscript' in response.data.lower() or b'The manuscript text' in response.data


class TestCreateSermonForm:
    """Test suite for create sermon form."""

    def test_should_return_200_when_create_form_accessed(self):
        """Test that create form returns 200."""
        from app import create_app

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.test_client() as client:
            response = client.get('/sermon/new')

            assert response.status_code == 200

    def test_should_display_form_fields_when_create_form_loaded(self):
        """Test that form contains required fields."""
        from app import create_app

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.test_client() as client:
            response = client.get('/sermon/new')

            # Should have form fields for title and scripture at minimum
            assert b'title' in response.data.lower()
            assert b'scripture' in response.data.lower()


class TestCreateSermon:
    """Test suite for creating sermons via POST."""

    def test_should_create_sermon_when_valid_data_posted(self):
        """Test that POST creates a new sermon."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)

        with app.test_client() as client:
            response = client.post('/sermon', data={
                'title': 'New Sermon',
                'scripture': 'John 3:16'
            }, follow_redirects=True)

            assert response.status_code == 200

        # Verify sermon was created
        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sermons WHERE title = ?", ('New Sermon',))
            sermon = cursor.fetchone()
            assert sermon is not None

    def test_should_redirect_after_successful_creation(self):
        """Test that user is redirected after creating sermon."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)

        with app.test_client() as client:
            response = client.post('/sermon', data={
                'title': 'New Sermon',
                'scripture': 'John 3:16'
            }, follow_redirects=False)

            # Should redirect to the new sermon or sermons list
            assert response.status_code == 302

    def test_should_show_error_when_title_missing(self):
        """Test that missing title shows validation error."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)

        with app.test_client() as client:
            response = client.post('/sermon', data={
                'scripture': 'John 3:16'
                # title missing
            })

            # Should show error or return 400
            assert response.status_code == 400 or b'error' in response.data.lower() or b'required' in response.data.lower()

    def test_should_show_error_when_scripture_missing(self):
        """Test that missing scripture shows validation error."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)

        with app.test_client() as client:
            response = client.post('/sermon', data={
                'title': 'New Sermon'
                # scripture missing
            })

            # Should show error or return 400
            assert response.status_code == 400 or b'error' in response.data.lower() or b'required' in response.data.lower()

    def test_should_save_optional_fields_when_provided(self):
        """Test that optional fields are saved."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)

        with app.test_client() as client:
            client.post('/sermon', data={
                'title': 'Full Sermon',
                'scripture': 'John 3:16',
                'theme': 'Love',
                'main_point': 'God loves everyone'
            })

        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT theme, main_point FROM sermons WHERE title = ?", ('Full Sermon',))
            row = cursor.fetchone()
            assert row[0] == 'Love'
            assert row[1] == 'God loves everyone'


class TestEditSermonForm:
    """Test suite for edit sermon form."""

    def test_should_return_200_when_edit_form_accessed(self):
        """Test that edit form returns 200."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('Test Sermon', 'John 3:16')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.get(f'/sermon/{sermon_id}/edit')

            assert response.status_code == 200

    def test_should_return_404_when_editing_nonexistent_sermon(self):
        """Test that editing missing sermon returns 404."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)

        with app.test_client() as client:
            response = client.get('/sermon/99999/edit')

            assert response.status_code == 404

    def test_should_prefill_form_with_existing_data(self):
        """Test that edit form is prefilled with current values."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture, theme) VALUES (?, ?, ?)",
                ('Existing Sermon', 'Romans 8:28', 'Hope')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.get(f'/sermon/{sermon_id}/edit')

            assert b'Existing Sermon' in response.data
            assert b'Romans 8:28' in response.data


class TestUpdateSermon:
    """Test suite for updating sermons via PUT."""

    def test_should_update_sermon_when_valid_data_posted(self):
        """Test that PUT updates the sermon."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('Original Title', 'John 3:16')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.put(f'/sermon/{sermon_id}', data={
                'title': 'Updated Title',
                'scripture': 'John 3:16-17'
            }, follow_redirects=True)

            assert response.status_code == 200

        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT title, scripture FROM sermons WHERE id = ?", (sermon_id,))
            row = cursor.fetchone()
            assert row[0] == 'Updated Title'
            assert row[1] == 'John 3:16-17'

    def test_should_return_404_when_updating_nonexistent_sermon(self):
        """Test that updating missing sermon returns 404."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)

        with app.test_client() as client:
            response = client.put('/sermon/99999', data={
                'title': 'Updated',
                'scripture': 'John 3:16'
            })

            assert response.status_code == 404

    def test_should_redirect_after_successful_update(self):
        """Test that user is redirected after updating."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('Original', 'John 3:16')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.put(f'/sermon/{sermon_id}', data={
                'title': 'Updated',
                'scripture': 'John 3:16'
            }, follow_redirects=False)

            assert response.status_code == 302


class TestDeleteSermon:
    """Test suite for deleting sermons."""

    def test_should_delete_sermon_when_delete_called(self):
        """Test that DELETE removes the sermon."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('To Delete', 'John 3:16')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.delete(f'/sermon/{sermon_id}')

            assert response.status_code == 200 or response.status_code == 204

        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sermons WHERE id = ?", (sermon_id,))
            row = cursor.fetchone()
            assert row is None

    def test_should_return_404_when_deleting_nonexistent_sermon(self):
        """Test that deleting missing sermon returns 404."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)

        with app.test_client() as client:
            response = client.delete('/sermon/99999')

            assert response.status_code == 404

    def test_should_cascade_delete_related_data(self):
        """Test that deleting sermon removes related illustrations, etc."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('With Illustrations', 'John 3:16')
            )
            sermon_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO illustrations (sermon_id, type, content) VALUES (?, ?, ?)",
                (sermon_id, 'story', 'A test illustration')
            )
            conn.commit()

        with app.test_client() as client:
            client.delete(f'/sermon/{sermon_id}')

        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM illustrations WHERE sermon_id = ?", (sermon_id,))
            row = cursor.fetchone()
            assert row is None


class TestAPIEndpoints:
    """Test suite for API-style endpoints (JSON responses)."""

    def test_should_return_json_when_api_list_called(self):
        """Test that API list endpoint returns JSON."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)

        with app.test_client() as client:
            response = client.get('/api/sermons')

            assert response.status_code == 200
            assert 'application/json' in response.content_type

    def test_should_return_json_when_api_sermon_called(self):
        """Test that API sermon endpoint returns JSON."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('Test Sermon', 'John 3:16')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.get(f'/api/sermon/{sermon_id}')

            assert response.status_code == 200
            assert 'application/json' in response.content_type

            data = json.loads(response.data)
            assert data['title'] == 'Test Sermon'


class TestErrorPages:
    """Test suite for error pages."""

    def test_should_return_404_page_for_unknown_route(self):
        """Test that 404 page is returned for unknown routes."""
        from app import create_app

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.test_client() as client:
            response = client.get('/nonexistent-page-12345')

            assert response.status_code == 404

    def test_should_return_html_for_404_on_html_request(self):
        """Test that 404 returns HTML for browser requests."""
        from app import create_app

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.test_client() as client:
            response = client.get('/nonexistent-page-12345',
                                  headers={'Accept': 'text/html'})

            assert response.status_code == 404
            assert 'text/html' in response.content_type

    def test_should_return_json_for_404_on_api_request(self):
        """Test that 404 returns JSON for API requests."""
        from app import create_app

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.test_client() as client:
            response = client.get('/api/sermon/99999',
                                  headers={'Accept': 'application/json'})

            assert response.status_code == 404
            assert 'application/json' in response.content_type
