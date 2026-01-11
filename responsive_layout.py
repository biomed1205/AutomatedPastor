"""Responsive Layout System (Issue #214)

Phase 9: UI/UX Design - Item 2

Provides responsive layout utilities:
- Layout containers (max-width, grid, flexbox)
- Responsive utilities (breakpoint classes, show/hide)
- Navigation (desktop, mobile menu, sidebar)
- Page layouts (standard, sermon editor, dashboard)
- Mobile-first approach
- Touch-friendly spacing
"""


def get_container_styles():
    """Return container style definitions.

    Returns:
        dict: Container styles with max-width, padding, and centering.
    """
    return {
        'maxWidth': '100%',
        'base': {
            'width': '100%',
            'marginLeft': 'auto',
            'marginRight': 'auto',
            'paddingLeft': '1rem',
            'paddingRight': '1rem',
        },
        'sm': {'maxWidth': '640px'},
        'md': {'maxWidth': '768px'},
        'lg': {'maxWidth': '1024px'},
        'xl': {'maxWidth': '1280px'},
    }


def get_grid_system():
    """Return CSS Grid system definitions.

    Returns:
        dict: Grid configuration with 12 columns.
    """
    return {
        'columns': 12,
        'gap': '1rem',
        'templateColumns': {
            'default': 'repeat(12, minmax(0, 1fr))',
            'auto': 'repeat(auto-fit, minmax(250px, 1fr))',
        },
    }


def get_flex_utilities():
    """Return flexbox utility definitions.

    Returns:
        dict: Flexbox utilities for direction, justify, align, wrap.
    """
    return {
        'direction': {
            'row': 'row',
            'row-reverse': 'row-reverse',
            'column': 'column',
            'column-reverse': 'column-reverse',
        },
        'justify': {
            'start': 'flex-start',
            'end': 'flex-end',
            'center': 'center',
            'between': 'space-between',
            'around': 'space-around',
            'evenly': 'space-evenly',
        },
        'align': {
            'start': 'flex-start',
            'end': 'flex-end',
            'center': 'center',
            'stretch': 'stretch',
            'baseline': 'baseline',
        },
        'wrap': {
            'nowrap': 'nowrap',
            'wrap': 'wrap',
            'wrap-reverse': 'wrap-reverse',
        },
    }


def get_responsive_classes(property_name, values):
    """Generate responsive variants of a property.

    Args:
        property_name: CSS property name.
        values: Dict of class names to CSS values.

    Returns:
        dict: Responsive class definitions for all breakpoints.
    """
    breakpoints = ['sm', 'md', 'lg', 'xl']
    result = {
        'base': {},
        'breakpoints': {},
    }

    for name, value in values.items():
        result['base'][name] = {property_name: value}
        for bp in breakpoints:
            if bp not in result['breakpoints']:
                result['breakpoints'][bp] = {}
            result['breakpoints'][bp][f'{bp}:{name}'] = {property_name: value}

    return result


def get_hidden_at_breakpoint(breakpoint, direction='below'):
    """Return class to hide at breakpoint.

    Args:
        breakpoint: Breakpoint name (sm, md, lg, xl).
        direction: 'below' or 'above' the breakpoint.

    Returns:
        dict: CSS rules for hiding.
    """
    if direction == 'below':
        return {
            'base': {'display': 'none'},
            f'{breakpoint}': {'display': 'block'},
        }
    return {
        'base': {'display': 'block'},
        f'{breakpoint}': {'display': 'none'},
    }


def get_column_spans(breakpoint):
    """Return column span definitions for a breakpoint.

    Args:
        breakpoint: Breakpoint name (sm, md, lg, xl).

    Returns:
        dict: Column span classes.
    """
    spans = {
        1: '8.333%',
        2: '16.666%',
        3: '25%',
        4: '33.333%',
        5: '41.666%',
        6: '50%',
        7: '58.333%',
        8: '66.666%',
        9: '75%',
        10: '83.333%',
        11: '91.666%',
        12: '100%',
        'full': '100%',
        'half': '50%',
        'third': '33.333%',
    }

    if breakpoint == 'sm':
        return {'default': 12, **spans}
    elif breakpoint == 'md':
        return {'default': 6, **spans}
    elif breakpoint == 'lg':
        return {'default': 4, **spans}
    elif breakpoint == 'xl':
        return {'default': 3, **spans}

    return spans


def get_nav_styles():
    """Return navigation styles.

    Returns:
        dict: Navigation header styles.
    """
    return {
        'height': '64px',
        'h-16': '4rem',
        'background': '#FFFFFF',
        'bg': '#FFFFFF',
        'position': 'sticky',
        'top': '0',
        'zIndex': '50',
        'z-index': 50,
        'borderBottom': '1px solid #E7E5E4',
        'padding': '0 1rem',
    }


def get_mobile_menu_styles():
    """Return mobile menu styles.

    Returns:
        dict: Mobile menu with hamburger, drawer, overlay.
    """
    return {
        'button': {
            'width': '44px',
            'height': '44px',
            'padding': '0.5rem',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
        },
        'hamburger': {
            'width': '24px',
            'height': '2px',
            'background': '#44403C',
        },
        'drawer': {
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '280px',
            'height': '100vh',
            'background': '#FFFFFF',
            'zIndex': '100',
            'padding': '1rem',
        },
        'menu': {
            'listStyle': 'none',
            'padding': '0',
            'margin': '0',
        },
        'menuItem': {
            'padding': '0.75rem 1rem',
            'py-3': '0.75rem',
            'minHeight': '48px',
            'touchAction': 'manipulation',
        },
        'overlay': {
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'right': '0',
            'bottom': '0',
            'background': 'rgba(0, 0, 0, 0.5)',
            'zIndex': '90',
        },
        'backdrop': {
            'background': 'rgba(0, 0, 0, 0.5)',
        },
    }


def get_sidebar_styles():
    """Return sidebar navigation styles.

    Returns:
        dict: Sidebar with width, collapse states.
    """
    return {
        'width': '256px',
        'w-64': '16rem',
        'background': '#FAFAF9',
        'expanded': {
            'width': '256px',
        },
        'collapsed': {
            'width': '64px',
        },
        'hidden': {
            'display': 'none',
        },
        'lg:block': {
            'display': 'block',
        },
        'md:hidden': {
            'display': 'none',
        },
    }


def get_page_layout(layout_type):
    """Return page layout definition.

    Args:
        layout_type: Type of layout ('default', 'with-sidebar').

    Returns:
        dict: Page layout configuration.
    """
    base = {
        'header': {
            'gridArea': 'header',
            'position': 'sticky',
            'top': '0',
            'zIndex': '10',
        },
        'main': {
            'gridArea': 'main',
            'minHeight': '100vh',
            'height': '100%',
        },
        'content': {
            'padding': '1rem',
            'maxWidth': '1280px',
            'margin': '0 auto',
        },
        'footer': {
            'gridArea': 'footer',
        },
    }

    if layout_type == 'with-sidebar':
        return {
            **base,
            'sidebar': {
                'gridArea': 'sidebar',
                'width': '256px',
                'position': 'sticky',
                'top': '64px',
                'height': 'calc(100vh - 64px)',
            },
            'grid': {
                'display': 'grid',
                'gridTemplateAreas': '"header header" "sidebar main" "footer footer"',
                'gridTemplateColumns': '256px 1fr',
                'minHeight': '100vh',
            },
        }

    return {
        **base,
        'grid': {
            'display': 'grid',
            'gridTemplateAreas': '"header" "main" "footer"',
            'gridTemplateRows': 'auto 1fr auto',
            'minHeight': '100vh',
        },
    }


def get_sermon_editor_layout():
    """Return sermon editor layout.

    Returns:
        dict: Editor layout with main area and panel.
    """
    return {
        'container': {
            'display': 'grid',
            'gridTemplateColumns': '1fr 320px',
            'gap': '1rem',
            'minHeight': 'calc(100vh - 64px)',
            'responsive': True,
            'lg:gridTemplateColumns': '1fr 320px',
            'md:gridTemplateColumns': '1fr',
        },
        'editor': {
            'minWidth': '400px',
            'width': '100%',
            'padding': '2rem',
            'background': '#FFFFFF',
        },
        'main': {
            'flex': '1',
            'minWidth': '0',
        },
        'panel': {
            'width': '320px',
            'background': '#FAFAF9',
            'borderLeft': '1px solid #E7E5E4',
            'padding': '1rem',
            'overflowY': 'auto',
        },
        'aside': {
            'width': '320px',
        },
        'sidebar': {
            'width': '320px',
        },
    }


def get_dashboard_layout():
    """Return dashboard grid layout.

    Returns:
        dict: Dashboard with responsive grid.
    """
    return {
        'container': {
            'display': 'grid',
            'gap': '1.5rem',
            'padding': '1.5rem',
        },
        'grid': {
            'display': 'grid',
            'gridTemplateColumns': 'repeat(auto-fit, minmax(300px, 1fr))',
            'gap': '1.5rem',
        },
        'sm': {
            'gridTemplateColumns': '1fr',
        },
        'md': {
            'gridTemplateColumns': 'repeat(2, 1fr)',
        },
        'lg': {
            'gridTemplateColumns': 'repeat(3, 1fr)',
        },
        'xl': {
            'gridTemplateColumns': 'repeat(4, 1fr)',
        },
        'card': {
            'background': '#FFFFFF',
            'borderRadius': '0.5rem',
            'padding': '1.5rem',
            'boxShadow': '0 1px 3px 0 rgb(0 0 0 / 0.1)',
        },
        'widget': {
            'gridColumn': 'span 1',
        },
        'item': {
            'display': 'flex',
            'flexDirection': 'column',
        },
    }
