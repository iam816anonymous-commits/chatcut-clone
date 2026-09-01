"""FFmpeg Filter String and Path Escaping Utilities."""

import re


def escape_drawtext_str(text: str) -> str:
    """Escape text content strings for FFmpeg drawtext filter syntax.

    FFmpeg filtergraph strings require escaping for:
    - Backslash '\\' -> '\\\\'
    - Single quote '\'' -> `'\\''` or `'\\''`
    - Colon ':' -> '\\:'
    - Percent '%' -> '\\%'
    - Semicolon ';' -> '\\;'
    """
    if not text:
        return ""

    # First, double all backslashes
    escaped = text.replace("\\", "\\\\")

    # Escape colons
    escaped = escaped.replace(":", "\\:")

    # Escape percent signs
    escaped = escaped.replace("%", "\\%")

    # Escape semicolons
    escaped = escaped.replace(";", "\\;")

    # Escape single quotes
    escaped = escaped.replace("'", "'\\\\''")

    return escaped


def escape_filter_path(path_str: str) -> str:
    """Escape file path string for FFmpeg filter arguments (e.g. fontfile path)."""
    if not path_str:
        return ""

    escaped = path_str.replace("\\", "/")
    escaped = escaped.replace(":", "\\:")
    escaped = escaped.replace("'", "'\\\\''")
    return escaped
