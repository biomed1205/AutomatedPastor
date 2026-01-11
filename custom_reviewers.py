"""Custom reviewer module for user-defined reviewer personas.

Allows users to create their own reviewer personas that work
alongside the default panel reviewers.
"""
import os
import re
import json
from datetime import datetime

from panel_feedback import DEFAULT_REVIEWER_TYPES


# Exceptions
class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class ReviewerNotFoundError(Exception):
    """Raised when a reviewer is not found."""
    pass


class CannotDeleteDefaultError(Exception):
    """Raised when trying to delete a default reviewer."""
    pass


class DuplicateIdentifierError(Exception):
    """Raised when identifier already exists."""
    pass


class InvalidIdentifierError(Exception):
    """Raised when identifier format is invalid."""
    pass


# Constants
MAX_NAME_LENGTH = 200
MAX_FOCUS_LENGTH = 500
IDENTIFIER_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


class CustomReviewer:
    """Custom reviewer persona."""

    def __init__(self, id=None, name=None, identifier=None, focus_area=None,
                 prompt_template=None, created_by=None, created_at=None, updated_at=None,
                 style_notes=None, is_default=None):
        self.id = id
        self.name = name
        self.identifier = identifier
        self.focus_area = focus_area
        self.prompt_template = prompt_template
        self.created_by = created_by
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.style_notes = style_notes
        self.is_default = is_default or False

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'identifier': self.identifier,
            'focus_area': self.focus_area,
            'prompt_template': self.prompt_template,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


def _generate_identifier(name):
    """Generate identifier from name."""
    identifier = name.lower().replace(' ', '_')
    identifier = re.sub(r'[^a-z0-9_]', '', identifier)
    if not identifier or not identifier[0].isalpha():
        identifier = 'custom_' + identifier
    return identifier


def _validate_identifier(identifier):
    """Validate identifier format."""
    if not identifier:
        return True  # Will be auto-generated
    if not IDENTIFIER_PATTERN.match(identifier):
        raise InvalidIdentifierError(f"Invalid identifier format: {identifier}")
    return True


def create_custom_reviewer(conn, name, focus_area, identifier=None,
                          prompt_template=None, created_by=None):
    """Create a custom reviewer.

    Args:
        conn: Database connection.
        name: Reviewer display name.
        focus_area: Focus area for reviews.
        identifier: Optional unique identifier.
        prompt_template: Optional custom prompt template.
        created_by: Optional creator ID.

    Returns:
        CustomReviewer: Created reviewer instance.

    Raises:
        ValidationError: If name or focus_area is empty or too long.
        InvalidIdentifierError: If identifier format is invalid.
        DuplicateIdentifierError: If identifier already exists.
    """
    if not name or not name.strip():
        raise ValidationError("Name is required")

    if not focus_area or not focus_area.strip():
        raise ValidationError("Focus area is required")

    if len(name) > MAX_NAME_LENGTH:
        raise ValidationError(f"Name too long (max {MAX_NAME_LENGTH})")

    if len(focus_area) > MAX_FOCUS_LENGTH:
        raise ValidationError(f"Focus area too long (max {MAX_FOCUS_LENGTH})")

    if identifier:
        _validate_identifier(identifier)
    else:
        identifier = _generate_identifier(name)

    # Check for duplicate identifier
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM custom_reviewers WHERE identifier = ?", (identifier,))
    if cursor.fetchone():
        raise DuplicateIdentifierError(f"Identifier already exists: {identifier}")

    # Insert into database
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO custom_reviewers (name, identifier, focus_area, prompt_template, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, identifier, focus_area, prompt_template, created_by, now, now))
    conn.commit()

    reviewer_id = cursor.lastrowid
    return CustomReviewer(
        id=reviewer_id,
        name=name,
        identifier=identifier,
        focus_area=focus_area,
        prompt_template=prompt_template,
        created_by=created_by,
        created_at=now,
        updated_at=now
    )


def get_custom_reviewer(conn, reviewer_id):
    """Get a custom reviewer by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM custom_reviewers WHERE id = ?", (reviewer_id,))
    row = cursor.fetchone()
    if not row:
        raise ReviewerNotFoundError(f"Reviewer not found: {reviewer_id}")
    return _row_to_reviewer(row)


def get_custom_reviewer_by_identifier(conn, identifier):
    """Get a custom reviewer by identifier."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM custom_reviewers WHERE identifier = ?", (identifier,))
    row = cursor.fetchone()
    if not row:
        raise ReviewerNotFoundError(f"Reviewer not found: {identifier}")
    return _row_to_reviewer(row)


def _row_to_reviewer(row):
    """Convert database row to CustomReviewer."""
    if hasattr(row, 'keys'):
        return CustomReviewer(**dict(row))
    # Column order: id, name, identifier, focus_area, style_notes, prompt_template, is_default, created_by, created_at, updated_at
    return CustomReviewer(
        id=row[0], name=row[1], identifier=row[2], focus_area=row[3],
        style_notes=row[4], prompt_template=row[5], is_default=row[6],
        created_by=row[7], created_at=row[8], updated_at=row[9]
    )


def save_reviewer_to_file(reviewer, directory):
    """Save reviewer to JSON file."""
    filepath = os.path.join(directory, f'{reviewer.identifier}.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(reviewer.to_dict(), f, indent=2)
    return filepath


def load_reviewer_from_file(filepath):
    """Load reviewer from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return CustomReviewer(**data)


def list_custom_reviewers(conn):
    """List all custom reviewers."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM custom_reviewers ORDER BY name")
    return [_row_to_reviewer(row) for row in cursor.fetchall()]


def get_feedback(bridge, reviewer, sermon_text):
    """Get feedback from a custom reviewer."""
    prompt = reviewer.prompt_template or f"Review this sermon focusing on: {reviewer.focus_area}"
    full_prompt = f"{prompt}\n\n## Sermon\n{sermon_text}"

    result = bridge.run(full_prompt)
    output = result.output if hasattr(result, 'output') else str(result)

    return {
        'reviewer': reviewer.identifier,
        'reviewer_name': reviewer.name,
        'focus_area': reviewer.focus_area,
        'comment': output,
        'type': 'custom'
    }


def get_and_save_feedback(bridge, conn, reviewer, sermon_id, sermon_text):
    """Get and save feedback to database."""
    feedback = get_feedback(bridge, reviewer, sermon_text)

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO panel_feedback (sermon_id, reviewer, comment, created_at)
        VALUES (?, ?, ?, ?)
    """, (sermon_id, reviewer.identifier, feedback.get('comment', ''), datetime.now().isoformat()))
    conn.commit()

    return feedback


def update_custom_reviewer(conn, reviewer_id, **kwargs):
    """Update a custom reviewer."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM custom_reviewers WHERE id = ?", (reviewer_id,))
    row = cursor.fetchone()
    if not row:
        raise ReviewerNotFoundError(f"Reviewer not found: {reviewer_id}")

    updates = []
    values = []
    for field in ['name', 'focus_area', 'prompt_template']:
        if field in kwargs:
            updates.append(f"{field} = ?")
            values.append(kwargs[field])

    if updates:
        now = datetime.now().isoformat()
        updates.append("updated_at = ?")
        values.append(now)
        values.append(reviewer_id)

        cursor.execute(
            f"UPDATE custom_reviewers SET {', '.join(updates)} WHERE id = ?",
            values
        )
        conn.commit()

    return get_custom_reviewer(conn, reviewer_id)


def delete_custom_reviewer(conn, reviewer_id=None, identifier=None):
    """Delete a custom reviewer."""
    # Check if trying to delete default reviewer
    if identifier and identifier in DEFAULT_REVIEWER_TYPES:
        raise CannotDeleteDefaultError(f"Cannot delete default reviewer: {identifier}")

    cursor = conn.cursor()
    if reviewer_id:
        cursor.execute("SELECT id FROM custom_reviewers WHERE id = ?", (reviewer_id,))
    elif identifier:
        cursor.execute("SELECT id FROM custom_reviewers WHERE identifier = ?", (identifier,))
    else:
        raise ValueError("Must provide reviewer_id or identifier")

    row = cursor.fetchone()
    if not row:
        raise ReviewerNotFoundError(f"Reviewer not found")

    cursor.execute("DELETE FROM custom_reviewers WHERE id = ?", (row[0] if hasattr(row, '__getitem__') else row['id'],))
    conn.commit()
    return True
