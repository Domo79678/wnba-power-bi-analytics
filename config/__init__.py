"""Configuration package for the WNBA analytics project.

Keeping configuration in its own package gives every pipeline step one
consistent place to find paths and environment-based settings.
"""

from config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
