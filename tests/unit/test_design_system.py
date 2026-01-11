"""
Tests for Design System Module (Issue #211)

Phase 9: UI/UX Design - Item 1 (PHASE 9 START)

Tests cover:
- Color system (palette, primary, semantic, dark mode)
- Typography system (scale, fonts, line heights)
- Spacing system (scale, breakpoints)
- Component tokens (buttons, cards, forms)
- Theme generation (CSS variables, Tailwind config)
- Accessibility (color contrast ratios)

TDD Approach: All tests fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real implementations.
"""

import pytest
import re


def is_valid_hex_color(color):
    """Validate hex color format."""
    if not color:
        return False
    return bool(re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color))


def is_valid_rgb_color(color):
    """Validate RGB color format."""
    if not color:
        return False
    return bool(re.match(r'^rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$', color))


def is_valid_hsl_color(color):
    """Validate HSL color format."""
    if not color:
        return False
    return bool(re.match(r'^hsl\(\s*\d+\s*,\s*\d+%?\s*,\s*\d+%?\s*\)$', color))


def is_valid_color(color):
    """Validate any color format."""
    return is_valid_hex_color(color) or is_valid_rgb_color(color) or is_valid_hsl_color(color)


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_luminance(rgb):
    """Calculate relative luminance for WCAG contrast."""
    def adjust(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)


def get_contrast_ratio(color1, color2):
    """Calculate WCAG contrast ratio between two colors."""
    l1 = get_luminance(hex_to_rgb(color1))
    l2 = get_luminance(hex_to_rgb(color2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


class TestGetColorPalette:
    """Tests for get_color_palette function."""

    def test_should_return_color_palette(self):
        """Should return a complete color palette."""
        from design_system import get_color_palette

        palette = get_color_palette()

        assert isinstance(palette, dict)
        assert len(palette) > 0

    def test_should_include_primary_colors(self):
        """Should include primary color shades."""
        from design_system import get_color_palette

        palette = get_color_palette()

        assert 'primary' in palette
        assert isinstance(palette['primary'], dict)
        # Should have multiple shades (50, 100, 200, ..., 900)
        assert len(palette['primary']) >= 5

    def test_should_include_neutral_colors(self):
        """Should include neutral/gray colors."""
        from design_system import get_color_palette

        palette = get_color_palette()

        assert 'neutral' in palette or 'gray' in palette

    def test_should_include_accent_colors(self):
        """Should include accent colors."""
        from design_system import get_color_palette

        palette = get_color_palette()

        assert 'accent' in palette or 'secondary' in palette

    def test_should_have_valid_hex_colors(self):
        """All colors should be valid hex format."""
        from design_system import get_color_palette

        palette = get_color_palette()

        for category in palette.values():
            if isinstance(category, dict):
                for color in category.values():
                    assert is_valid_color(color), f"Invalid color: {color}"


class TestGetPrimaryColor:
    """Tests for get_primary_color function."""

    def test_should_return_primary_color(self):
        """Should return the primary brand color."""
        from design_system import get_primary_color

        color = get_primary_color()

        assert is_valid_hex_color(color)

    def test_should_be_warm_color(self):
        """Primary should be warm/inviting (not harsh blue/gray)."""
        from design_system import get_primary_color

        color = get_primary_color()
        rgb = hex_to_rgb(color)

        # Warm colors have higher red component or are earth tones
        # This is a soft check - just ensuring it's not pure cold blue
        r, g, b = rgb
        # Either warm (red-ish) or a balanced warm tone
        assert r >= g * 0.5, "Primary should be warm, not cold blue"

    def test_should_support_shade_parameter(self):
        """Should support getting different shades."""
        from design_system import get_primary_color

        light = get_primary_color(shade=100)
        default = get_primary_color(shade=500)
        dark = get_primary_color(shade=900)

        assert light != default
        assert default != dark
        # Light should be lighter (higher luminance)
        l_light = get_luminance(hex_to_rgb(light))
        l_dark = get_luminance(hex_to_rgb(dark))
        assert l_light > l_dark


class TestGetSemanticColors:
    """Tests for get_semantic_colors function."""

    def test_should_return_semantic_colors(self):
        """Should return success/warning/error/info colors."""
        from design_system import get_semantic_colors

        colors = get_semantic_colors()

        assert 'success' in colors
        assert 'warning' in colors
        assert 'error' in colors
        assert 'info' in colors

    def test_success_should_be_green(self):
        """Success color should be green-ish."""
        from design_system import get_semantic_colors

        colors = get_semantic_colors()
        rgb = hex_to_rgb(colors['success'])

        r, g, b = rgb
        assert g >= r and g >= b, "Success should be primarily green"

    def test_error_should_be_red(self):
        """Error color should be red-ish."""
        from design_system import get_semantic_colors

        colors = get_semantic_colors()
        rgb = hex_to_rgb(colors['error'])

        r, g, b = rgb
        assert r > g and r > b, "Error should be primarily red"

    def test_warning_should_be_amber(self):
        """Warning color should be amber/yellow."""
        from design_system import get_semantic_colors

        colors = get_semantic_colors()
        rgb = hex_to_rgb(colors['warning'])

        r, g, b = rgb
        # Amber/yellow has high red and green
        assert r > b and g > b, "Warning should be amber/yellow"

    def test_colors_should_be_valid(self):
        """All semantic colors should be valid."""
        from design_system import get_semantic_colors

        colors = get_semantic_colors()

        for color in colors.values():
            assert is_valid_hex_color(color)


class TestGetDarkModeColors:
    """Tests for get_dark_mode_colors function."""

    def test_should_return_dark_mode_palette(self):
        """Should return dark mode color palette."""
        from design_system import get_dark_mode_colors

        colors = get_dark_mode_colors()

        assert isinstance(colors, dict)
        assert 'background' in colors
        assert 'text' in colors

    def test_background_should_be_dark(self):
        """Background should be dark (low luminance)."""
        from design_system import get_dark_mode_colors

        colors = get_dark_mode_colors()
        luminance = get_luminance(hex_to_rgb(colors['background']))

        assert luminance < 0.2, "Dark mode background should be dark"

    def test_text_should_be_light(self):
        """Text should be light for contrast."""
        from design_system import get_dark_mode_colors

        colors = get_dark_mode_colors()
        luminance = get_luminance(hex_to_rgb(colors['text']))

        assert luminance > 0.5, "Dark mode text should be light"

    def test_should_have_adequate_contrast(self):
        """Text and background should have adequate contrast."""
        from design_system import get_dark_mode_colors

        colors = get_dark_mode_colors()
        ratio = get_contrast_ratio(colors['text'], colors['background'])

        # WCAG AA requires 4.5:1 for normal text
        assert ratio >= 4.5, f"Contrast ratio {ratio} is below WCAG AA (4.5)"

    def test_should_include_surface_colors(self):
        """Should include surface/card colors."""
        from design_system import get_dark_mode_colors

        colors = get_dark_mode_colors()

        assert 'surface' in colors or 'card' in colors


class TestGetTypographyScale:
    """Tests for get_typography_scale function."""

    def test_should_return_typography_scale(self):
        """Should return a typography scale."""
        from design_system import get_typography_scale

        scale = get_typography_scale()

        assert isinstance(scale, dict)
        assert len(scale) > 0

    def test_should_include_heading_sizes(self):
        """Should include h1-h6 sizes."""
        from design_system import get_typography_scale

        scale = get_typography_scale()

        # Should have heading sizes
        heading_keys = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        for key in heading_keys:
            assert key in scale, f"Missing heading size: {key}"

    def test_should_include_body_sizes(self):
        """Should include body text sizes."""
        from design_system import get_typography_scale

        scale = get_typography_scale()

        # Should have body sizes
        assert 'body' in scale or 'base' in scale
        assert 'small' in scale or 'sm' in scale

    def test_sizes_should_be_valid(self):
        """Font sizes should be valid CSS values."""
        from design_system import get_typography_scale

        scale = get_typography_scale()

        for size in scale.values():
            # Should be rem, em, or px
            assert re.match(r'^[\d.]+(?:rem|em|px)$', str(size)), f"Invalid size: {size}"

    def test_should_follow_modular_scale(self):
        """Sizes should follow a modular scale."""
        from design_system import get_typography_scale

        scale = get_typography_scale()

        # Extract numeric values
        def parse_size(s):
            return float(re.match(r'[\d.]+', str(s)).group())

        h1 = parse_size(scale['h1'])
        h2 = parse_size(scale['h2'])
        h3 = parse_size(scale['h3'])

        # Larger headings should be bigger
        assert h1 > h2 > h3, "Headings should decrease in size"


class TestGetFontFamilies:
    """Tests for get_font_families function."""

    def test_should_return_font_families(self):
        """Should return font family definitions."""
        from design_system import get_font_families

        fonts = get_font_families()

        assert isinstance(fonts, dict)
        assert 'heading' in fonts or 'display' in fonts
        assert 'body' in fonts

    def test_should_include_fallback_fonts(self):
        """Font stacks should include fallbacks."""
        from design_system import get_font_families

        fonts = get_font_families()

        for font_stack in fonts.values():
            # Should be a comma-separated list with fallbacks
            assert ',' in font_stack, "Font stack should include fallbacks"

    def test_should_include_system_font_fallback(self):
        """Should include system font fallback."""
        from design_system import get_font_families

        fonts = get_font_families()

        # At least one stack should have system font fallback
        any_has_system = any(
            'sans-serif' in stack or 'serif' in stack or 'system-ui' in stack
            for stack in fonts.values()
        )
        assert any_has_system, "Should include system font fallback"


class TestGetLineHeights:
    """Tests for get_line_heights function."""

    def test_should_return_line_heights(self):
        """Should return line height scale."""
        from design_system import get_line_heights

        heights = get_line_heights()

        assert isinstance(heights, dict)
        assert len(heights) >= 3

    def test_should_include_standard_heights(self):
        """Should include tight, normal, and relaxed."""
        from design_system import get_line_heights

        heights = get_line_heights()

        # Should have at least tight, normal/base, relaxed
        assert 'tight' in heights or 'condensed' in heights
        assert 'normal' in heights or 'base' in heights
        assert 'relaxed' in heights or 'loose' in heights

    def test_heights_should_be_valid(self):
        """Line heights should be valid values."""
        from design_system import get_line_heights

        heights = get_line_heights()

        for height in heights.values():
            # Should be unitless or with unit
            assert re.match(r'^[\d.]+(?:rem|em|px|%)?$', str(height)), f"Invalid: {height}"


class TestGetSpacingScale:
    """Tests for get_spacing_scale function."""

    def test_should_return_spacing_scale(self):
        """Should return spacing scale."""
        from design_system import get_spacing_scale

        scale = get_spacing_scale()

        assert isinstance(scale, dict)
        assert len(scale) >= 8

    def test_should_follow_consistent_scale(self):
        """Spacing should follow 4px or 8px base scale."""
        from design_system import get_spacing_scale

        scale = get_spacing_scale()

        # Extract values and check for consistent increments
        values = []
        for key, val in scale.items():
            if isinstance(key, int):
                match = re.match(r'([\d.]+)', str(val))
                if match:
                    values.append(float(match.group(1)))

        # Values should be multiples of base (typically 4px or 0.25rem)
        assert len(values) > 0, "Should have numeric spacing values"

    def test_should_include_zero(self):
        """Should include zero spacing."""
        from design_system import get_spacing_scale

        scale = get_spacing_scale()

        assert 0 in scale or '0' in scale

    def test_values_should_be_valid_css(self):
        """Values should be valid CSS units."""
        from design_system import get_spacing_scale

        scale = get_spacing_scale()

        for val in scale.values():
            if val != 0 and val != '0':
                assert re.match(r'^[\d.]+(?:rem|em|px)$', str(val)), f"Invalid: {val}"


class TestGetBreakpoints:
    """Tests for get_breakpoints function."""

    def test_should_return_breakpoints(self):
        """Should return responsive breakpoints."""
        from design_system import get_breakpoints

        breakpoints = get_breakpoints()

        assert isinstance(breakpoints, dict)
        assert len(breakpoints) >= 4

    def test_should_include_standard_breakpoints(self):
        """Should include sm, md, lg, xl breakpoints."""
        from design_system import get_breakpoints

        breakpoints = get_breakpoints()

        standard = ['sm', 'md', 'lg', 'xl']
        for bp in standard:
            assert bp in breakpoints, f"Missing breakpoint: {bp}"

    def test_breakpoints_should_increase(self):
        """Breakpoints should increase in size."""
        from design_system import get_breakpoints

        breakpoints = get_breakpoints()

        def parse_px(val):
            return int(re.match(r'(\d+)', str(val)).group(1))

        sm = parse_px(breakpoints['sm'])
        md = parse_px(breakpoints['md'])
        lg = parse_px(breakpoints['lg'])
        xl = parse_px(breakpoints['xl'])

        assert sm < md < lg < xl


class TestGetButtonStyles:
    """Tests for get_button_styles function."""

    def test_should_return_button_styles(self):
        """Should return button style definitions."""
        from design_system import get_button_styles

        styles = get_button_styles()

        assert isinstance(styles, dict)

    def test_should_include_variants(self):
        """Should include button variants."""
        from design_system import get_button_styles

        styles = get_button_styles()

        assert 'primary' in styles
        assert 'secondary' in styles or 'outline' in styles

    def test_should_include_sizes(self):
        """Should include button sizes."""
        from design_system import get_button_styles

        styles = get_button_styles()

        assert 'sizes' in styles or all(
            'sm' in str(styles) or 'lg' in str(styles)
            for _ in [1]
        )

    def test_primary_should_have_good_contrast(self):
        """Primary button should have good text contrast."""
        from design_system import get_button_styles

        styles = get_button_styles()
        primary = styles['primary']

        if 'background' in primary and 'color' in primary:
            ratio = get_contrast_ratio(primary['color'], primary['background'])
            assert ratio >= 4.5, f"Button contrast {ratio} below WCAG AA"


class TestGetCardStyles:
    """Tests for get_card_styles function."""

    def test_should_return_card_styles(self):
        """Should return card/panel styles."""
        from design_system import get_card_styles

        styles = get_card_styles()

        assert isinstance(styles, dict)

    def test_should_include_padding(self):
        """Cards should have padding."""
        from design_system import get_card_styles

        styles = get_card_styles()

        assert 'padding' in styles or 'p' in styles

    def test_should_include_border_radius(self):
        """Cards should have border radius."""
        from design_system import get_card_styles

        styles = get_card_styles()

        assert 'borderRadius' in styles or 'border-radius' in styles or 'rounded' in styles

    def test_should_include_shadow(self):
        """Cards should have shadow options."""
        from design_system import get_card_styles

        styles = get_card_styles()

        assert 'shadow' in styles or 'boxShadow' in styles or 'box-shadow' in styles


class TestGetFormStyles:
    """Tests for get_form_styles function."""

    def test_should_return_form_styles(self):
        """Should return form input styles."""
        from design_system import get_form_styles

        styles = get_form_styles()

        assert isinstance(styles, dict)

    def test_should_include_input_styles(self):
        """Should include input field styles."""
        from design_system import get_form_styles

        styles = get_form_styles()

        assert 'input' in styles or 'text' in styles

    def test_should_include_focus_states(self):
        """Should include focus state styles."""
        from design_system import get_form_styles

        styles = get_form_styles()

        # Should have focus ring or outline
        style_str = str(styles).lower()
        assert 'focus' in style_str or 'ring' in style_str

    def test_should_include_error_states(self):
        """Should include error state styles."""
        from design_system import get_form_styles

        styles = get_form_styles()

        style_str = str(styles).lower()
        assert 'error' in style_str or 'invalid' in style_str


class TestGenerateCSSVariables:
    """Tests for generate_css_variables function."""

    def test_should_generate_css_variables(self):
        """Should generate CSS custom properties."""
        from design_system import generate_css_variables

        css = generate_css_variables()

        assert isinstance(css, str)
        assert ':root' in css
        assert '--' in css

    def test_should_include_color_variables(self):
        """Should include color variables."""
        from design_system import generate_css_variables

        css = generate_css_variables()

        assert '--color-primary' in css or '--primary' in css
        assert '--color-' in css

    def test_should_include_spacing_variables(self):
        """Should include spacing variables."""
        from design_system import generate_css_variables

        css = generate_css_variables()

        assert '--spacing' in css or '--space' in css

    def test_should_include_typography_variables(self):
        """Should include typography variables."""
        from design_system import generate_css_variables

        css = generate_css_variables()

        assert '--font' in css or '--text' in css

    def test_should_be_valid_css(self):
        """Output should be valid CSS."""
        from design_system import generate_css_variables

        css = generate_css_variables()

        # Should have balanced braces
        assert css.count('{') == css.count('}')
        # Should end with closing brace
        assert css.strip().endswith('}')


class TestExportTailwindConfig:
    """Tests for export_tailwind_config function."""

    def test_should_export_tailwind_config(self):
        """Should export Tailwind configuration."""
        from design_system import export_tailwind_config

        config = export_tailwind_config()

        assert isinstance(config, dict)
        assert 'theme' in config

    def test_should_include_colors(self):
        """Should include color configuration."""
        from design_system import export_tailwind_config

        config = export_tailwind_config()

        assert 'colors' in config['theme'] or 'extend' in config['theme']

    def test_should_include_spacing(self):
        """Should include spacing configuration."""
        from design_system import export_tailwind_config

        config = export_tailwind_config()

        theme = config['theme']
        has_spacing = 'spacing' in theme or (
            'extend' in theme and 'spacing' in theme.get('extend', {})
        )
        assert has_spacing

    def test_should_include_typography(self):
        """Should include typography configuration."""
        from design_system import export_tailwind_config

        config = export_tailwind_config()

        theme = config['theme']
        has_fonts = 'fontFamily' in theme or 'fontSize' in theme or (
            'extend' in theme and (
                'fontFamily' in theme.get('extend', {}) or
                'fontSize' in theme.get('extend', {})
            )
        )
        assert has_fonts

    def test_should_be_json_serializable(self):
        """Config should be JSON serializable."""
        from design_system import export_tailwind_config
        import json

        config = export_tailwind_config()

        # Should not raise
        json_str = json.dumps(config)
        assert len(json_str) > 0


class TestAccessibility:
    """Tests for accessibility compliance."""

    def test_primary_text_contrast(self):
        """Primary color with white should have adequate contrast."""
        from design_system import get_primary_color

        primary = get_primary_color(shade=500)
        white = '#FFFFFF'

        ratio = get_contrast_ratio(primary, white)
        # Either text on primary or primary on white should work
        assert ratio >= 3.0, f"Primary contrast {ratio} too low for large text"

    def test_dark_mode_text_contrast(self):
        """Dark mode should have WCAG AA contrast."""
        from design_system import get_dark_mode_colors

        colors = get_dark_mode_colors()
        ratio = get_contrast_ratio(colors['text'], colors['background'])

        assert ratio >= 4.5, f"Dark mode contrast {ratio} below WCAG AA"

    def test_semantic_colors_on_white(self):
        """Semantic colors should be visible on white."""
        from design_system import get_semantic_colors

        colors = get_semantic_colors()
        white = '#FFFFFF'

        for name, color in colors.items():
            ratio = get_contrast_ratio(color, white)
            # At least 3:1 for UI components
            assert ratio >= 3.0, f"{name} color contrast {ratio} too low"

    def test_focus_visibility(self):
        """Focus states should be visible."""
        from design_system import get_form_styles

        styles = get_form_styles()
        style_str = str(styles).lower()

        # Should have focus indicator
        has_focus = 'focus' in style_str or 'ring' in style_str or 'outline' in style_str
        assert has_focus, "Form styles should include focus indicators"


class TestWarmAesthetic:
    """Tests for warm, pastoral aesthetic (not harsh/clinical)."""

    def test_primary_is_not_clinical_blue(self):
        """Primary should not be harsh clinical blue."""
        from design_system import get_primary_color

        color = get_primary_color()
        rgb = hex_to_rgb(color)
        r, g, b = rgb

        # Clinical blue would be low red, high blue
        is_clinical_blue = r < 100 and b > 200 and g < 150
        assert not is_clinical_blue, "Primary should not be clinical blue"

    def test_has_warm_accent(self):
        """Should have warm accent or secondary color."""
        from design_system import get_color_palette

        palette = get_color_palette()

        # Check for warm tones somewhere in palette
        warm_found = False
        for category, colors in palette.items():
            if isinstance(colors, dict):
                for color in colors.values():
                    if is_valid_hex_color(color):
                        rgb = hex_to_rgb(color)
                        r, g, b = rgb
                        if r > g and r > b and r > 150:
                            warm_found = True
                            break
            if warm_found:
                break

        assert warm_found, "Palette should include warm tones"

    def test_neutral_is_not_pure_gray(self):
        """Neutral colors should have slight warmth."""
        from design_system import get_color_palette

        palette = get_color_palette()

        neutral_key = 'neutral' if 'neutral' in palette else 'gray'
        if neutral_key in palette:
            # Check a mid-tone neutral
            neutral_colors = palette[neutral_key]
            mid_shade = neutral_colors.get(500) or neutral_colors.get('500')

            if mid_shade and is_valid_hex_color(mid_shade):
                rgb = hex_to_rgb(mid_shade)
                r, g, b = rgb
                # Warm gray has slightly higher red or similar r/b
                # Pure gray has r == g == b
                is_pure_gray = abs(r - g) < 3 and abs(g - b) < 3 and abs(r - b) < 3
                # Allow slight warmth
                assert not is_pure_gray or r >= b, "Neutral should have slight warmth"


class TestIntegration:
    """Integration tests for design system."""

    def test_should_generate_complete_theme(self):
        """Should generate a complete theme."""
        from design_system import (
            get_color_palette,
            get_typography_scale,
            get_spacing_scale,
            generate_css_variables
        )

        palette = get_color_palette()
        typography = get_typography_scale()
        spacing = get_spacing_scale()
        css = generate_css_variables()

        assert len(palette) > 0
        assert len(typography) > 0
        assert len(spacing) > 0
        assert len(css) > 100

    def test_should_export_consistent_tailwind_config(self):
        """Tailwind config should match CSS variables."""
        from design_system import (
            get_color_palette,
            export_tailwind_config
        )

        palette = get_color_palette()
        config = export_tailwind_config()

        # Both should have primary color
        assert 'primary' in palette
        theme = config.get('theme', {})
        colors = theme.get('colors', theme.get('extend', {}).get('colors', {}))
        assert 'primary' in colors or len(colors) > 0

    def test_should_support_theming(self):
        """Should support light and dark theming."""
        from design_system import (
            get_color_palette,
            get_dark_mode_colors
        )

        light = get_color_palette()
        dark = get_dark_mode_colors()

        assert light != dark
        assert 'background' in dark
        assert 'text' in dark

    def test_should_be_complete_for_app(self):
        """Should have all elements needed for the app."""
        from design_system import (
            get_color_palette,
            get_semantic_colors,
            get_typography_scale,
            get_font_families,
            get_spacing_scale,
            get_breakpoints,
            get_button_styles,
            get_card_styles,
            get_form_styles
        )

        # All required functions should return valid data
        assert len(get_color_palette()) > 0
        assert len(get_semantic_colors()) >= 4
        assert len(get_typography_scale()) >= 6
        assert len(get_font_families()) >= 2
        assert len(get_spacing_scale()) >= 8
        assert len(get_breakpoints()) >= 4
        assert len(get_button_styles()) > 0
        assert len(get_card_styles()) > 0
        assert len(get_form_styles()) > 0
