"""Design System Module (Issue #211)

Phase 9: UI/UX Design - Item 1

Provides design tokens for:
- Color system (palette, primary, semantic, dark mode)
- Typography system (scale, fonts, line heights)
- Spacing system (scale, breakpoints)
- Component tokens (buttons, cards, forms)
- Theme generation (CSS variables, Tailwind config)
"""


def get_color_palette():
    """Return complete color palette.

    Returns:
        dict: Color palette with primary, neutral, and accent shades.
    """
    return {
        'primary': {
            50: '#FFEDD5',
            100: '#FED7AA',
            200: '#FDBA74',
            300: '#FB923C',
            400: '#EA580C',
            500: '#C2410C',
            600: '#9A3412',
            700: '#7C2D12',
            800: '#5C1D0C',
            900: '#3D1106',
        },
        'neutral': {
            50: '#FAFAF9',
            100: '#F5F5F4',
            200: '#E7E5E4',
            300: '#D6D3D1',
            400: '#A8A29E',
            500: '#78716C',
            600: '#57534E',
            700: '#44403C',
            800: '#292524',
            900: '#1C1917',
        },
        'accent': {
            50: '#FDF4FF',
            100: '#FAE8FF',
            200: '#F5D0FE',
            300: '#F0ABFC',
            400: '#E879F9',
            500: '#D946EF',
            600: '#C026D3',
            700: '#A21CAF',
            800: '#86198F',
            900: '#701A75',
        },
    }


def get_primary_color(shade=500):
    """Return primary brand color.

    Args:
        shade: Color shade (50-900). Default 500.

    Returns:
        str: Hex color value.
    """
    palette = get_color_palette()
    return palette['primary'].get(shade, palette['primary'][500])


def get_semantic_colors():
    """Return semantic colors for UI feedback.

    Returns:
        dict: Success, warning, error, info colors.
    """
    return {
        'success': '#15803D',
        'warning': '#B45309',
        'error': '#DC2626',
        'info': '#1D4ED8',
    }


def get_dark_mode_colors():
    """Return dark mode color palette.

    Returns:
        dict: Dark mode background, text, and surface colors.
    """
    return {
        'background': '#1C1917',
        'text': '#FAFAF9',
        'surface': '#292524',
    }


def get_typography_scale():
    """Return typography scale.

    Returns:
        dict: Font sizes for headings and body text.
    """
    return {
        'h1': '2.25rem',
        'h2': '1.875rem',
        'h3': '1.5rem',
        'h4': '1.25rem',
        'h5': '1.125rem',
        'h6': '1rem',
        'body': '1rem',
        'small': '0.875rem',
    }


def get_font_families():
    """Return font family stacks.

    Returns:
        dict: Font stacks for headings and body text.
    """
    return {
        'heading': 'Merriweather, Georgia, serif',
        'body': 'Inter, system-ui, sans-serif',
    }


def get_line_heights():
    """Return line height scale.

    Returns:
        dict: Line heights for different text densities.
    """
    return {
        'tight': '1.25',
        'normal': '1.5',
        'relaxed': '1.75',
    }


def get_spacing_scale():
    """Return spacing scale.

    Returns:
        dict: Spacing values based on 4px base.
    """
    return {
        0: '0',
        1: '0.25rem',
        2: '0.5rem',
        3: '0.75rem',
        4: '1rem',
        5: '1.25rem',
        6: '1.5rem',
        8: '2rem',
        10: '2.5rem',
        12: '3rem',
        16: '4rem',
    }


def get_breakpoints():
    """Return responsive breakpoints.

    Returns:
        dict: Breakpoint values for responsive design.
    """
    return {
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
    }


def get_button_styles():
    """Return button style definitions.

    Returns:
        dict: Button variants and sizes.
    """
    return {
        'primary': {
            'background': '#9A3412',
            'color': '#FFFFFF',
            'border': 'none',
            'borderRadius': '0.375rem',
        },
        'secondary': {
            'background': '#FFFFFF',
            'color': '#44403C',
            'border': '1px solid #D6D3D1',
            'borderRadius': '0.375rem',
        },
        'sizes': {
            'sm': {'padding': '0.5rem 1rem', 'fontSize': '0.875rem'},
            'md': {'padding': '0.625rem 1.25rem', 'fontSize': '1rem'},
            'lg': {'padding': '0.75rem 1.5rem', 'fontSize': '1.125rem'},
        },
    }


def get_card_styles():
    """Return card style definitions.

    Returns:
        dict: Card padding, radius, and shadow.
    """
    return {
        'padding': '1.5rem',
        'borderRadius': '0.5rem',
        'shadow': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    }


def get_form_styles():
    """Return form input styles.

    Returns:
        dict: Input, focus, and error states.
    """
    return {
        'input': {
            'padding': '0.625rem 0.75rem',
            'borderRadius': '0.375rem',
            'border': '1px solid #D6D3D1',
            'fontSize': '1rem',
        },
        'focus': {
            'outline': 'none',
            'ring': '2px solid #F97316',
            'ringOffset': '2px',
        },
        'error': {
            'border': '1px solid #EF4444',
            'ring': '2px solid #EF4444',
        },
    }


def generate_css_variables():
    """Generate CSS custom properties.

    Returns:
        str: CSS with :root custom properties.
    """
    lines = [':root {']

    palette = get_color_palette()
    for category, shades in palette.items():
        for shade, color in shades.items():
            lines.append(f'  --color-{category}-{shade}: {color};')

    semantic = get_semantic_colors()
    for name, color in semantic.items():
        lines.append(f'  --color-{name}: {color};')

    typography = get_typography_scale()
    for name, size in typography.items():
        lines.append(f'  --font-size-{name}: {size};')

    fonts = get_font_families()
    for name, stack in fonts.items():
        lines.append(f'  --font-{name}: {stack};')

    spacing = get_spacing_scale()
    for key, value in spacing.items():
        lines.append(f'  --spacing-{key}: {value};')

    lines.append('}')

    return '\n'.join(lines)


def export_tailwind_config():
    """Export Tailwind configuration.

    Returns:
        dict: Tailwind config with theme settings.
    """
    palette = get_color_palette()
    spacing = get_spacing_scale()
    typography = get_typography_scale()
    fonts = get_font_families()
    breakpoints = get_breakpoints()

    return {
        'theme': {
            'extend': {
                'colors': {
                    'primary': palette['primary'],
                    'neutral': palette['neutral'],
                    'accent': palette['accent'],
                },
                'spacing': {str(k): v for k, v in spacing.items()},
                'fontSize': typography,
                'fontFamily': fonts,
            },
            'screens': breakpoints,
        },
    }
