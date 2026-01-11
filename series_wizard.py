"""Sermon series creation wizard.

Provides a step-by-step workflow for creating sermon series with validation.
"""
import json
from datetime import datetime


# Wizard steps definition
WIZARD_STEPS = {
    1: 'name_description',
    2: 'theme_dates',
    3: 'sermon_slots',
    4: 'passage_suggestions',
    5: 'review_create'
}

# Theme-based passage suggestions
THEME_PASSAGES = {
    'hope': [
        {'scripture': 'Romans 15:13', 'title': 'The God of Hope'},
        {'scripture': 'Jeremiah 29:11', 'title': 'Plans for Hope'},
        {'scripture': 'Psalm 42:5', 'title': 'Hope in God'},
        {'scripture': 'Hebrews 6:19', 'title': 'Anchor of the Soul'},
        {'scripture': 'Romans 8:24-25', 'title': 'Hope Unseen'},
        {'scripture': 'Lamentations 3:21-24', 'title': 'New Every Morning'}
    ],
    'love': [
        {'scripture': '1 Corinthians 13:1-13', 'title': 'The Greatest Gift'},
        {'scripture': '1 John 4:7-12', 'title': 'God is Love'},
        {'scripture': 'John 15:12-17', 'title': 'Love One Another'},
        {'scripture': 'Romans 8:38-39', 'title': 'Inseparable Love'},
        {'scripture': 'Song of Solomon 8:6-7', 'title': 'Love as Strong as Death'},
        {'scripture': 'Matthew 22:37-40', 'title': 'The Greatest Commandment'}
    ],
    'faith': [
        {'scripture': 'Hebrews 11:1-3', 'title': 'Faith Defined'},
        {'scripture': 'Romans 10:17', 'title': 'Faith Comes by Hearing'},
        {'scripture': 'James 2:14-26', 'title': 'Faith and Works'},
        {'scripture': 'Mark 11:22-24', 'title': 'Have Faith in God'},
        {'scripture': 'Matthew 17:20', 'title': 'Mustard Seed Faith'},
        {'scripture': 'Galatians 2:20', 'title': 'Living by Faith'}
    ],
    'default': [
        {'scripture': 'John 3:16', 'title': 'God\'s Love'},
        {'scripture': 'Psalm 23', 'title': 'The Good Shepherd'},
        {'scripture': 'Romans 8:28', 'title': 'All Things Work Together'},
        {'scripture': 'Philippians 4:13', 'title': 'Strength in Christ'},
        {'scripture': 'Matthew 28:18-20', 'title': 'The Great Commission'},
        {'scripture': 'Proverbs 3:5-6', 'title': 'Trust in the Lord'},
        {'scripture': 'Isaiah 40:31', 'title': 'Renewed Strength'},
        {'scripture': 'Psalm 46:10', 'title': 'Be Still and Know'}
    ]
}


def validate_series_step(step, data):
    """Validate data for a wizard step.

    Args:
        step: Step number (1-5).
        data: Dictionary of step data.

    Returns:
        list: List of error messages, empty if valid.
    """
    if step not in WIZARD_STEPS:
        return ['Invalid step number']

    errors = []

    if step == 1:
        errors = _validate_step_one(data)
    elif step == 2:
        errors = _validate_step_two(data)
    elif step == 3:
        errors = _validate_step_three(data)
    elif step == 4:
        errors = _validate_step_four(data)
    elif step == 5:
        errors = _validate_step_five(data)

    return errors


def _validate_step_one(data):
    """Validate step 1: name and description."""
    errors = []
    name = data.get('name', '').strip()

    if not name:
        errors.append('Name is required')
    elif len(name) < 3:
        errors.append('Name must be at least 3 characters')

    return errors


def _validate_step_two(data):
    """Validate step 2: theme and dates."""
    errors = []
    start_date = data.get('start_date', '')
    end_date = data.get('end_date', '')

    # Validate date format
    start_parsed = None
    end_parsed = None

    if start_date:
        try:
            start_parsed = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            errors.append('Invalid start date format (use YYYY-MM-DD)')

    if end_date:
        try:
            end_parsed = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            errors.append('Invalid end date format (use YYYY-MM-DD)')

    # Validate date range
    if start_parsed and end_parsed and start_parsed > end_parsed:
        errors.append('End date must be after start date')

    return errors


def _validate_step_three(data):
    """Validate step 3: sermon slots."""
    errors = []
    sermon_count = data.get('sermon_count', 0)

    # Handle string input
    try:
        sermon_count = int(sermon_count)
    except (ValueError, TypeError):
        errors.append('Sermon count must be a number')
        return errors

    if sermon_count < 1:
        errors.append('Must have at least one sermon')
    elif sermon_count > 52:
        errors.append('Maximum 52 sermons per series')

    return errors


def _validate_step_four(data):
    """Validate step 4: passage suggestions (optional step)."""
    return []


def _validate_step_five(data):
    """Validate step 5: review (all data should already be valid)."""
    return []


def save_wizard_progress(conn, user_id, step, data):
    """Save wizard progress for a user.

    Args:
        conn: Database connection.
        user_id: User identifier.
        step: Current step number.
        data: Step data dictionary.

    Returns:
        bool: True if saved successfully.
    """
    cursor = conn.cursor()

    # Check for existing progress
    cursor.execute(
        '''SELECT id, step_data FROM wizard_progress
           WHERE user_id = ? AND wizard_type = 'series' ''',
        (user_id,)
    )
    row = cursor.fetchone()

    if row:
        # Merge with existing data
        existing_id = row['id'] if hasattr(row, 'keys') else row[0]
        existing_data_str = row['step_data'] if hasattr(row, 'keys') else row[1]

        existing_data = {}
        if existing_data_str:
            existing_data = json.loads(existing_data_str)

        # Merge new data into existing
        existing_data.update(data)

        cursor.execute(
            '''UPDATE wizard_progress
               SET current_step = ?, step_data = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?''',
            (step, json.dumps(existing_data), existing_id)
        )
    else:
        # Insert new progress
        cursor.execute(
            '''INSERT INTO wizard_progress (user_id, wizard_type, current_step, step_data)
               VALUES (?, 'series', ?, ?)''',
            (user_id, step, json.dumps(data))
        )

    conn.commit()
    return True


def load_wizard_progress(conn, user_id):
    """Load wizard progress for a user.

    Args:
        conn: Database connection.
        user_id: User identifier.

    Returns:
        dict: Progress data with current_step and step_data, or None if not found.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, current_step, step_data, started_at, updated_at
           FROM wizard_progress
           WHERE user_id = ? AND wizard_type = 'series' ''',
        (user_id,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    step_data_str = row['step_data'] if hasattr(row, 'keys') else row[2]
    step_data = {}
    if step_data_str:
        step_data = json.loads(step_data_str)

    return {
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'current_step': row['current_step'] if hasattr(row, 'keys') else row[1],
        'step_data': step_data,
        'started_at': row['started_at'] if hasattr(row, 'keys') else row[3],
        'updated_at': row['updated_at'] if hasattr(row, 'keys') else row[4]
    }


def complete_wizard(conn, user_id):
    """Complete the wizard and create the series.

    Args:
        conn: Database connection.
        user_id: User identifier.

    Returns:
        int: Created series ID, or None if incomplete.
    """
    progress = load_wizard_progress(conn, user_id)

    if progress is None:
        return None

    # Check minimum required step
    if progress['current_step'] < 5:
        return None

    step_data = progress.get('step_data', {})

    # Validate required fields
    name = step_data.get('name', '').strip()
    if not name:
        return None

    # Create the series
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO series (name, description, theme, start_date, end_date, status)
           VALUES (?, ?, ?, ?, ?, 'planning')''',
        (
            name,
            step_data.get('description'),
            step_data.get('theme'),
            step_data.get('start_date'),
            step_data.get('end_date')
        )
    )
    series_id = cursor.lastrowid

    # Create sermon slots
    sermon_count = step_data.get('sermon_count', 0)
    try:
        sermon_count = int(sermon_count)
    except (ValueError, TypeError):
        sermon_count = 0

    for slot_num in range(1, sermon_count + 1):
        cursor.execute(
            '''INSERT INTO sermon_slots (series_id, slot_number, status)
               VALUES (?, ?, 'planned')''',
            (series_id, slot_num)
        )

    # Clean up wizard progress
    cursor.execute(
        '''DELETE FROM wizard_progress
           WHERE user_id = ? AND wizard_type = 'series' ''',
        (user_id,)
    )

    conn.commit()
    return series_id


def cancel_wizard(conn, user_id):
    """Cancel the wizard and clean up progress.

    Args:
        conn: Database connection.
        user_id: User identifier.

    Returns:
        bool: True if canceled, False if no progress found.
    """
    cursor = conn.cursor()

    # Check if progress exists
    cursor.execute(
        '''SELECT id FROM wizard_progress
           WHERE user_id = ? AND wizard_type = 'series' ''',
        (user_id,)
    )
    if cursor.fetchone() is None:
        return False

    # Delete progress
    cursor.execute(
        '''DELETE FROM wizard_progress
           WHERE user_id = ? AND wizard_type = 'series' ''',
        (user_id,)
    )
    conn.commit()
    return True


def generate_passage_suggestions(context):
    """Generate passage suggestions based on context.

    Args:
        context: Dictionary with theme and sermon_count.

    Returns:
        list: List of passage suggestion dictionaries.
    """
    theme = context.get('theme', '').lower().strip()
    sermon_count = context.get('sermon_count', 5)

    try:
        sermon_count = int(sermon_count)
    except (ValueError, TypeError):
        sermon_count = 5

    # Get theme-based passages or defaults
    passages = THEME_PASSAGES.get(theme, THEME_PASSAGES['default'])

    # Ensure we have enough suggestions
    suggestions = []
    while len(suggestions) < sermon_count:
        for passage in passages:
            if len(suggestions) >= sermon_count:
                break
            suggestions.append(passage.copy())

    return suggestions
