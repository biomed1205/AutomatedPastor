"""Passage suggestion engine for sermon series planning.

Provides intelligent passage recommendations based on themes, series context,
and user preferences.
"""
import json
from datetime import datetime, timedelta


# Theme-based passage database
THEME_PASSAGES = {
    'hope': [
        {'reference': 'Romans 15:13', 'testament': 'NT', 'genre': 'epistle', 'themes': 'hope,joy,peace'},
        {'reference': 'Jeremiah 29:11', 'testament': 'OT', 'genre': 'prophecy', 'themes': 'hope,future,plans'},
        {'reference': 'Psalm 42:5', 'testament': 'OT', 'genre': 'poetry', 'themes': 'hope,soul,praise'},
        {'reference': 'Hebrews 6:19', 'testament': 'NT', 'genre': 'epistle', 'themes': 'hope,anchor,faith'},
        {'reference': 'Romans 8:24-25', 'testament': 'NT', 'genre': 'epistle', 'themes': 'hope,patience,salvation'},
        {'reference': 'Lamentations 3:21-24', 'testament': 'OT', 'genre': 'poetry', 'themes': 'hope,mercy,faithfulness'},
        {'reference': '1 Peter 1:3', 'testament': 'NT', 'genre': 'epistle', 'themes': 'hope,resurrection,mercy'},
        {'reference': 'Isaiah 40:31', 'testament': 'OT', 'genre': 'prophecy', 'themes': 'hope,strength,renewal'}
    ],
    'love': [
        {'reference': '1 Corinthians 13:4-7', 'testament': 'NT', 'genre': 'epistle', 'themes': 'love,patience,kindness'},
        {'reference': '1 John 4:7-8', 'testament': 'NT', 'genre': 'epistle', 'themes': 'love,god,born'},
        {'reference': 'John 3:16', 'testament': 'NT', 'genre': 'gospel', 'themes': 'love,salvation,eternal'},
        {'reference': 'Romans 8:38-39', 'testament': 'NT', 'genre': 'epistle', 'themes': 'love,inseparable,christ'},
        {'reference': 'John 15:12-17', 'testament': 'NT', 'genre': 'gospel', 'themes': 'love,friends,commandment'},
        {'reference': 'Song of Solomon 8:6-7', 'testament': 'OT', 'genre': 'poetry', 'themes': 'love,strong,waters'},
        {'reference': 'Matthew 22:37-40', 'testament': 'NT', 'genre': 'gospel', 'themes': 'love,commandment,neighbor'},
        {'reference': 'Ephesians 5:25', 'testament': 'NT', 'genre': 'epistle', 'themes': 'love,christ,church'}
    ],
    'faith': [
        {'reference': 'Hebrews 11:1', 'testament': 'NT', 'genre': 'epistle', 'themes': 'faith,substance,evidence'},
        {'reference': 'Romans 10:17', 'testament': 'NT', 'genre': 'epistle', 'themes': 'faith,hearing,word'},
        {'reference': 'James 2:14-26', 'testament': 'NT', 'genre': 'epistle', 'themes': 'faith,works,dead'},
        {'reference': 'Mark 11:22-24', 'testament': 'NT', 'genre': 'gospel', 'themes': 'faith,mountain,prayer'},
        {'reference': 'Matthew 17:20', 'testament': 'NT', 'genre': 'gospel', 'themes': 'faith,mustard,nothing'},
        {'reference': 'Galatians 2:20', 'testament': 'NT', 'genre': 'epistle', 'themes': 'faith,christ,live'},
        {'reference': 'Habakkuk 2:4', 'testament': 'OT', 'genre': 'prophecy', 'themes': 'faith,righteous,live'},
        {'reference': '2 Corinthians 5:7', 'testament': 'NT', 'genre': 'epistle', 'themes': 'faith,walk,sight'}
    ],
    'grace': [
        {'reference': 'Ephesians 2:8-9', 'testament': 'NT', 'genre': 'epistle', 'themes': 'grace,saved,faith'},
        {'reference': '2 Corinthians 12:9', 'testament': 'NT', 'genre': 'epistle', 'themes': 'grace,sufficient,power'},
        {'reference': 'Romans 6:14', 'testament': 'NT', 'genre': 'epistle', 'themes': 'grace,sin,dominion'},
        {'reference': 'Titus 2:11-12', 'testament': 'NT', 'genre': 'epistle', 'themes': 'grace,salvation,teaching'},
        {'reference': 'John 1:16-17', 'testament': 'NT', 'genre': 'gospel', 'themes': 'grace,fullness,truth'},
        {'reference': 'Romans 5:20-21', 'testament': 'NT', 'genre': 'epistle', 'themes': 'grace,abounded,sin'},
        {'reference': '2 Peter 3:18', 'testament': 'NT', 'genre': 'epistle', 'themes': 'grace,grow,knowledge'},
        {'reference': 'Hebrews 4:16', 'testament': 'NT', 'genre': 'epistle', 'themes': 'grace,throne,mercy'}
    ],
    'forgiveness': [
        {'reference': '1 John 1:9', 'testament': 'NT', 'genre': 'epistle', 'themes': 'forgiveness,confess,cleanse'},
        {'reference': 'Colossians 3:13', 'testament': 'NT', 'genre': 'epistle', 'themes': 'forgiveness,bearing,lord'},
        {'reference': 'Ephesians 4:32', 'testament': 'NT', 'genre': 'epistle', 'themes': 'forgiveness,kind,tenderhearted'},
        {'reference': 'Matthew 6:14-15', 'testament': 'NT', 'genre': 'gospel', 'themes': 'forgiveness,father,trespasses'},
        {'reference': 'Psalm 103:12', 'testament': 'OT', 'genre': 'poetry', 'themes': 'forgiveness,east,west'},
        {'reference': 'Acts 3:19', 'testament': 'NT', 'genre': 'narrative', 'themes': 'forgiveness,repent,refreshing'},
        {'reference': 'Isaiah 1:18', 'testament': 'OT', 'genre': 'prophecy', 'themes': 'forgiveness,scarlet,white'},
        {'reference': 'Matthew 18:21-22', 'testament': 'NT', 'genre': 'gospel', 'themes': 'forgiveness,seventy,times'}
    ],
    'repentance': [
        {'reference': '2 Chronicles 7:14', 'testament': 'OT', 'genre': 'narrative', 'themes': 'repentance,humble,pray'},
        {'reference': 'Acts 3:19', 'testament': 'NT', 'genre': 'narrative', 'themes': 'repentance,turn,refreshing'},
        {'reference': 'Joel 2:12-13', 'testament': 'OT', 'genre': 'prophecy', 'themes': 'repentance,heart,gracious'},
        {'reference': 'Luke 15:7', 'testament': 'NT', 'genre': 'gospel', 'themes': 'repentance,joy,heaven'},
        {'reference': 'Romans 2:4', 'testament': 'NT', 'genre': 'epistle', 'themes': 'repentance,kindness,patience'},
        {'reference': 'Ezekiel 18:30-32', 'testament': 'OT', 'genre': 'prophecy', 'themes': 'repentance,turn,live'},
        {'reference': 'Matthew 4:17', 'testament': 'NT', 'genre': 'gospel', 'themes': 'repentance,kingdom,near'},
        {'reference': '2 Peter 3:9', 'testament': 'NT', 'genre': 'epistle', 'themes': 'repentance,patient,perish'}
    ],
    'resurrection': [
        {'reference': 'John 11:25-26', 'testament': 'NT', 'genre': 'gospel', 'themes': 'resurrection,life,believe'},
        {'reference': '1 Corinthians 15:20-22', 'testament': 'NT', 'genre': 'epistle', 'themes': 'resurrection,firstfruits,adam'},
        {'reference': 'Romans 6:4-5', 'testament': 'NT', 'genre': 'epistle', 'themes': 'resurrection,newness,life'},
        {'reference': 'Philippians 3:10-11', 'testament': 'NT', 'genre': 'epistle', 'themes': 'resurrection,power,suffering'},
        {'reference': '1 Peter 1:3', 'testament': 'NT', 'genre': 'epistle', 'themes': 'resurrection,hope,mercy'},
        {'reference': 'Colossians 3:1', 'testament': 'NT', 'genre': 'epistle', 'themes': 'resurrection,raised,christ'},
        {'reference': 'John 5:28-29', 'testament': 'NT', 'genre': 'gospel', 'themes': 'resurrection,hour,tombs'},
        {'reference': 'Revelation 21:4', 'testament': 'NT', 'genre': 'prophecy', 'themes': 'resurrection,tears,death'}
    ],
    'default': [
        {'reference': 'John 3:16', 'testament': 'NT', 'genre': 'gospel', 'themes': 'love,salvation,eternal'},
        {'reference': 'Psalm 23:1', 'testament': 'OT', 'genre': 'poetry', 'themes': 'shepherd,comfort,provision'},
        {'reference': 'Romans 8:28', 'testament': 'NT', 'genre': 'epistle', 'themes': 'hope,providence,good'},
        {'reference': 'Philippians 4:13', 'testament': 'NT', 'genre': 'epistle', 'themes': 'strength,christ,all'},
        {'reference': 'Matthew 28:18-20', 'testament': 'NT', 'genre': 'gospel', 'themes': 'commission,authority,disciples'},
        {'reference': 'Proverbs 3:5-6', 'testament': 'OT', 'genre': 'wisdom', 'themes': 'trust,lean,acknowledge'},
        {'reference': 'Isaiah 40:31', 'testament': 'OT', 'genre': 'prophecy', 'themes': 'hope,strength,wait'},
        {'reference': 'Psalm 46:10', 'testament': 'OT', 'genre': 'poetry', 'themes': 'peace,still,god'},
        {'reference': 'Jeremiah 29:11', 'testament': 'OT', 'genre': 'prophecy', 'themes': 'hope,future,plans'},
        {'reference': 'Romans 12:2', 'testament': 'NT', 'genre': 'epistle', 'themes': 'transformation,mind,renewal'},
        {'reference': 'Galatians 5:22-23', 'testament': 'NT', 'genre': 'epistle', 'themes': 'fruit,spirit,love'},
        {'reference': '1 Peter 5:7', 'testament': 'NT', 'genre': 'epistle', 'themes': 'anxiety,cast,cares'}
    ]
}

# Passage context database
PASSAGE_CONTEXTS = {
    'John 3:16': {
        'book': 'John',
        'testament': 'NT',
        'author': 'John the Apostle',
        'context': 'Jesus speaking to Nicodemus about being born again',
        'background': 'Part of Jesus\' conversation with a Pharisee at night about spiritual rebirth'
    },
    'Romans 8:28': {
        'book': 'Romans',
        'testament': 'NT',
        'author': 'Paul',
        'context': 'Paul discussing the security of believers in Christ',
        'background': 'Written to the church in Rome explaining the gospel and Christian living'
    },
    'Genesis 1:1': {
        'book': 'Genesis',
        'testament': 'OT',
        'author': 'Moses (traditional)',
        'context': 'The opening verse of the Bible describing creation',
        'background': 'The foundational account of God creating the universe'
    },
    'Psalm 23:1': {
        'book': 'Psalms',
        'testament': 'OT',
        'author': 'David',
        'context': 'A psalm of trust and confidence in God as shepherd',
        'background': 'Written by David, likely reflecting on his time as a shepherd'
    },
    'Isaiah 53:5': {
        'book': 'Isaiah',
        'testament': 'OT',
        'author': 'Isaiah',
        'context': 'The Suffering Servant prophecy about the Messiah',
        'background': 'Prophetic description of the Messiah\'s atoning work, fulfilled in Christ'
    },
    '1 John 4:7-8': {
        'book': '1 John',
        'testament': 'NT',
        'author': 'John the Apostle',
        'context': 'John teaching about the nature of God as love',
        'background': 'A letter addressing the importance of love in the Christian community'
    }
}

# Complementary passages database
COMPLEMENTARY_PASSAGES = {
    'John 3:16': [
        {'reference': 'Romans 5:8', 'relationship': 'God\'s love demonstrated'},
        {'reference': '1 John 4:9-10', 'relationship': 'God\'s love sent His Son'},
        {'reference': 'Ephesians 2:4-5', 'relationship': 'God\'s love and mercy'}
    ],
    'Romans 8:28': [
        {'reference': 'Jeremiah 29:11', 'relationship': 'God\'s good plans'},
        {'reference': 'Genesis 50:20', 'relationship': 'God works through difficulty'},
        {'reference': 'Philippians 1:6', 'relationship': 'God will complete His work'}
    ],
    'Psalm 23:1': [
        {'reference': 'John 10:11', 'relationship': 'Jesus the Good Shepherd'},
        {'reference': 'Isaiah 40:11', 'relationship': 'God tends His flock'},
        {'reference': 'Ezekiel 34:11-12', 'relationship': 'God searches for His sheep'}
    ],
    'Isaiah 53:5': [
        {'reference': '1 Peter 2:24', 'relationship': 'NT fulfillment of the prophecy'},
        {'reference': 'Matthew 8:17', 'relationship': 'Jesus fulfills Isaiah\'s words'},
        {'reference': 'Acts 8:32-35', 'relationship': 'Philip explains Isaiah to the Ethiopian'}
    ],
    'default': [
        {'reference': 'John 14:6', 'relationship': 'Jesus as the way'},
        {'reference': 'Hebrews 4:12', 'relationship': 'The power of God\'s Word'},
        {'reference': 'Romans 10:9', 'relationship': 'Salvation through confession'}
    ]
}


def suggest_passages_for_theme(theme, count=5):
    """Suggest passages based on a theme.

    Args:
        theme: Theme string to search for.
        count: Number of passages to return (default 5).

    Returns:
        list: List of passage dictionaries.
    """
    theme_lower = theme.lower().strip() if theme else ''

    # Find matching theme or use default
    passages = None
    for key in THEME_PASSAGES:
        if key in theme_lower or theme_lower in key:
            passages = THEME_PASSAGES[key]
            break

    if passages is None:
        passages = THEME_PASSAGES['default']

    # Return requested count, padding with defaults if needed
    result = []
    seen = set()

    # Add theme-specific passages first
    for p in passages:
        if len(result) >= count:
            break
        if p['reference'] not in seen:
            result.append(p.copy())
            seen.add(p['reference'])

    # Pad with default passages if needed
    if len(result) < count:
        for p in THEME_PASSAGES['default']:
            if len(result) >= count:
                break
            if p['reference'] not in seen:
                result.append(p.copy())
                seen.add(p['reference'])

    return result[:count]


def suggest_passages_for_series(conn, series_id, count=10):
    """Suggest passages based on series context.

    Args:
        conn: Database connection.
        series_id: ID of the series.
        count: Number of passages to return (default 10).

    Returns:
        list: List of passage dictionaries, or None/empty if series not found.
    """
    cursor = conn.cursor()

    # Get series info
    cursor.execute('SELECT theme FROM series WHERE id = ?', (series_id,))
    row = cursor.fetchone()

    if row is None:
        return None

    theme = row['theme'] if hasattr(row, 'keys') else row[0]

    # Get existing sermons to avoid duplicates
    cursor.execute(
        'SELECT scripture FROM sermons WHERE series_id = ?',
        (series_id,)
    )
    used_passages = set()
    for row in cursor.fetchall():
        scripture = row['scripture'] if hasattr(row, 'keys') else row[0]
        if scripture:
            used_passages.add(scripture)

    # Check for stored passages in database
    cursor.execute(
        '''SELECT reference, testament, genre, themes FROM passages
           WHERE themes LIKE ?''',
        (f'%{theme.lower() if theme else ""}%',)
    )
    db_passages = []
    for row in cursor.fetchall():
        db_passages.append({
            'reference': row['reference'] if hasattr(row, 'keys') else row[0],
            'testament': row['testament'] if hasattr(row, 'keys') else row[1],
            'genre': row['genre'] if hasattr(row, 'keys') else row[2],
            'themes': row['themes'] if hasattr(row, 'keys') else row[3]
        })

    # Get theme-based suggestions
    suggestions = suggest_passages_for_theme(theme or '', count=count + len(used_passages))

    # Combine db and theme suggestions
    all_passages = db_passages + suggestions

    # Filter out already used passages
    result = []
    seen = set()
    for p in all_passages:
        ref = p.get('reference', '')
        if ref not in used_passages and ref not in seen:
            result.append(p)
            seen.add(ref)
            if len(result) >= count:
                break

    return result[:count]


def filter_by_testament(passages, testament):
    """Filter passages by testament.

    Args:
        passages: List of passage dictionaries.
        testament: Testament to filter by ('OT' or 'NT').

    Returns:
        list: Filtered passages.
    """
    return [p for p in passages if p.get('testament') == testament]


def filter_by_genre(passages, genre):
    """Filter passages by genre.

    Args:
        passages: List of passage dictionaries.
        genre: Genre to filter by (gospel, epistle, wisdom, prophecy, etc.).

    Returns:
        list: Filtered passages.
    """
    return [p for p in passages if p.get('genre') == genre]


def get_passage_context(passage):
    """Get context and background for a passage.

    Args:
        passage: Passage reference string.

    Returns:
        dict: Context information, or empty dict/None if not found.
    """
    # Normalize the reference
    passage_clean = passage.strip()

    # Check exact match
    if passage_clean in PASSAGE_CONTEXTS:
        return PASSAGE_CONTEXTS[passage_clean].copy()

    # Check partial match (for ranges like 1 John 4:7-8)
    for ref, ctx in PASSAGE_CONTEXTS.items():
        if ref in passage_clean or passage_clean in ref:
            return ctx.copy()

    # Extract book name for basic context
    parts = passage_clean.split()
    if parts:
        book = parts[0]
        if len(parts) > 1 and parts[0] in ('1', '2', '3'):
            book = f"{parts[0]} {parts[1]}"

        # Known Bible books
        all_books = [
            'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
            'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
            '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
            'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalm', 'Psalms',
            'Proverbs', 'Ecclesiastes', 'Song', 'Isaiah', 'Jeremiah',
            'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel',
            'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk',
            'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
            'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans',
            '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
            'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
            '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews',
            'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John',
            'Jude', 'Revelation'
        ]

        # Check if it's a valid book
        if book not in all_books:
            return {}

        ot_books = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
                    'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
                    '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
                    'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalm', 'Psalms',
                    'Proverbs', 'Ecclesiastes', 'Song', 'Isaiah', 'Jeremiah',
                    'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel',
                    'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk',
                    'Zephaniah', 'Haggai', 'Zechariah', 'Malachi']

        testament = 'OT' if book in ot_books else 'NT'

        return {
            'book': book,
            'testament': testament,
            'context': f'Passage from {book}'
        }

    return {}


def suggest_complementary_passages(passage):
    """Suggest complementary passages related to a given passage.

    Args:
        passage: Passage reference string.

    Returns:
        list: List of related passage dictionaries.
    """
    passage_clean = passage.strip()

    # Check exact match
    if passage_clean in COMPLEMENTARY_PASSAGES:
        return [p.copy() for p in COMPLEMENTARY_PASSAGES[passage_clean]]

    # Check partial match
    for ref, complements in COMPLEMENTARY_PASSAGES.items():
        if ref in passage_clean or passage_clean.startswith(ref.split(':')[0]):
            return [p.copy() for p in complements]

    # Return default suggestions
    return [p.copy() for p in COMPLEMENTARY_PASSAGES['default']]


def rank_passages_by_relevance(passages, criteria):
    """Rank passages by relevance to criteria.

    Args:
        passages: List of passage dictionaries.
        criteria: Dictionary of criteria (theme, testament, genre).

    Returns:
        list: Passages ordered by relevance (most relevant first).
    """
    if not passages:
        return []

    if not criteria:
        return passages.copy()

    def score_passage(p):
        score = 0
        themes = p.get('themes', '')

        # Theme matching
        if 'theme' in criteria:
            theme = criteria['theme'].lower()
            if theme in themes.lower():
                score += 10

        # Testament matching
        if 'testament' in criteria:
            if p.get('testament') == criteria['testament']:
                score += 5

        # Genre matching
        if 'genre' in criteria:
            if p.get('genre') == criteria['genre']:
                score += 3

        return score

    # Sort by score descending
    return sorted(passages, key=score_passage, reverse=True)


def cache_suggestions(conn, key, suggestions, ttl=3600):
    """Cache passage suggestions.

    Args:
        conn: Database connection.
        key: Cache key.
        suggestions: List of suggestions to cache.
        ttl: Time to live in seconds (default 3600).

    Returns:
        bool: True if cached successfully.
    """
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(seconds=ttl)

    # Remove existing entry
    cursor.execute('DELETE FROM passage_cache WHERE cache_key = ?', (key,))

    # Insert new entry
    cursor.execute(
        '''INSERT INTO passage_cache (cache_key, suggestions, expires_at)
           VALUES (?, ?, ?)''',
        (key, json.dumps(suggestions), expires_at.isoformat())
    )
    conn.commit()
    return True


def get_cached_suggestions(conn, key):
    """Get cached suggestions if not expired.

    Args:
        conn: Database connection.
        key: Cache key.

    Returns:
        list: Cached suggestions, or None if not found or expired.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT suggestions, expires_at FROM passage_cache
           WHERE cache_key = ?''',
        (key,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    expires_at_str = row['expires_at'] if hasattr(row, 'keys') else row[1]
    expires_at = datetime.fromisoformat(expires_at_str)

    if expires_at <= datetime.now():
        # Expired - clean up
        cursor.execute('DELETE FROM passage_cache WHERE cache_key = ?', (key,))
        conn.commit()
        return None

    suggestions_str = row['suggestions'] if hasattr(row, 'keys') else row[0]
    return json.loads(suggestions_str)
