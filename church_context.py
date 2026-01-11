"""Church context awareness functionality module.

Provides storage and utilization of church-specific context
(congregation demographics, theology preferences, etc.)
to tailor sermon generation.
"""

import json
from datetime import datetime


def create_church_profile(conn, name=None, denomination=None, location=None,
                         size=None, founded_year=None, website=None):
    """Create a new church profile.

    Args:
        conn: Database connection.
        name: Church name (required).
        denomination: Denomination affiliation.
        location: Church location.
        size: Congregation size category.
        founded_year: Year church was founded.
        website: Church website URL.

    Returns:
        dict: Result with success status and church_id.
    """
    if not name:
        return {'success': False, 'error': 'Name is required'}

    cursor = conn.cursor()

    # Check for duplicate name
    cursor.execute('SELECT id FROM church_profile WHERE name = ?', (name,))
    if cursor.fetchone():
        return {'success': False, 'warning': 'Church name already exists'}

    cursor.execute(
        '''INSERT INTO church_profile (name, denomination, location, size, founded_year, website)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (name, denomination, location, size, founded_year, website)
    )
    conn.commit()

    return {'success': True, 'church_id': cursor.lastrowid}


def update_church_profile(conn, church_id, name=None, denomination=None,
                         location=None, size=None, founded_year=None, website=None):
    """Update an existing church profile.

    Args:
        conn: Database connection.
        church_id: ID of the church to update.
        name: New church name.
        denomination: New denomination.
        location: New location.
        size: New size category.
        founded_year: New founded year.
        website: New website URL.

    Returns:
        dict: Result with success status.
    """
    cursor = conn.cursor()

    # Check church exists
    cursor.execute('SELECT id FROM church_profile WHERE id = ?', (church_id,))
    if not cursor.fetchone():
        return {'success': False, 'error': 'Church not found'}

    # Build update query
    updates = []
    params = []

    if name is not None:
        updates.append('name = ?')
        params.append(name)
    if denomination is not None:
        updates.append('denomination = ?')
        params.append(denomination)
    if location is not None:
        updates.append('location = ?')
        params.append(location)
    if size is not None:
        updates.append('size = ?')
        params.append(size)
    if founded_year is not None:
        updates.append('founded_year = ?')
        params.append(founded_year)
    if website is not None:
        updates.append('website = ?')
        params.append(website)

    updates.append('updated_at = ?')
    params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    params.append(church_id)

    query = f'UPDATE church_profile SET {", ".join(updates)} WHERE id = ?'  # nosec B608
    cursor.execute(query, params)
    conn.commit()

    return {'success': True}


def get_church_profile(conn, church_id):
    """Get complete church profile with all sections.

    Args:
        conn: Database connection.
        church_id: ID of the church.

    Returns:
        dict: Complete profile or None if not found.
    """
    cursor = conn.cursor()

    # Get base profile
    cursor.execute('SELECT * FROM church_profile WHERE id = ?', (church_id,))
    row = cursor.fetchone()

    if row is None:
        return None

    profile = {
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'name': row['name'] if hasattr(row, 'keys') else row[1],
        'denomination': row['denomination'] if hasattr(row, 'keys') else row[2],
        'location': row['location'] if hasattr(row, 'keys') else row[3],
        'size': row['size'] if hasattr(row, 'keys') else row[4],
        'founded_year': row['founded_year'] if hasattr(row, 'keys') else row[5],
        'website': row['website'] if hasattr(row, 'keys') else row[6]
    }

    # Get demographics
    profile['demographics'] = get_congregation_demographics(conn, church_id)

    # Get preferences
    profile['preferences'] = get_pastor_preferences(conn, church_id)

    # Get theology
    cursor.execute('SELECT * FROM theological_context WHERE church_id = ?', (church_id,))
    theology_row = cursor.fetchone()
    if theology_row:
        profile['theology'] = {
            'tradition': theology_row['tradition'] if hasattr(theology_row, 'keys') else theology_row[2],
            'emphasis': theology_row['emphasis'] if hasattr(theology_row, 'keys') else theology_row[3],
            'scripture_approach': theology_row['scripture_approach'] if hasattr(theology_row, 'keys') else theology_row[4],
            'social_stance': theology_row['social_stance'] if hasattr(theology_row, 'keys') else theology_row[5],
            'topics_to_avoid': theology_row['topics_to_avoid'] if hasattr(theology_row, 'keys') else theology_row[6]
        }
    else:
        profile['theology'] = None

    return profile


def set_congregation_demographics(conn, church_id, data):
    """Set congregation demographics.

    Args:
        conn: Database connection.
        church_id: ID of the church.
        data: Dict with demographic fields.

    Returns:
        dict: Result with success status.
    """
    cursor = conn.cursor()

    # Check if demographics exist
    cursor.execute('SELECT id FROM congregation_demographics WHERE church_id = ?', (church_id,))
    existing = cursor.fetchone()

    if existing:
        # Update existing
        updates = []
        params = []

        for field in ['age_distribution', 'education_level', 'political_leaning',
                      'economic_background', 'cultural_diversity']:
            if field in data:
                updates.append(f'{field} = ?')
                params.append(data[field])

        if updates:
            updates.append('updated_at = ?')
            params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            params.append(church_id)

            query = f'UPDATE congregation_demographics SET {", ".join(updates)} WHERE church_id = ?'  # nosec B608
            cursor.execute(query, params)
    else:
        # Insert new
        cursor.execute(
            '''INSERT INTO congregation_demographics
               (church_id, age_distribution, education_level, political_leaning,
                economic_background, cultural_diversity)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (church_id,
             data.get('age_distribution'),
             data.get('education_level'),
             data.get('political_leaning'),
             data.get('economic_background'),
             data.get('cultural_diversity'))
        )

    conn.commit()
    return {'success': True}


def get_congregation_demographics(conn, church_id):
    """Get congregation demographics.

    Args:
        conn: Database connection.
        church_id: ID of the church.

    Returns:
        dict: Demographics or None if not set.
    """
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM congregation_demographics WHERE church_id = ?', (church_id,))
    row = cursor.fetchone()

    if row is None:
        return None

    return {
        'age_distribution': row['age_distribution'] if hasattr(row, 'keys') else row[2],
        'education_level': row['education_level'] if hasattr(row, 'keys') else row[3],
        'political_leaning': row['political_leaning'] if hasattr(row, 'keys') else row[4],
        'economic_background': row['economic_background'] if hasattr(row, 'keys') else row[5],
        'cultural_diversity': row['cultural_diversity'] if hasattr(row, 'keys') else row[6]
    }


def set_pastor_preferences(conn, church_id, data):
    """Set pastor preferences.

    Args:
        conn: Database connection.
        church_id: ID of the church.
        data: Dict with preference fields.

    Returns:
        dict: Result with success status.
    """
    # Validate min/max
    min_len = data.get('sermon_length_min')
    max_len = data.get('sermon_length_max')
    if min_len is not None and max_len is not None and min_len > max_len:
        return {'success': False, 'warning': 'Min length cannot exceed max length'}

    cursor = conn.cursor()

    # Check if preferences exist
    cursor.execute('SELECT id FROM pastor_preferences WHERE church_id = ?', (church_id,))
    existing = cursor.fetchone()

    if existing:
        # Update existing
        updates = []
        params = []

        for field in ['sermon_length_min', 'sermon_length_max', 'illustration_preference',
                      'application_style', 'use_personal_stories', 'humor_level']:
            if field in data:
                updates.append(f'{field} = ?')
                value = data[field]
                if field == 'use_personal_stories':
                    value = 1 if value else 0
                params.append(value)

        if updates:
            updates.append('updated_at = ?')
            params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            params.append(church_id)

            query = f'UPDATE pastor_preferences SET {", ".join(updates)} WHERE church_id = ?'  # nosec B608
            cursor.execute(query, params)
    else:
        # Insert new
        use_stories = 1 if data.get('use_personal_stories') else 0
        cursor.execute(
            '''INSERT INTO pastor_preferences
               (church_id, sermon_length_min, sermon_length_max, illustration_preference,
                application_style, use_personal_stories, humor_level)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (church_id,
             data.get('sermon_length_min', 2000),
             data.get('sermon_length_max', 2500),
             data.get('illustration_preference'),
             data.get('application_style'),
             use_stories,
             data.get('humor_level', 'moderate'))
        )

    conn.commit()
    return {'success': True}


def get_pastor_preferences(conn, church_id):
    """Get pastor preferences.

    Args:
        conn: Database connection.
        church_id: ID of the church.

    Returns:
        dict: Preferences or None if not set.
    """
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM pastor_preferences WHERE church_id = ?', (church_id,))
    row = cursor.fetchone()

    if row is None:
        return None

    return {
        'sermon_length_min': row['sermon_length_min'] if hasattr(row, 'keys') else row[2],
        'sermon_length_max': row['sermon_length_max'] if hasattr(row, 'keys') else row[3],
        'illustration_preference': row['illustration_preference'] if hasattr(row, 'keys') else row[4],
        'application_style': row['application_style'] if hasattr(row, 'keys') else row[5],
        'use_personal_stories': bool(row['use_personal_stories'] if hasattr(row, 'keys') else row[6]),
        'humor_level': row['humor_level'] if hasattr(row, 'keys') else row[7]
    }


def set_theological_context(conn, church_id, data):
    """Set theological context.

    Args:
        conn: Database connection.
        church_id: ID of the church.
        data: Dict with theology fields.

    Returns:
        dict: Result with success status.
    """
    cursor = conn.cursor()

    # Check if context exists
    cursor.execute('SELECT id FROM theological_context WHERE church_id = ?', (church_id,))
    existing = cursor.fetchone()

    if existing:
        # Update existing
        updates = []
        params = []

        for field in ['tradition', 'emphasis', 'scripture_approach', 'social_stance', 'topics_to_avoid']:
            if field in data:
                updates.append(f'{field} = ?')
                params.append(data[field])

        if updates:
            updates.append('updated_at = ?')
            params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            params.append(church_id)

            query = f'UPDATE theological_context SET {", ".join(updates)} WHERE church_id = ?'  # nosec B608
            cursor.execute(query, params)
    else:
        # Insert new
        cursor.execute(
            '''INSERT INTO theological_context
               (church_id, tradition, emphasis, scripture_approach, social_stance, topics_to_avoid)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (church_id,
             data.get('tradition'),
             data.get('emphasis'),
             data.get('scripture_approach'),
             data.get('social_stance'),
             data.get('topics_to_avoid'))
        )

    conn.commit()
    return {'success': True}


def apply_context_to_generation(conn, church_id, params):
    """Apply church context to sermon generation params.

    Args:
        conn: Database connection.
        church_id: ID of the church.
        params: Base generation parameters.

    Returns:
        dict: Enhanced parameters with context applied.
    """
    result = dict(params)

    profile = get_church_profile(conn, church_id)
    if profile is None:
        return result

    # Build context summary
    context = {}

    if profile.get('denomination'):
        context['denomination'] = profile['denomination']

    # Apply preferences
    prefs = profile.get('preferences')
    if prefs:
        result['min_words'] = prefs.get('sermon_length_min', 2000)
        result['max_words'] = prefs.get('sermon_length_max', 2500)
        result['word_count'] = {'min': result['min_words'], 'max': result['max_words']}
        result['length'] = {'min': result['min_words'], 'max': result['max_words']}

        if prefs.get('illustration_preference'):
            context['illustration_style'] = prefs['illustration_preference']
        if prefs.get('use_personal_stories') is not None:
            context['use_personal_stories'] = prefs['use_personal_stories']

    # Apply theology
    theology = profile.get('theology')
    if theology:
        if theology.get('tradition'):
            result['tradition'] = theology['tradition']
            context['tradition'] = theology['tradition']
        if theology.get('emphasis'):
            context['emphasis'] = theology['emphasis']
        if theology.get('topics_to_avoid'):
            result['avoid'] = theology['topics_to_avoid']
            result['topics_to_avoid'] = theology['topics_to_avoid']

    # Apply demographics
    demographics = profile.get('demographics')
    if demographics:
        if demographics.get('education_level'):
            context['audience_education'] = demographics['education_level']
        if demographics.get('age_distribution'):
            context['audience_age'] = demographics['age_distribution']

    result['context'] = context

    return result


def export_church_profile(conn, church_id):
    """Export church profile as JSON.

    Args:
        conn: Database connection.
        church_id: ID of the church.

    Returns:
        str: JSON string of profile or None if not found.
    """
    profile = get_church_profile(conn, church_id)

    if profile is None:
        return None

    return json.dumps(profile, indent=2)


def import_church_profile(conn, json_data):
    """Import church profile from JSON.

    Args:
        conn: Database connection.
        json_data: JSON string of profile.

    Returns:
        dict: Result with success status and church_id.
    """
    try:
        data = json.loads(json_data)
    except json.JSONDecodeError:
        return {'success': False, 'error': 'Invalid JSON'}

    if not data.get('name'):
        return {'success': False, 'error': 'Name is required'}

    # Create base profile
    result = create_church_profile(
        conn,
        name=data.get('name'),
        denomination=data.get('denomination'),
        location=data.get('location'),
        size=data.get('size'),
        founded_year=data.get('founded_year'),
        website=data.get('website')
    )

    if not result.get('success'):
        return result

    church_id = result['church_id']

    # Import demographics
    if data.get('demographics'):
        set_congregation_demographics(conn, church_id, data['demographics'])

    # Import preferences
    if data.get('preferences'):
        set_pastor_preferences(conn, church_id, data['preferences'])

    # Import theology
    if data.get('theology'):
        set_theological_context(conn, church_id, data['theology'])

    return {'success': True, 'church_id': church_id}
