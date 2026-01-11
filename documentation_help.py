"""Documentation and Help System (Issue #230)

Phase 10: Polish - Item 3

Provides documentation and help utilities:
- Help content retrieval
- Documentation sections
- Search functionality
- Contextual help
- Tutorial system
"""

from datetime import datetime


# Help topics content
HELP_TOPICS = {
    'getting-started': {
        'name': 'getting-started',
        'title': 'Getting Started',
        'category': 'basics',
        'content': 'Welcome to AutomatedPastor! This guide will help you create your first sermon.'
    },
    'sermon-creation': {
        'name': 'sermon-creation',
        'title': 'Creating a Sermon',
        'category': 'features',
        'content': 'Learn how to create, edit, and generate sermons with AI assistance.'
    },
    'scripture-input': {
        'name': 'scripture-input',
        'title': 'Scripture Input',
        'category': 'features',
        'content': 'How to enter and format scripture references for sermon generation.'
    },
    'reviewer-panel': {
        'name': 'reviewer-panel',
        'title': 'Reviewer Panel',
        'category': 'features',
        'content': 'Use the reviewer panel to get feedback from multiple theological perspectives.'
    },
}

# Documentation sections
DOCUMENTATION = {
    'overview': {
        'title': 'Overview',
        'content': 'AutomatedPastor is a sermon generation tool designed for pastors and preachers.',
        'body': 'AutomatedPastor helps you create well-structured sermons with theological depth.'
    },
    'features': {
        'title': 'Features',
        'content': 'AI-powered sermon generation, practice timing, reviewer panel, and more.',
        'body': 'Explore all the features that make sermon preparation easier.'
    },
}

# Feature guides
FEATURE_GUIDES = {
    'sermon-generation': {
        'title': 'Sermon Generation',
        'content': 'Learn how to use the AI-powered sermon generation feature.',
        'usage': 'Enter your scripture text and theme, then click Generate.'
    },
    'reviewer-panel': {
        'title': 'Reviewer Panel',
        'content': 'Get feedback from multiple theological perspectives.',
        'usage': 'After generating a sermon, click Review to see feedback from various reviewers.'
    },
}

# Tooltips
TOOLTIPS = {
    'generate-button': 'Click to generate a sermon based on your input',
    'save-button': 'Save the current sermon to your archive',
    'scripture-input': 'Enter the primary scripture for your sermon',
    'theme-input': 'Enter the main theme or topic',
}

# Keyboard shortcuts
KEYBOARD_SHORTCUTS = [
    {'key': 'Ctrl+S', 'keys': 'Ctrl+S', 'shortcut': 'Ctrl+S', 'action': 'Save', 'description': 'Save sermon'},
    {'key': 'Ctrl+G', 'keys': 'Ctrl+G', 'shortcut': 'Ctrl+G', 'action': 'Generate', 'description': 'Generate sermon'},
    {'key': 'Ctrl+N', 'keys': 'Ctrl+N', 'shortcut': 'Ctrl+N', 'action': 'New', 'description': 'Create new sermon'},
    {'key': 'Ctrl+P', 'keys': 'Ctrl+P', 'shortcut': 'Ctrl+P', 'action': 'Practice', 'description': 'Start practice mode'},
    {'key': 'Esc', 'keys': 'Esc', 'shortcut': 'Esc', 'action': 'Cancel', 'description': 'Cancel current operation'},
]

# FAQ content
FAQ = [
    {'question': 'How do I create my first sermon?', 'q': 'How do I create my first sermon?',
     'answer': 'Enter your scripture and theme, then click Generate.', 'a': 'Enter your scripture and theme, then click Generate.'},
    {'question': 'What theological traditions are supported?', 'q': 'What theological traditions are supported?',
     'answer': 'We support Wesleyan, Reformed, Lutheran, Baptist, and more.', 'a': 'We support Wesleyan, Reformed, Lutheran, Baptist, and more.'},
    {'question': 'Can I edit the generated sermon?', 'q': 'Can I edit the generated sermon?',
     'answer': 'Yes, all sermons are fully editable after generation.', 'a': 'Yes, all sermons are fully editable after generation.'},
    {'question': 'How does the practice timer work?', 'q': 'How does the practice timer work?',
     'answer': 'The practice timer helps you track your delivery time and pacing.', 'a': 'The practice timer helps you track your delivery time and pacing.'},
]

# Tutorials
TUTORIALS = {
    'first-sermon': {
        'name': 'first-sermon',
        'title': 'Creating Your First Sermon',
        'description': 'A step-by-step guide to creating your first AI-assisted sermon.',
        'steps': [
            {'order': 1, 'content': 'Enter your scripture reference in the Scripture field', 'text': 'Enter your scripture reference', 'instruction': 'Enter scripture'},
            {'order': 2, 'content': 'Add a theme or topic for your sermon', 'text': 'Add a theme', 'instruction': 'Add theme'},
            {'order': 3, 'content': 'Click the Generate button to create your sermon', 'text': 'Click Generate', 'instruction': 'Generate sermon'},
            {'order': 4, 'content': 'Review and edit the generated content', 'text': 'Review content', 'instruction': 'Review and edit'},
            {'order': 5, 'content': 'Save your sermon to the archive', 'text': 'Save sermon', 'instruction': 'Save to archive'},
        ]
    },
    'advanced-features': {
        'name': 'advanced-features',
        'title': 'Advanced Features',
        'description': 'Learn about advanced features like the reviewer panel and practice timing.',
        'steps': [
            {'order': 1, 'content': 'Explore the reviewer panel for feedback', 'text': 'Use reviewer panel', 'instruction': 'Get feedback'},
            {'order': 2, 'content': 'Use practice timing to refine delivery', 'text': 'Practice timing', 'instruction': 'Time your practice'},
        ]
    },
}


def get_help_content(topic):
    """Get help content for a topic.

    Args:
        topic: Topic name.

    Returns:
        dict: Help content or None if not found.
    """
    return HELP_TOPICS.get(topic)


def get_all_help_topics():
    """Get all help topics.

    Returns:
        list: List of help topic dicts.
    """
    return list(HELP_TOPICS.values())


def search_help(query):
    """Search help content.

    Args:
        query: Search query string.

    Returns:
        list: Matching help topics.
    """
    if not query:
        return []

    query_lower = query.lower()
    results = []

    for topic in HELP_TOPICS.values():
        title = topic.get('title', '').lower()
        content = topic.get('content', '').lower()
        name = topic.get('name', '').lower()

        if query_lower in title or query_lower in content or query_lower in name:
            results.append(topic)

    return results


def get_documentation(section):
    """Get documentation section.

    Args:
        section: Section name.

    Returns:
        dict: Documentation section or None if not found.
    """
    return DOCUMENTATION.get(section)


def get_quick_start_guide():
    """Get quick start guide.

    Returns:
        dict: Quick start guide content.
    """
    return {
        'title': 'Quick Start Guide',
        'content': '''Welcome to AutomatedPastor! Here is how to get started:

Step 1: Enter your scripture reference
Step 2: Add a theme or topic
Step 3: Click Generate to create your sermon
Step 4: Review and edit the content
Step 5: Save to your archive

You are now ready to create your first sermon!''',
        'steps': [
            'Enter your scripture reference',
            'Add a theme or topic',
            'Click Generate to create your sermon',
            'Review and edit the content',
            'Save to your archive',
        ]
    }


def get_feature_guide(feature):
    """Get guide for a feature.

    Args:
        feature: Feature name.

    Returns:
        dict: Feature guide or None if not found.
    """
    return FEATURE_GUIDES.get(feature)


def get_faq():
    """Get FAQ content.

    Returns:
        list: FAQ Q&A pairs.
    """
    return FAQ


def get_tooltip(element):
    """Get tooltip for an element.

    Args:
        element: Element identifier.

    Returns:
        str: Tooltip text or None if not found.
    """
    return TOOLTIPS.get(element)


def get_contextual_help(page, element):
    """Get contextual help for a page element.

    Args:
        page: Page name.
        element: Element identifier.

    Returns:
        str: Contextual help text or None.
    """
    # Check tooltip first
    tooltip = TOOLTIPS.get(element)
    if tooltip:
        return f"[{page}] {tooltip}"

    # Check help topics
    topic = HELP_TOPICS.get(element)
    if topic:
        return topic.get('content')

    return None


def get_keyboard_shortcuts():
    """Get keyboard shortcuts.

    Returns:
        list: List of keyboard shortcuts.
    """
    return KEYBOARD_SHORTCUTS


def get_tutorial(tutorial_name):
    """Get tutorial content.

    Args:
        tutorial_name: Tutorial name.

    Returns:
        dict: Tutorial content or None if not found.
    """
    return TUTORIALS.get(tutorial_name)


def get_tutorial_steps(tutorial_name):
    """Get tutorial steps.

    Args:
        tutorial_name: Tutorial name.

    Returns:
        list: List of tutorial steps.
    """
    tutorial = TUTORIALS.get(tutorial_name)
    if tutorial:
        return tutorial.get('steps', [])
    return []


def mark_tutorial_complete(conn, user_id, tutorial_name):
    """Mark a tutorial as complete for a user.

    Args:
        conn: Database connection.
        user_id: User ID.
        tutorial_name: Tutorial name.

    Returns:
        bool: True if marked complete.
    """
    cursor = conn.cursor()

    # Check if already completed
    cursor.execute('''
        SELECT id FROM tutorial_progress
        WHERE user_id = ? AND tutorial_name = ?
    ''', (user_id, tutorial_name))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE tutorial_progress SET completed_at = ?
            WHERE user_id = ? AND tutorial_name = ?
        ''', (datetime.now().isoformat(), user_id, tutorial_name))
    else:
        cursor.execute('''
            INSERT INTO tutorial_progress (user_id, tutorial_name, completed_at)
            VALUES (?, ?, ?)
        ''', (user_id, tutorial_name, datetime.now().isoformat()))

    conn.commit()
    return True


def get_completed_tutorials(conn, user_id):
    """Get list of completed tutorials for a user.

    Args:
        conn: Database connection.
        user_id: User ID.

    Returns:
        list: List of completed tutorial names.
    """
    cursor = conn.cursor()

    cursor.execute('''
        SELECT tutorial_name FROM tutorial_progress
        WHERE user_id = ?
    ''', (user_id,))
    rows = cursor.fetchall()

    return [row['tutorial_name'] if hasattr(row, 'keys') else row[0] for row in rows]
