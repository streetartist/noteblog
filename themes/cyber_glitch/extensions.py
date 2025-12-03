"""Cyber Glitch theme extensions and dynamic pages."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _sanitize_slug(raw_value: Optional[str]) -> str:
    slug = (raw_value or 'about').strip().strip('/')
    return slug or 'about'


def get_custom_pages(theme=None, **_kwargs) -> List[Dict[str, Any]]:
    """Expose a dedicated about page that follows the configured slug."""
    slug = 'about'
    if theme is not None:
        try:
            theme_config = theme.get_config() or {}
        except Exception:
            theme_config = {}
        slug = _sanitize_slug(theme_config.get('about_page_slug'))
    route = f"/{slug}" if slug.startswith('/') is False else slug
    return [
        {
            'name': 'cyber_glitch_about',
            'endpoint': 'cyber_glitch.about',
            'route': route,
            'template': 'about.html',
            'methods': ['GET'],
        }
    ]
