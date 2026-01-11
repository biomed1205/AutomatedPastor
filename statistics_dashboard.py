"""Statistics dashboard functionality module.

Provides dashboard showing sermon statistics and analytics
including counts, frequencies, averages, and trend data.
"""

import json
from datetime import datetime


def get_sermon_counts_by_period(conn, period='month', start_date=None):
    """Get sermon counts grouped by period.

    Args:
        conn: Database connection.
        period: Period to group by ('month', 'year', 'week').
        start_date: Optional start date filter.

    Returns:
        dict: Dictionary with period as key and count as value.
    """
    cursor = conn.cursor()

    # Determine period format
    if period == 'year':
        period_format = '%Y'
    elif period == 'week':
        period_format = '%Y-W%W'
    else:  # month
        period_format = '%Y-%m'

    query = '''SELECT strftime(?, preached_date) as period, COUNT(*) as count
               FROM sermons
               WHERE status = 'preached' AND preached_date IS NOT NULL'''
    params = [period_format]

    if start_date:
        query += ' AND preached_date >= ?'
        params.append(start_date)

    query += ' GROUP BY period ORDER BY period'

    cursor.execute(query, params)
    rows = cursor.fetchall()

    result = {}
    for row in rows:
        period_key = row['period'] if hasattr(row, 'keys') else row[0]
        count = row['count'] if hasattr(row, 'keys') else row[1]
        if period_key:
            result[period_key] = count

    return result


def get_scripture_frequency(conn, limit=10):
    """Get most frequently used scripture books.

    Args:
        conn: Database connection.
        limit: Maximum number of results.

    Returns:
        list: List of dicts with book and count, ordered by frequency.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT scripture_book as book, COUNT(*) as count
           FROM sermons
           WHERE scripture_book IS NOT NULL
           GROUP BY scripture_book
           ORDER BY count DESC, book
           LIMIT ?''',
        (limit,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'book': row['book'] if hasattr(row, 'keys') else row[0],
            'count': row['count'] if hasattr(row, 'keys') else row[1]
        })

    return result


def get_theme_frequency(conn, limit=10):
    """Get most frequently used themes.

    Args:
        conn: Database connection.
        limit: Maximum number of results.

    Returns:
        list: List of dicts with theme and count, ordered by frequency.
    """
    cursor = conn.cursor()

    # Get themes from sermons table and tags table
    cursor.execute(
        '''SELECT theme, COUNT(*) as count
           FROM (
               SELECT theme FROM sermons WHERE theme IS NOT NULL
               UNION ALL
               SELECT tag as theme FROM sermon_tags
           )
           GROUP BY theme
           ORDER BY count DESC, theme
           LIMIT ?''',
        (limit,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        theme = row['theme'] if hasattr(row, 'keys') else row[0]
        count = row['count'] if hasattr(row, 'keys') else row[1]
        if theme:
            result.append({
                'theme': theme,
                'count': count
            })

    return result


def get_series_statistics(conn):
    """Get statistics for all sermon series.

    Args:
        conn: Database connection.

    Returns:
        list: List of dicts with series statistics.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT ss.id, ss.name, ss.planned_count,
                  COUNT(s.id) as completed
           FROM sermon_series ss
           LEFT JOIN sermons s ON ss.id = s.series_id
           GROUP BY ss.id, ss.name, ss.planned_count
           HAVING completed > 0
           ORDER BY ss.name'''
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        series_id = row['id'] if hasattr(row, 'keys') else row[0]
        name = row['name'] if hasattr(row, 'keys') else row[1]
        planned = row['planned_count'] if hasattr(row, 'keys') else row[2]
        completed = row['completed'] if hasattr(row, 'keys') else row[3]

        planned = planned or 0
        completion_rate = (completed / planned * 100) if planned > 0 else 0

        result.append({
            'id': series_id,
            'name': name,
            'planned': planned,
            'completed': completed,
            'completion_rate': round(completion_rate, 2)
        })

    return result


def get_word_count_stats(conn):
    """Get word count statistics.

    Args:
        conn: Database connection.

    Returns:
        dict: Dictionary with average, min, max, total word counts.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT AVG(word_count) as average,
                  MIN(word_count) as min,
                  MAX(word_count) as max,
                  SUM(word_count) as total,
                  COUNT(*) as count
           FROM sermons'''
    )
    row = cursor.fetchone()

    if row is None or (row['count'] if hasattr(row, 'keys') else row[4]) == 0:
        return {
            'average': 0,
            'min': 0,
            'max': 0,
            'total': 0
        }

    return {
        'average': (row['average'] if hasattr(row, 'keys') else row[0]) or 0,
        'min': (row['min'] if hasattr(row, 'keys') else row[1]) or 0,
        'max': (row['max'] if hasattr(row, 'keys') else row[2]) or 0,
        'total': (row['total'] if hasattr(row, 'keys') else row[3]) or 0
    }


def get_preaching_frequency(conn):
    """Get preaching frequency statistics.

    Args:
        conn: Database connection.

    Returns:
        dict: Dictionary with frequency statistics.
    """
    cursor = conn.cursor()

    # Get total preached
    cursor.execute(
        '''SELECT COUNT(*) as count FROM sermons WHERE status = 'preached' '''
    )
    row = cursor.fetchone()
    total_preached = row['count'] if hasattr(row, 'keys') else row[0]

    if total_preached == 0:
        return {
            'total_preached': 0,
            'sermons_per_month': 0,
            'sermons_per_week': 0
        }

    # Get date range
    cursor.execute(
        '''SELECT MIN(preached_date) as earliest, MAX(preached_date) as latest
           FROM sermons WHERE status = 'preached' AND preached_date IS NOT NULL'''
    )
    row = cursor.fetchone()
    earliest = row['earliest'] if hasattr(row, 'keys') else row[0]
    latest = row['latest'] if hasattr(row, 'keys') else row[1]

    if not earliest or not latest:
        return {
            'total_preached': total_preached,
            'sermons_per_month': total_preached,
            'sermons_per_week': total_preached / 4
        }

    # Calculate time span
    try:
        earliest_dt = datetime.strptime(earliest, '%Y-%m-%d')
        latest_dt = datetime.strptime(latest, '%Y-%m-%d')
        days = (latest_dt - earliest_dt).days + 1
        weeks = max(1, days / 7)
        months = max(1, days / 30)

        return {
            'total_preached': total_preached,
            'sermons_per_month': round(total_preached / months, 2),
            'sermons_per_week': round(total_preached / weeks, 2)
        }
    except ValueError:
        return {
            'total_preached': total_preached,
            'sermons_per_month': total_preached,
            'sermons_per_week': total_preached / 4
        }


def get_dashboard_summary(conn):
    """Get dashboard summary statistics.

    Args:
        conn: Database connection.

    Returns:
        dict: Dictionary with summary statistics.
    """
    cursor = conn.cursor()

    # Total sermons
    cursor.execute('SELECT COUNT(*) as count FROM sermons')
    row = cursor.fetchone()
    total_sermons = row['count'] if hasattr(row, 'keys') else row[0]

    # Total preached
    cursor.execute(
        '''SELECT COUNT(*) as count FROM sermons WHERE status = 'preached' '''
    )
    row = cursor.fetchone()
    total_preached = row['count'] if hasattr(row, 'keys') else row[0]

    # Last preached date
    cursor.execute(
        '''SELECT MAX(preached_date) as last_date FROM sermons
           WHERE status = 'preached' AND preached_date IS NOT NULL'''
    )
    row = cursor.fetchone()
    last_preached_date = row['last_date'] if hasattr(row, 'keys') else row[0]

    # Total series
    cursor.execute('SELECT COUNT(*) as count FROM sermon_series')
    row = cursor.fetchone()
    total_series = row['count'] if hasattr(row, 'keys') else row[0]

    # Average word count
    cursor.execute('SELECT AVG(word_count) as average FROM sermons')
    row = cursor.fetchone()
    average_word_count = (row['average'] if hasattr(row, 'keys') else row[0]) or 0

    return {
        'total_sermons': total_sermons,
        'total_preached': total_preached,
        'last_preached_date': last_preached_date,
        'total_series': total_series,
        'average_word_count': round(average_word_count, 2) if average_word_count else 0
    }


def export_statistics(conn, format='json'):
    """Export all statistics.

    Args:
        conn: Database connection.
        format: Export format ('json' or 'csv').

    Returns:
        str: Exported statistics as string, or None for invalid format.
    """
    if format not in ('json', 'csv'):
        return None

    # Gather all statistics
    summary = get_dashboard_summary(conn)
    counts = get_sermon_counts_by_period(conn)
    books = get_scripture_frequency(conn)
    themes = get_theme_frequency(conn)
    series = get_series_statistics(conn)
    word_stats = get_word_count_stats(conn)
    frequency = get_preaching_frequency(conn)

    if format == 'json':
        data = {
            'summary': summary,
            'sermon_counts_by_month': counts,
            'scripture_frequency': books,
            'theme_frequency': themes,
            'series_statistics': series,
            'word_count_stats': word_stats,
            'preaching_frequency': frequency,
            'exported_at': datetime.now().isoformat()
        }
        return json.dumps(data, indent=2)

    # CSV format
    lines = []
    lines.append('Statistic,Value')
    lines.append(f'Total Sermons,{summary["total_sermons"]}')
    lines.append(f'Total Preached,{summary["total_preached"]}')
    lines.append(f'Total Series,{summary["total_series"]}')
    lines.append(f'Average Word Count,{summary["average_word_count"]}')
    lines.append(f'Min Word Count,{word_stats["min"]}')
    lines.append(f'Max Word Count,{word_stats["max"]}')
    lines.append(f'Total Word Count,{word_stats["total"]}')
    lines.append(f'Sermons Per Month,{frequency["sermons_per_month"]}')
    lines.append(f'Sermons Per Week,{frequency["sermons_per_week"]}')

    lines.append('')
    lines.append('Scripture Book,Count')
    for book in books:
        lines.append(f'{book["book"]},{book["count"]}')

    lines.append('')
    lines.append('Theme,Count')
    for theme in themes:
        lines.append(f'{theme["theme"]},{theme["count"]}')

    return '\n'.join(lines)


def generate_chart_data(conn, chart_type):
    """Generate data for specific chart type.

    Args:
        conn: Database connection.
        chart_type: Type of chart ('monthly', 'scripture', 'theme', 'word_count').

    Returns:
        dict: Chart data with labels and values.
    """
    if chart_type == 'monthly':
        counts = get_sermon_counts_by_period(conn, period='month')
        return {
            'labels': list(counts.keys()),
            'values': list(counts.values()),
            'chart_type': 'bar'
        }

    elif chart_type == 'scripture':
        books = get_scripture_frequency(conn)
        return {
            'labels': [b['book'] for b in books],
            'values': [b['count'] for b in books],
            'chart_type': 'pie'
        }

    elif chart_type == 'theme':
        themes = get_theme_frequency(conn)
        return {
            'labels': [t['theme'] for t in themes],
            'values': [t['count'] for t in themes],
            'chart_type': 'pie'
        }

    elif chart_type == 'word_count':
        stats = get_word_count_stats(conn)
        return {
            'labels': ['Average', 'Min', 'Max'],
            'values': [stats['average'], stats['min'], stats['max']],
            'chart_type': 'bar'
        }

    return None
