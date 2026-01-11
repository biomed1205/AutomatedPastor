"""Lectionary calendar integration module.

Provides integration with lectionary calendars (primarily RCL)
to suggest scripture passages based on the liturgical calendar.
"""


def get_lectionary_readings(conn, date):
    """Get lectionary readings for a specific date.

    Args:
        conn: Database connection.
        date: Date string in YYYY-MM-DD format.

    Returns:
        dict: Reading data including passages and season, or None if no readings.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT date, year, season, name, first_reading, psalm,
                  second_reading, gospel, alternate_first, alternate_psalm
           FROM lectionary_readings
           WHERE date = ?''',
        (date,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    return {
        'date': row['date'] if hasattr(row, 'keys') else row[0],
        'year': row['year'] if hasattr(row, 'keys') else row[1],
        'season': row['season'] if hasattr(row, 'keys') else row[2],
        'name': row['name'] if hasattr(row, 'keys') else row[3],
        'first_reading': row['first_reading'] if hasattr(row, 'keys') else row[4],
        'psalm': row['psalm'] if hasattr(row, 'keys') else row[5],
        'second_reading': row['second_reading'] if hasattr(row, 'keys') else row[6],
        'gospel': row['gospel'] if hasattr(row, 'keys') else row[7],
        'alternate_first': row['alternate_first'] if hasattr(row, 'keys') else row[8],
        'alternate_psalm': row['alternate_psalm'] if hasattr(row, 'keys') else row[9]
    }


def get_upcoming_readings(conn, count=4, from_date=None):
    """Get upcoming lectionary readings.

    Args:
        conn: Database connection.
        count: Maximum number of readings to return.
        from_date: Start date string (optional).

    Returns:
        list: List of reading dicts ordered by date.
    """
    cursor = conn.cursor()

    if from_date:
        cursor.execute(
            '''SELECT date, year, season, name, first_reading, psalm,
                      second_reading, gospel
               FROM lectionary_readings
               WHERE date > ?
               ORDER BY date
               LIMIT ?''',
            (from_date, count)
        )
    else:
        cursor.execute(
            '''SELECT date, year, season, name, first_reading, psalm,
                      second_reading, gospel
               FROM lectionary_readings
               ORDER BY date
               LIMIT ?''',
            (count,)
        )

    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'date': row['date'] if hasattr(row, 'keys') else row[0],
            'year': row['year'] if hasattr(row, 'keys') else row[1],
            'season': row['season'] if hasattr(row, 'keys') else row[2],
            'name': row['name'] if hasattr(row, 'keys') else row[3],
            'first_reading': row['first_reading'] if hasattr(row, 'keys') else row[4],
            'psalm': row['psalm'] if hasattr(row, 'keys') else row[5],
            'second_reading': row['second_reading'] if hasattr(row, 'keys') else row[6],
            'gospel': row['gospel'] if hasattr(row, 'keys') else row[7]
        })

    return result


def get_liturgical_season(conn, date):
    """Get the liturgical season for a specific date.

    Args:
        conn: Database connection.
        date: Date string in YYYY-MM-DD format.

    Returns:
        dict: Season info with name and color, or ordinary if not found.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT name, color
           FROM liturgical_seasons
           WHERE start_date <= ? AND end_date >= ?''',
        (date, date)
    )
    row = cursor.fetchone()

    if row is None:
        return {'name': 'ordinary', 'color': 'green'}

    return {
        'name': row['name'] if hasattr(row, 'keys') else row[0],
        'color': row['color'] if hasattr(row, 'keys') else row[1]
    }


def get_lectionary_year(date):
    """Get the lectionary year (A, B, or C) for a date.

    The lectionary follows a 3-year cycle:
    - Year A: years where (year - 1) % 3 == 0 (e.g., 2023)
    - Year B: years where (year - 1) % 3 == 1 (e.g., 2024)
    - Year C: years where (year - 1) % 3 == 2 (e.g., 2025)

    Args:
        date: Date string in YYYY-MM-DD format.

    Returns:
        str: "A", "B", or "C".
    """
    year = int(date.split('-')[0])
    remainder = (year - 1) % 3

    if remainder == 0:
        return "A"
    elif remainder == 1:
        return "B"
    else:
        return "C"


def get_special_occasions(conn, year):
    """Get special occasions for a specific year.

    Args:
        conn: Database connection.
        year: Year as integer.

    Returns:
        list: List of occasion dicts with name, date, and moveable status.
    """
    cursor = conn.cursor()

    year_str = str(year)

    cursor.execute(
        '''SELECT name, date, moveable
           FROM special_occasions
           WHERE date LIKE ?''',
        (f'{year_str}%',)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'name': row['name'] if hasattr(row, 'keys') else row[0],
            'date': row['date'] if hasattr(row, 'keys') else row[1],
            'moveable': bool(row['moveable'] if hasattr(row, 'keys') else row[2])
        })

    return result


def search_lectionary_by_passage(conn, passage):
    """Search for dates when a passage is read in the lectionary.

    Args:
        conn: Database connection.
        passage: Passage reference to search for.

    Returns:
        list: List of dicts with date, name, and reading type.
    """
    cursor = conn.cursor()

    search_pattern = f'%{passage}%'

    cursor.execute(
        '''SELECT date, name, first_reading, psalm, second_reading, gospel
           FROM lectionary_readings
           WHERE first_reading LIKE ?
              OR psalm LIKE ?
              OR second_reading LIKE ?
              OR gospel LIKE ?
           ORDER BY date''',
        (search_pattern, search_pattern, search_pattern, search_pattern)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        date = row['date'] if hasattr(row, 'keys') else row[0]
        name = row['name'] if hasattr(row, 'keys') else row[1]
        first_reading = row['first_reading'] if hasattr(row, 'keys') else row[2]
        psalm = row['psalm'] if hasattr(row, 'keys') else row[3]
        second_reading = row['second_reading'] if hasattr(row, 'keys') else row[4]
        gospel = row['gospel'] if hasattr(row, 'keys') else row[5]

        reading_type = None
        if first_reading and passage in first_reading:
            reading_type = 'first_reading'
        elif psalm and passage in psalm:
            reading_type = 'psalm'
        elif second_reading and passage in second_reading:
            reading_type = 'second_reading'
        elif gospel and passage in gospel:
            reading_type = 'gospel'

        result.append({
            'date': date,
            'name': name,
            'reading_type': reading_type
        })

    return result


def get_season_readings(conn, season, year=None):
    """Get all readings for a liturgical season.

    Args:
        conn: Database connection.
        season: Season name (e.g., 'advent', 'lent').
        year: Optional lectionary year ('A', 'B', or 'C').

    Returns:
        list: List of reading dicts for the season.
    """
    cursor = conn.cursor()

    if year:
        cursor.execute(
            '''SELECT date, year, season, name, first_reading, psalm,
                      second_reading, gospel
               FROM lectionary_readings
               WHERE season = ? AND year = ?
               ORDER BY date''',
            (season, year)
        )
    else:
        cursor.execute(
            '''SELECT date, year, season, name, first_reading, psalm,
                      second_reading, gospel
               FROM lectionary_readings
               WHERE season = ?
               ORDER BY date''',
            (season,)
        )

    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'date': row['date'] if hasattr(row, 'keys') else row[0],
            'year': row['year'] if hasattr(row, 'keys') else row[1],
            'season': row['season'] if hasattr(row, 'keys') else row[2],
            'name': row['name'] if hasattr(row, 'keys') else row[3],
            'first_reading': row['first_reading'] if hasattr(row, 'keys') else row[4],
            'psalm': row['psalm'] if hasattr(row, 'keys') else row[5],
            'second_reading': row['second_reading'] if hasattr(row, 'keys') else row[6],
            'gospel': row['gospel'] if hasattr(row, 'keys') else row[7]
        })

    return result


def suggest_passages_for_date(conn, date):
    """Suggest passages for a specific date based on lectionary.

    Args:
        conn: Database connection.
        date: Date string in YYYY-MM-DD format.

    Returns:
        list: List of suggestion dicts with passage, type, and occasion.
    """
    reading = get_lectionary_readings(conn, date)

    if reading is None:
        return []

    result = []
    occasion = reading.get('name', '')

    if reading.get('first_reading'):
        result.append({
            'passage': reading['first_reading'],
            'type': 'first_reading',
            'occasion': occasion
        })

    if reading.get('psalm'):
        result.append({
            'passage': reading['psalm'],
            'type': 'psalm',
            'occasion': occasion
        })

    if reading.get('second_reading'):
        result.append({
            'passage': reading['second_reading'],
            'type': 'second_reading',
            'occasion': occasion
        })

    if reading.get('gospel'):
        result.append({
            'passage': reading['gospel'],
            'type': 'gospel',
            'occasion': occasion
        })

    return result
