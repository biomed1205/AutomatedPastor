"""Previous Sermon Detection module.

Provides detection of recently preached topics and scriptures
to help maintain variety in sermon content.

Phase 8: Enhanced Features - Item 5 (FINAL)
"""

from datetime import datetime, timedelta


def check_recent_topic(conn, topic, days=90):
    """Check if a topic was preached recently.

    Args:
        conn: Database connection.
        topic: Topic to check.
        days: Number of days to look back.

    Returns:
        dict: Result with is_recent, days_since, sermon details.
    """
    cursor = conn.cursor()

    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    cursor.execute(
        '''SELECT s.id, s.title, s.primary_scripture, s.date_preached, tu.date_used
           FROM topic_usage tu
           JOIN sermons s ON tu.sermon_id = s.id
           WHERE LOWER(tu.topic) = LOWER(?)
           AND tu.date_used >= ?
           ORDER BY tu.date_used DESC
           LIMIT 1''',
        (topic, cutoff_date)
    )
    row = cursor.fetchone()

    if row is None:
        # Check if topic was ever used
        cursor.execute(
            '''SELECT MAX(date_used) as last_used FROM topic_usage
               WHERE LOWER(topic) = LOWER(?)''',
            (topic,)
        )
        last_row = cursor.fetchone()
        last_used = last_row['last_used'] if hasattr(last_row, 'keys') else last_row[0] if last_row else None

        return {
            'is_recent': False,
            'last_preached': last_used,
            'days_since': None
        }

    date_used = row['date_used'] if hasattr(row, 'keys') else row[4]
    days_since = (datetime.now() - datetime.strptime(date_used, '%Y-%m-%d')).days

    return {
        'is_recent': True,
        'days_since': days_since,
        'sermon_title': row['title'] if hasattr(row, 'keys') else row[1],
        'scripture': row['primary_scripture'] if hasattr(row, 'keys') else row[2],
        'date_preached': row['date_preached'] if hasattr(row, 'keys') else row[3],
        'last_preached': date_used
    }


def check_recent_scripture(conn, scripture, days=90):
    """Check if a scripture passage was used recently.

    Args:
        conn: Database connection.
        scripture: Scripture passage to check.
        days: Number of days to look back.

    Returns:
        dict: Result with is_recent, days_since, sermon details.
    """
    cursor = conn.cursor()

    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    # Search for exact or partial match
    cursor.execute(
        '''SELECT s.id, s.title, s.topic, s.date_preached, su.date_used, su.passage
           FROM scripture_usage su
           JOIN sermons s ON su.sermon_id = s.id
           WHERE (su.passage = ? OR su.passage LIKE ?)
           AND su.date_used >= ?
           ORDER BY su.date_used DESC
           LIMIT 1''',
        (scripture, f'{scripture}%', cutoff_date)
    )
    row = cursor.fetchone()

    if row is None:
        return {
            'is_recent': False,
            'last_preached': None
        }

    date_used = row['date_used'] if hasattr(row, 'keys') else row[4]
    days_since = (datetime.now() - datetime.strptime(date_used, '%Y-%m-%d')).days

    return {
        'is_recent': True,
        'days_since': days_since,
        'sermon_title': row['title'] if hasattr(row, 'keys') else row[1],
        'topic': row['topic'] if hasattr(row, 'keys') else row[2],
        'date_preached': row['date_preached'] if hasattr(row, 'keys') else row[3]
    }


def get_last_preached_date(conn, topic_or_scripture, is_scripture=False):
    """Get the last date a topic or scripture was preached.

    Args:
        conn: Database connection.
        topic_or_scripture: Topic or scripture to check.
        is_scripture: True if checking scripture, False for topic.

    Returns:
        str: Date string or None if never preached.
    """
    cursor = conn.cursor()

    if is_scripture:
        cursor.execute(
            '''SELECT MAX(date_used) as last_date
               FROM scripture_usage
               WHERE passage = ? OR passage LIKE ?''',
            (topic_or_scripture, f'{topic_or_scripture}%')
        )
    else:
        cursor.execute(
            '''SELECT MAX(date_used) as last_date
               FROM topic_usage
               WHERE LOWER(topic) = LOWER(?)''',
            (topic_or_scripture,)
        )

    row = cursor.fetchone()
    if row is None:
        return None

    return row['last_date'] if hasattr(row, 'keys') else row[0]


def get_similar_recent_sermons(conn, sermon_params):
    """Find sermons similar to the proposed sermon.

    Args:
        conn: Database connection.
        sermon_params: Dict with topic, scripture, title.

    Returns:
        list: List of similar sermon dicts with similarity scores.
    """
    cursor = conn.cursor()
    results = []
    seen_ids = set()

    topic = sermon_params.get('topic')
    scripture = sermon_params.get('scripture')

    # Find by topic
    if topic:
        cursor.execute(
            '''SELECT s.id, s.title, s.primary_scripture, s.topic, s.date_preached
               FROM sermons s
               JOIN topic_usage tu ON s.id = tu.sermon_id
               WHERE LOWER(tu.topic) = LOWER(?)
               ORDER BY s.date_preached DESC''',
            (topic,)
        )
        rows = cursor.fetchall()
        for row in rows:
            sermon_id = row['id'] if hasattr(row, 'keys') else row[0]
            if sermon_id not in seen_ids:
                seen_ids.add(sermon_id)
                results.append({
                    'id': sermon_id,
                    'title': row['title'] if hasattr(row, 'keys') else row[1],
                    'primary_scripture': row['primary_scripture'] if hasattr(row, 'keys') else row[2],
                    'topic': row['topic'] if hasattr(row, 'keys') else row[3],
                    'date_preached': row['date_preached'] if hasattr(row, 'keys') else row[4],
                    'similarity_score': 0.8,
                    'match_type': 'topic'
                })

    # Find by scripture
    if scripture:
        cursor.execute(
            '''SELECT s.id, s.title, s.primary_scripture, s.topic, s.date_preached
               FROM sermons s
               JOIN scripture_usage su ON s.id = su.sermon_id
               WHERE su.passage = ?
               ORDER BY s.date_preached DESC''',
            (scripture,)
        )
        rows = cursor.fetchall()
        for row in rows:
            sermon_id = row['id'] if hasattr(row, 'keys') else row[0]
            if sermon_id not in seen_ids:
                seen_ids.add(sermon_id)
                results.append({
                    'id': sermon_id,
                    'title': row['title'] if hasattr(row, 'keys') else row[1],
                    'primary_scripture': row['primary_scripture'] if hasattr(row, 'keys') else row[2],
                    'topic': row['topic'] if hasattr(row, 'keys') else row[3],
                    'date_preached': row['date_preached'] if hasattr(row, 'keys') else row[4],
                    'similarity_score': 0.9,
                    'match_type': 'scripture'
                })

    return results


def set_recency_threshold(conn, days):
    """Set the recency threshold for warnings.

    Args:
        conn: Database connection.
        days: Number of days for threshold.

    Returns:
        bool: True if successful.
    """
    if days <= 0:
        return False

    cursor = conn.cursor()

    cursor.execute(
        '''INSERT INTO recency_settings (threshold_days)
           VALUES (?)''',
        (days,)
    )
    conn.commit()

    return True


def get_recency_threshold(conn):
    """Get the current recency threshold.

    Args:
        conn: Database connection.

    Returns:
        int: Threshold in days, default 90.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT threshold_days FROM recency_settings
           ORDER BY id DESC LIMIT 1'''
    )
    row = cursor.fetchone()

    if row is None:
        return 90

    return row['threshold_days'] if hasattr(row, 'keys') else row[0]


def get_warning_for_sermon(conn, sermon_params):
    """Generate warnings for a proposed sermon.

    Args:
        conn: Database connection.
        sermon_params: Dict with topic, scripture, title, optional series_id.

    Returns:
        list: List of warning dicts.
    """
    warnings = []
    threshold = get_recency_threshold(conn)

    topic = sermon_params.get('topic')
    scripture = sermon_params.get('scripture')
    series_id = sermon_params.get('series_id')

    # Check if part of a series (allows repetition)
    is_series = series_id is not None

    # Check topic
    if topic:
        topic_result = check_recent_topic(conn, topic, days=threshold)
        if topic_result['is_recent']:
            warning = {
                'warning_type': 'recent_topic',
                'warning_message': f"Topic '{topic}' was preached {topic_result['days_since']} days ago",
                'previous_sermon': topic_result.get('sermon_title'),
                'days_since': topic_result['days_since'],
                'is_series': is_series
            }
            if not is_series:
                warnings.append(warning)

    # Check scripture
    if scripture:
        scripture_result = check_recent_scripture(conn, scripture, days=threshold)
        if scripture_result['is_recent']:
            warning = {
                'warning_type': 'recent_scripture',
                'warning_message': f"Scripture '{scripture}' was used {scripture_result['days_since']} days ago",
                'previous_sermon': scripture_result.get('sermon_title'),
                'days_since': scripture_result['days_since'],
                'is_series': is_series
            }
            warnings.append(warning)

    return warnings


def dismiss_warning(conn, sermon_id, warning_id, reason=''):
    """Dismiss a warning with a reason.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        warning_id: ID of the warning to dismiss.
        reason: Reason for dismissal.

    Returns:
        bool: True if successful.
    """
    if not reason or not reason.strip():
        return False

    cursor = conn.cursor()

    # Check warning exists
    cursor.execute('SELECT id FROM sermon_warnings WHERE id = ?', (warning_id,))
    if cursor.fetchone() is None:
        return False

    cursor.execute(
        '''UPDATE sermon_warnings
           SET dismissed = 1, dismissed_reason = ?
           WHERE id = ?''',
        (reason, warning_id)
    )
    conn.commit()

    return True


def generate_diversity_report(conn, months=12):
    """Generate a diversity report for sermon content.

    Args:
        conn: Database connection.
        months: Number of months to analyze.

    Returns:
        dict: Report with statistics and suggestions.
    """
    cursor = conn.cursor()

    cutoff_date = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')

    # Total sermons
    cursor.execute(
        '''SELECT COUNT(*) as count FROM sermons
           WHERE date_preached >= ?''',
        (cutoff_date,)
    )
    row = cursor.fetchone()
    total_sermons = row['count'] if hasattr(row, 'keys') else row[0]

    # Unique topics
    cursor.execute(
        '''SELECT COUNT(DISTINCT topic) as count FROM topic_usage
           WHERE date_used >= ?''',
        (cutoff_date,)
    )
    row = cursor.fetchone()
    unique_topics = row['count'] if hasattr(row, 'keys') else row[0]

    # Unique scriptures
    cursor.execute(
        '''SELECT COUNT(DISTINCT passage) as count FROM scripture_usage
           WHERE date_used >= ?''',
        (cutoff_date,)
    )
    row = cursor.fetchone()
    unique_scriptures = row['count'] if hasattr(row, 'keys') else row[0]

    # Topic frequency
    cursor.execute(
        '''SELECT topic, COUNT(*) as count FROM topic_usage
           WHERE date_used >= ?
           GROUP BY LOWER(topic)
           ORDER BY count DESC''',
        (cutoff_date,)
    )
    rows = cursor.fetchall()
    topic_frequency = {}
    for row in rows:
        topic = row['topic'] if hasattr(row, 'keys') else row[0]
        count = row['count'] if hasattr(row, 'keys') else row[1]
        topic_frequency[topic] = count

    # Scripture books
    cursor.execute(
        '''SELECT DISTINCT passage FROM scripture_usage
           WHERE date_used >= ?''',
        (cutoff_date,)
    )
    rows = cursor.fetchall()
    scripture_books = set()
    for row in rows:
        passage = row['passage'] if hasattr(row, 'keys') else row[0]
        if passage:
            book = passage.split()[0] if passage else ''
            scripture_books.add(book)

    # Identify overused topics (more than 3 uses)
    overused_topics = [topic for topic, count in topic_frequency.items() if count > 3]

    # Suggestions
    suggestions = []
    if len(scripture_books) < 5:
        suggestions.append('Consider exploring more diverse scripture books')
    if any('Genesis' not in book and 'Exodus' not in book for book in scripture_books):
        suggestions.append('Consider incorporating Old Testament passages')

    return {
        'total_sermons': total_sermons,
        'unique_topics': unique_topics,
        'unique_scriptures': unique_scriptures,
        'topic_frequency': topic_frequency,
        'scripture_books': list(scripture_books),
        'overused_topics': overused_topics,
        'suggestions': suggestions
    }


def suggest_fresh_topics(conn, include_liturgical=False):
    """Suggest fresh topics not recently covered.

    Args:
        conn: Database connection.
        include_liturgical: Include liturgical calendar suggestions.

    Returns:
        list: List of topic suggestions.
    """
    cursor = conn.cursor()
    suggestions = []

    # Get recently used topics
    cutoff_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    cursor.execute(
        '''SELECT DISTINCT LOWER(topic) as topic FROM topic_usage
           WHERE date_used >= ?''',
        (cutoff_date,)
    )
    rows = cursor.fetchall()
    recent_topics = set(row['topic'] if hasattr(row, 'keys') else row[0] for row in rows)

    # Standard theological topics
    standard_topics = [
        'grace', 'love', 'faith', 'hope', 'peace', 'joy', 'patience',
        'forgiveness', 'redemption', 'salvation', 'sanctification',
        'stewardship', 'service', 'community', 'discipleship',
        'justice', 'mercy', 'compassion', 'prayer', 'worship'
    ]

    # Find topics not recently used
    for topic in standard_topics:
        if topic.lower() not in recent_topics:
            # Get days since last use
            result = get_last_preached_date(conn, topic)
            days_since = None
            if result:
                days_since = (datetime.now() - datetime.strptime(result, '%Y-%m-%d')).days

            suggestions.append({
                'topic': topic,
                'days_since_use': days_since,
                'priority': days_since if days_since else 999,
                'source': 'standard'
            })

    # Add liturgical suggestions
    if include_liturgical:
        liturgical_topics = ['advent', 'christmas', 'epiphany', 'lent',
                            'easter', 'pentecost', 'ordinary time']
        for topic in liturgical_topics:
            if topic.lower() not in recent_topics:
                suggestions.append({
                    'topic': topic,
                    'source': 'liturgical',
                    'priority': 500
                })

    # Sort by priority (higher = longer since used)
    suggestions.sort(key=lambda x: x.get('priority', 0), reverse=True)

    return suggestions


def get_series_context(conn, series_id):
    """Get context for a sermon series.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        dict: Series context with sermon count and suggestions.
    """
    cursor = conn.cursor()

    # Get series info
    cursor.execute(
        '''SELECT name, description FROM sermon_series WHERE id = ?''',
        (series_id,)
    )
    series_row = cursor.fetchone()

    if series_row is None:
        return None

    # Get sermon count
    cursor.execute(
        '''SELECT COUNT(*) as count, MAX(order_in_series) as max_order
           FROM series_sermons WHERE series_id = ?''',
        (series_id,)
    )
    count_row = cursor.fetchone()
    sermon_count = count_row['count'] if hasattr(count_row, 'keys') else count_row[0]
    max_order = count_row['max_order'] if hasattr(count_row, 'keys') else count_row[1]

    # Get sermons in series
    cursor.execute(
        '''SELECT s.title, s.primary_scripture, s.topic, ss.order_in_series
           FROM series_sermons ss
           JOIN sermons s ON ss.sermon_id = s.id
           WHERE ss.series_id = ?
           ORDER BY ss.order_in_series''',
        (series_id,)
    )
    sermons = []
    for row in cursor.fetchall():
        sermons.append({
            'title': row['title'] if hasattr(row, 'keys') else row[0],
            'scripture': row['primary_scripture'] if hasattr(row, 'keys') else row[1],
            'topic': row['topic'] if hasattr(row, 'keys') else row[2],
            'order': row['order_in_series'] if hasattr(row, 'keys') else row[3]
        })

    return {
        'name': series_row['name'] if hasattr(series_row, 'keys') else series_row[0],
        'description': series_row['description'] if hasattr(series_row, 'keys') else series_row[1],
        'sermon_count': sermon_count,
        'sermons': sermons,
        'next_suggested': max_order + 1 if max_order else 1
    }
