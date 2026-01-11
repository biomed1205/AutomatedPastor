"""Insight import module for panel chat to sermon drafts.

Provides functionality to extract and import valuable insights from
panel chat discussions into sermon drafts.
"""


# Insight types for categorization
INSIGHT_TYPES = [
    'theological',
    'pastoral',
    'structural',
    'illustration',
    'scripture',
    'language',
    'general'
]

# Section relevance mapping for insight suggestions
SECTION_RELEVANCE = {
    'introduction': ['illustration', 'engagement', 'structural'],
    'point1': ['theological', 'scripture', 'pastoral'],
    'point2': ['theological', 'scripture', 'pastoral'],
    'point3': ['theological', 'scripture', 'pastoral'],
    'body': ['theological', 'scripture', 'pastoral', 'illustration'],
    'application': ['pastoral', 'illustration', 'engagement'],
    'conclusion': ['illustration', 'engagement', 'language', 'pastoral']
}


def extract_insights_from_chat(conn, session_id):
    """Extract insights from a chat session.

    Args:
        conn: Database connection.
        session_id: ID of the chat session.

    Returns:
        list: List of insight dictionaries, or empty list if none found.
    """
    cursor = conn.cursor()

    # Check if session exists
    cursor.execute('SELECT id FROM chat_sessions WHERE id = ?', (session_id,))
    if cursor.fetchone() is None:
        return []

    # Get all reviewer messages (not user messages)
    cursor.execute(
        """SELECT id, sender, sender_type, content, created_at
           FROM chat_messages
           WHERE session_id = ? AND sender_type = 'reviewer'
           ORDER BY created_at""",
        (session_id,)
    )
    rows = cursor.fetchall()

    if not rows:
        return []

    insights = []
    for row in rows:
        message_id = row['id'] if hasattr(row, 'keys') else row[0]
        sender = row['sender'] if hasattr(row, 'keys') else row[1]
        content = row['content'] if hasattr(row, 'keys') else row[3]

        # Determine insight type from sender
        insight_type = sender if sender in INSIGHT_TYPES else 'general'

        # Calculate relevance score based on content length and actionability
        relevance_score = _calculate_relevance(content)

        # Store insight in database
        cursor.execute(
            """INSERT INTO insights
               (session_id, message_id, content, insight_type, source_reviewer, relevance_score)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, message_id, content, insight_type, sender, relevance_score)
        )
        insight_id = cursor.lastrowid

        insights.append({
            'id': insight_id,
            'content': content,
            'insight_type': insight_type,
            'type': insight_type,
            'source_reviewer': sender,
            'sender': sender,
            'relevance_score': relevance_score
        })

    conn.commit()
    return insights


def _calculate_relevance(content):
    """Calculate relevance score for an insight.

    Args:
        content: Insight content text.

    Returns:
        float: Relevance score between 0 and 1.
    """
    score = 0.5

    # Longer content tends to be more detailed/actionable
    if len(content) > 100:
        score += 0.1
    if len(content) > 200:
        score += 0.1

    # Actionable keywords increase relevance
    actionable_keywords = [
        'consider', 'suggest', 'recommend', 'try', 'should',
        'could', 'needs', 'add', 'include', 'emphasize'
    ]
    content_lower = content.lower()
    for keyword in actionable_keywords:
        if keyword in content_lower:
            score += 0.05
            break

    return min(score, 1.0)


def import_insight_to_sermon(conn, insight, sermon_id, section=None):
    """Import an insight to a sermon.

    Args:
        conn: Database connection.
        insight: Insight dictionary with 'id' key.
        sermon_id: ID of the target sermon.
        section: Optional section reference.

    Returns:
        bool: True if import successful, False if duplicate.
    """
    insight_id = insight.get('id')
    if insight_id is None:
        return False

    cursor = conn.cursor()

    # Check for duplicate
    cursor.execute(
        """SELECT id FROM imported_insights
           WHERE insight_id = ? AND sermon_id = ?""",
        (insight_id, sermon_id)
    )
    if cursor.fetchone() is not None:
        return False

    # Insert import record
    cursor.execute(
        """INSERT INTO imported_insights
           (insight_id, sermon_id, section, used)
           VALUES (?, ?, ?, 0)""",
        (insight_id, sermon_id, section)
    )
    conn.commit()
    return True


def get_imported_insights(conn, sermon_id):
    """Get all imported insights for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of imported insight dictionaries.
    """
    cursor = conn.cursor()
    cursor.execute(
        """SELECT ii.id, ii.insight_id, ii.section, ii.used, ii.imported_at,
                  i.content, i.insight_type, i.source_reviewer, i.relevance_score
           FROM imported_insights ii
           JOIN insights i ON ii.insight_id = i.id
           WHERE ii.sermon_id = ?
           ORDER BY ii.imported_at""",
        (sermon_id,)
    )
    rows = cursor.fetchall()

    insights = []
    for row in rows:
        insights.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'insight_id': row['insight_id'] if hasattr(row, 'keys') else row[1],
            'section': row['section'] if hasattr(row, 'keys') else row[2],
            'used': bool(row['used'] if hasattr(row, 'keys') else row[3]),
            'imported_at': row['imported_at'] if hasattr(row, 'keys') else row[4],
            'content': row['content'] if hasattr(row, 'keys') else row[5],
            'insight_type': row['insight_type'] if hasattr(row, 'keys') else row[6],
            'source_reviewer': row['source_reviewer'] if hasattr(row, 'keys') else row[7],
            'relevance_score': row['relevance_score'] if hasattr(row, 'keys') else row[8]
        })

    return insights


def mark_insight_as_used(conn, insight_id, sermon_id):
    """Mark an imported insight as used.

    Args:
        conn: Database connection.
        insight_id: ID of the imported insight record.
        sermon_id: ID of the sermon.
    """
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE imported_insights
           SET used = 1
           WHERE id = ? AND sermon_id = ?""",
        (insight_id, sermon_id)
    )
    conn.commit()


def filter_insights_by_type(insights, insight_type):
    """Filter insights by type (case-insensitive).

    Args:
        insights: List of insight dictionaries.
        insight_type: Type to filter by.

    Returns:
        list: Filtered insights matching the type.
    """
    type_lower = insight_type.lower()
    filtered = []

    for insight in insights:
        this_type = insight.get('insight_type', insight.get('type', ''))
        if this_type and this_type.lower() == type_lower:
            filtered.append(insight)

    return filtered


def suggest_insights_for_section(conn, session_id, section):
    """Suggest relevant insights for a sermon section.

    Args:
        conn: Database connection.
        session_id: ID of the chat session.
        section: Sermon section name.

    Returns:
        list: List of suggested insights sorted by relevance.
    """
    # Get all insights from session
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, content, insight_type, source_reviewer, relevance_score
           FROM insights
           WHERE session_id = ?""",
        (session_id,)
    )
    rows = cursor.fetchall()

    if not rows:
        # Try extracting insights first
        insights = extract_insights_from_chat(conn, session_id)
    else:
        insights = []
        for row in rows:
            insights.append({
                'id': row['id'] if hasattr(row, 'keys') else row[0],
                'content': row['content'] if hasattr(row, 'keys') else row[1],
                'insight_type': row['insight_type'] if hasattr(row, 'keys') else row[2],
                'source_reviewer': row['source_reviewer'] if hasattr(row, 'keys') else row[3],
                'relevance_score': row['relevance_score'] if hasattr(row, 'keys') else row[4]
            })

    # Get relevant types for this section
    section_lower = section.lower()
    relevant_types = SECTION_RELEVANCE.get(section_lower, [])

    # Score insights by section relevance
    suggestions = []
    for insight in insights:
        insight_type = insight.get('insight_type', '')
        base_score = insight.get('relevance_score', 0.5)

        # Boost score if type is relevant to section
        if insight_type in relevant_types:
            adjusted_score = base_score + 0.2
        else:
            adjusted_score = base_score

        suggestions.append({
            **insight,
            'relevance_score': min(adjusted_score, 1.0)
        })

    # Sort by relevance score descending
    suggestions.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

    return suggestions


def clear_imported_insights(conn, sermon_id):
    """Clear all imported insights for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        bool: True if insights were cleared, False if none existed.
    """
    cursor = conn.cursor()

    # Check if any exist
    cursor.execute(
        'SELECT COUNT(*) as count FROM imported_insights WHERE sermon_id = ?',
        (sermon_id,)
    )
    row = cursor.fetchone()
    count = row['count'] if hasattr(row, 'keys') else row[0]

    if count == 0:
        return False

    # Delete imports
    cursor.execute(
        'DELETE FROM imported_insights WHERE sermon_id = ?',
        (sermon_id,)
    )
    conn.commit()
    return True
