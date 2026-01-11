"""Series arc tracking module.

Provides narrative arc tracking across sermon series with visualization and validation.
"""


# Valid arc types with typical intensity values
ARC_TYPES = {
    'introduction': {'order': 1, 'intensity': 20, 'description': 'Setup, problem statement'},
    'rising_action': {'order': 2, 'intensity': 50, 'description': 'Building tension, complications'},
    'climax': {'order': 3, 'intensity': 100, 'description': 'Turning point, main revelation'},
    'falling_action': {'order': 4, 'intensity': 60, 'description': 'Resolution path'},
    'conclusion': {'order': 5, 'intensity': 30, 'description': 'Resolution, application'}
}


def create_arc_point(conn, series_id, sermon_order, description, arc_type):
    """Create a narrative arc point for a series.

    Args:
        conn: Database connection.
        series_id: ID of the series.
        sermon_order: Order of the sermon this arc point relates to.
        description: Description of this arc point.
        arc_type: Type of arc point (introduction, rising_action, climax, falling_action, conclusion).

    Returns:
        int: ID of the created arc point, or None if invalid.
    """
    # Validate arc type
    if arc_type not in ARC_TYPES:
        return None

    cursor = conn.cursor()

    # Check series exists
    cursor.execute('SELECT id FROM series WHERE id = ?', (series_id,))
    if cursor.fetchone() is None:
        return None

    # Insert arc point
    cursor.execute(
        '''INSERT INTO arc_points (series_id, sermon_order, description, arc_type)
           VALUES (?, ?, ?, ?)''',
        (series_id, sermon_order, description, arc_type)
    )
    conn.commit()
    return cursor.lastrowid


def get_arc_points(conn, series_id):
    """Get arc points for a series in order.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        list: List of arc point dictionaries ordered by sermon_order.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, series_id, sermon_order, description, arc_type, notes, created_at
           FROM arc_points
           WHERE series_id = ?
           ORDER BY sermon_order''',
        (series_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'series_id': row['series_id'] if hasattr(row, 'keys') else row[1],
            'sermon_order': row['sermon_order'] if hasattr(row, 'keys') else row[2],
            'description': row['description'] if hasattr(row, 'keys') else row[3],
            'arc_type': row['arc_type'] if hasattr(row, 'keys') else row[4],
            'notes': row['notes'] if hasattr(row, 'keys') else row[5],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[6]
        })

    return result


def update_arc_point(conn, arc_id, **kwargs):
    """Update an arc point.

    Args:
        conn: Database connection.
        arc_id: ID of the arc point.
        **kwargs: Fields to update (description, arc_type, sermon_order, notes).

    Returns:
        bool: True if updated, False if not found or invalid.
    """
    if not kwargs:
        return False

    cursor = conn.cursor()

    # Check arc point exists
    cursor.execute('SELECT id FROM arc_points WHERE id = ?', (arc_id,))
    if cursor.fetchone() is None:
        return False

    # Validate arc_type if being updated
    if 'arc_type' in kwargs and kwargs['arc_type'] not in ARC_TYPES:
        return False

    # Build update query
    allowed_fields = ['description', 'arc_type', 'sermon_order', 'notes']
    fields_to_update = []
    values = []

    for field in allowed_fields:
        if field in kwargs:
            fields_to_update.append(f'{field} = ?')
            values.append(kwargs[field])

    if not fields_to_update:
        return False

    values.append(arc_id)
    query = f'UPDATE arc_points SET {", ".join(fields_to_update)} WHERE id = ?'  # nosec B608 - fields from whitelist
    cursor.execute(query, values)
    conn.commit()
    return True


def delete_arc_point(conn, arc_id):
    """Delete an arc point.

    Args:
        conn: Database connection.
        arc_id: ID of the arc point.

    Returns:
        bool: True if deleted, False if not found.
    """
    cursor = conn.cursor()

    # Check arc point exists
    cursor.execute('SELECT id FROM arc_points WHERE id = ?', (arc_id,))
    if cursor.fetchone() is None:
        return False

    cursor.execute('DELETE FROM arc_points WHERE id = ?', (arc_id,))
    conn.commit()
    return True


def get_arc_visualization(conn, series_id):
    """Get visualization data for charting the arc.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        dict: Visualization data with points and intensity values.
    """
    arc_points = get_arc_points(conn, series_id)

    points = []
    for point in arc_points:
        arc_type = point.get('arc_type', '')
        intensity = ARC_TYPES.get(arc_type, {}).get('intensity', 50)

        points.append({
            'id': point['id'],
            'sermon_order': point['sermon_order'],
            'description': point['description'],
            'arc_type': arc_type,
            'type': arc_type,
            'intensity': intensity,
            'x': point['sermon_order'],
            'y': intensity
        })

    return {
        'series_id': series_id,
        'points': points,
        'arc_points': points,
        'total_points': len(points)
    }


def validate_arc_progression(conn, series_id):
    """Validate the arc progression for a series.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        list: List of issue strings, empty if valid.
    """
    arc_points = get_arc_points(conn, series_id)
    issues = []

    if not arc_points:
        issues.append('No arc points defined')
        return issues

    # Get arc types present
    types_present = [p['arc_type'] for p in arc_points]

    # Check for climax
    if 'climax' not in types_present:
        issues.append('Missing climax point')

    # Check arc order (introduction should come before climax, etc.)
    type_orders = []
    for point in arc_points:
        arc_type = point['arc_type']
        if arc_type in ARC_TYPES:
            type_orders.append({
                'sermon_order': point['sermon_order'],
                'arc_type': arc_type,
                'expected_order': ARC_TYPES[arc_type]['order']
            })

    # Check for introduction before climax
    intro_orders = [p['sermon_order'] for p in arc_points if p['arc_type'] == 'introduction']
    climax_orders = [p['sermon_order'] for p in arc_points if p['arc_type'] == 'climax']

    if intro_orders and climax_orders:
        if min(intro_orders) > min(climax_orders):
            issues.append('Introduction should come before climax')

    # Check for conclusion after climax
    conclusion_orders = [p['sermon_order'] for p in arc_points if p['arc_type'] == 'conclusion']
    if conclusion_orders and climax_orders:
        if max(conclusion_orders) < max(climax_orders):
            issues.append('Conclusion should come after climax')

    return issues


def suggest_arc_improvements(conn, series_id):
    """Suggest improvements to the series arc.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        list: List of suggestion dictionaries.
    """
    arc_points = get_arc_points(conn, series_id)
    suggestions = []

    if not arc_points:
        suggestions.append({
            'type': 'missing',
            'priority': 'high',
            'message': 'Add arc points to structure your series narrative'
        })
        return suggestions

    # Check for missing arc types
    types_present = set(p['arc_type'] for p in arc_points)
    all_types = set(ARC_TYPES.keys())
    missing_types = all_types - types_present

    for missing_type in missing_types:
        priority = 'high' if missing_type == 'climax' else 'medium'
        suggestions.append({
            'type': 'missing_arc_type',
            'arc_type': missing_type,
            'priority': priority,
            'message': f'Consider adding a {missing_type.replace("_", " ")} point'
        })

    # Check climax placement (should be roughly 2/3 through series)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT COUNT(*) as count FROM sermons WHERE series_id = ?',
        (series_id,)
    )
    row = cursor.fetchone()
    sermon_count = row['count'] if hasattr(row, 'keys') else row[0]

    if sermon_count > 0:
        climax_points = [p for p in arc_points if p['arc_type'] == 'climax']
        for climax in climax_points:
            ideal_position = int(sermon_count * 0.6)
            actual_position = climax['sermon_order']
            if abs(actual_position - ideal_position) > 2 and sermon_count >= 4:
                suggestions.append({
                    'type': 'climax_placement',
                    'priority': 'low',
                    'message': f'Climax at sermon {actual_position} - consider placing around sermon {ideal_position}'
                })

    return suggestions


def get_arc_summary(conn, series_id):
    """Get a summary of the series arc.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        dict: Summary with counts, completeness, and missing elements.
    """
    arc_points = get_arc_points(conn, series_id)

    types_present = set(p['arc_type'] for p in arc_points)
    all_types = set(ARC_TYPES.keys())
    missing_types = all_types - types_present

    # Count by type
    type_counts = {}
    for arc_type in ARC_TYPES:
        type_counts[arc_type] = sum(1 for p in arc_points if p['arc_type'] == arc_type)

    is_complete = len(missing_types) == 0 and 'climax' in types_present

    return {
        'series_id': series_id,
        'total': len(arc_points),
        'count': len(arc_points),
        'arc_points': len(arc_points),
        'complete': is_complete,
        'is_complete': is_complete,
        'missing': list(missing_types),
        'types_present': list(types_present),
        'type_counts': type_counts
    }
