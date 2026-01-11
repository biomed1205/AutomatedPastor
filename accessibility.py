"""Accessibility Utilities (Issue #218)

Phase 9: UI/UX Design - Item 3

Provides accessibility utilities:
- ARIA utilities (attributes, live regions, labels)
- Focus management (trap, skip link, visible focus)
- Keyboard navigation (handlers, tabindex, roving)
- Screen reader support (sr-only, announcements, dates)
- Color and contrast (WCAG checks, high contrast)
"""

from datetime import datetime, date


def get_aria_attributes(role):
    """Return ARIA attributes for a given role.

    Args:
        role: ARIA role name.

    Returns:
        dict: ARIA attributes for the role.
    """
    if role is None:
        return {}

    roles = {
        'button': {
            'role': 'button',
            'tabindex': '0',
        },
        'dialog': {
            'role': 'dialog',
            'aria-modal': 'true',
        },
        'navigation': {
            'role': 'navigation',
        },
        'alert': {
            'role': 'alert',
            'aria-live': 'assertive',
        },
        'menu': {
            'role': 'menu',
            'aria-expanded': 'false',
            'aria-haspopup': 'true',
        },
        'listbox': {
            'role': 'listbox',
            'aria-activedescendant': '',
        },
        'toolbar': {
            'role': 'toolbar',
            'aria-orientation': 'horizontal',
        },
    }

    return roles.get(role, {'role': role})


def get_live_region_attributes(politeness, atomic=False, relevant=None):
    """Return live region attributes.

    Args:
        politeness: 'polite', 'assertive', or 'off'.
        atomic: Whether to announce whole region.
        relevant: What changes are relevant.

    Returns:
        dict: Live region ARIA attributes.
    """
    attrs = {'aria-live': politeness}

    if atomic:
        attrs['aria-atomic'] = 'true'

    if relevant:
        attrs['aria-relevant'] = relevant

    return attrs


def get_labelledby_id(id_or_ids):
    """Generate aria-labelledby reference.

    Args:
        id_or_ids: Single ID string or list of IDs.

    Returns:
        str: Space-separated IDs for aria-labelledby.
    """
    if isinstance(id_or_ids, list):
        return ' '.join(id_or_ids)
    return id_or_ids


def get_focus_trap_config():
    """Return focus trap configuration.

    Returns:
        dict: Focus trap options.
    """
    return {
        'initialFocus': '[autofocus]',
        'fallbackFocus': '[role="dialog"]',
        'escapeDeactivates': True,
        'clickOutsideDeactivates': True,
        'returnFocusOnDeactivate': True,
        'allowOutsideClick': False,
        'backdrop': True,
    }


def get_skip_link_styles():
    """Return skip to content link styles.

    Returns:
        dict: Skip link styles.
    """
    return {
        'default': {
            'position': 'absolute',
            'top': '-9999px',
            'left': '0',
            'background': '#000000',
            'color': '#FFFFFF',
            'padding': '1rem',
            'zIndex': '100',
            'clip': 'rect(0, 0, 0, 0)',
        },
        'focus': {
            'top': '0',
            'clip': 'auto',
            'outline': '2px solid #C2410C',
            'outlineOffset': '2px',
        },
        ':focus': {
            'top': '0',
            'clip': 'auto',
        },
    }


def get_focus_visible_styles():
    """Return focus-visible indicator styles.

    Returns:
        dict: Focus visible styles.
    """
    return {
        'outline': '2px solid #C2410C',
        'outlineOffset': '2px',
        'ring': '2px',
        'ringColor': '#C2410C',
        'boxShadow': '0 0 0 2px #C2410C',
    }


def get_keyboard_handler_config(element_type):
    """Return keyboard handler configuration.

    Args:
        element_type: Type of element (menu, dialog, listbox, toolbar).

    Returns:
        dict: Keyboard handler configuration.
    """
    configs = {
        'menu': {
            'ArrowUp': 'previous',
            'ArrowDown': 'next',
            'Home': 'first',
            'End': 'last',
            'Escape': 'close',
            'Enter': 'select',
            'Tab': 'exit',
        },
        'dialog': {
            'Escape': 'close',
            'Tab': 'focusNext',
            'Shift+Tab': 'focusPrevious',
        },
        'listbox': {
            'ArrowUp': 'previous',
            'ArrowDown': 'next',
            'Enter': 'select',
            'Space': 'select',
            'Home': 'first',
            'End': 'last',
        },
        'toolbar': {
            'ArrowLeft': 'previous',
            'ArrowRight': 'next',
            'Tab': 'exit',
            'Home': 'first',
            'End': 'last',
        },
    }

    return configs.get(element_type, {'Tab': 'focusNext'})


def get_tabindex_strategy(context):
    """Return tabindex management strategy.

    Args:
        context: Context type (form, modal, skip-content).

    Returns:
        dict: Tabindex strategy configuration.
    """
    strategies = {
        'form': {
            'focusableElements': 'input, button, select, textarea',
            'tabindex': '0',
        },
        'modal': {
            'trapFocus': True,
            'focusFirst': True,
            'restoreFocus': True,
        },
        'skip-content': {
            'tabindex': '-1',
            'skipToContent': True,
        },
    }

    return strategies.get(context, {'tabindex': '0'})


def get_roving_tabindex_config(orientation='vertical'):
    """Return roving tabindex configuration.

    Args:
        orientation: 'horizontal' or 'vertical'.

    Returns:
        dict: Roving tabindex configuration.
    """
    config = {
        'wrap': True,
        'loop': True,
        'cycle': True,
        'currentIndex': 0,
        'orientation': orientation,
    }

    if orientation == 'horizontal':
        config['ArrowLeft'] = 'prev'
        config['ArrowRight'] = 'next'
    else:
        config['ArrowUp'] = 'prev'
        config['ArrowDown'] = 'next'

    return config


def get_sr_only_styles():
    """Return screen reader only styles.

    Returns:
        dict: Styles that hide visually but remain accessible.
    """
    return {
        'position': 'absolute',
        'width': '1px',
        'height': '1px',
        'padding': '0',
        'margin': '-1px',
        'overflow': 'hidden',
        'clip': 'rect(0, 0, 0, 0)',
        'whiteSpace': 'nowrap',
        'borderWidth': '0',
    }


def get_announcement_config(priority='polite'):
    """Return screen reader announcement configuration.

    Args:
        priority: 'polite' or 'assertive'.

    Returns:
        dict: Announcement configuration.
    """
    return {
        'aria-live': priority,
        'priority': priority,
        'clearDelay': 1000,
        'timeout': 5000,
        'role': 'status' if priority == 'polite' else 'alert',
    }


def format_readable_date(date_obj):
    """Format date for screen reader readability.

    Args:
        date_obj: Date or datetime object.

    Returns:
        str: Human-readable date string.
    """
    if isinstance(date_obj, str):
        raise ValueError("Expected date or datetime object")

    if isinstance(date_obj, datetime):
        d = date_obj.date()
    elif isinstance(date_obj, date):
        d = date_obj
    else:
        raise TypeError("Expected date or datetime object")

    return d.strftime('%B %d, %Y')


def check_contrast_ratio(color1, color2):
    """Check WCAG contrast ratio between two colors.

    Args:
        color1: First hex color.
        color2: Second hex color.

    Returns:
        dict: Contrast ratio and WCAG compliance.
    """
    if not color1 or not color2:
        raise ValueError("Colors cannot be empty")

    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def get_luminance(rgb):
        def adjust(c):
            c = c / 255
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = rgb
        return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)

    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    l1 = get_luminance(rgb1)
    l2 = get_luminance(rgb2)

    lighter = max(l1, l2)
    darker = min(l1, l2)

    ratio = (lighter + 0.05) / (darker + 0.05)

    return {
        'ratio': ratio,
        'aa_pass': ratio >= 4.5,
        'aa_large_pass': ratio >= 3.0,
        'aaa_pass': ratio >= 7.0,
        'wcag': 'AAA' if ratio >= 7.0 else ('AA' if ratio >= 4.5 else 'fail'),
    }


def get_high_contrast_colors():
    """Return high contrast mode colors.

    Returns:
        dict: High contrast color palette.
    """
    return {
        'text': '#000000',
        'foreground': '#000000',
        'background': '#FFFFFF',
        'link': '#0000EE',
        'accent': '#0000FF',
        'visited': '#551A8B',
        'border': '#000000',
    }
