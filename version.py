"""Single source of truth for the application version.

Semantic Versioning (MAJOR.MINOR.PATCH)
Increment guideline:
 - MAJOR: Backwards incompatible config or UI changes
 - MINOR: Backwards compatible feature additions / improvements
 - PATCH: Backwards compatible bug fixes / small tweaks

Recent notable changes:
 - 2.0.0: Major OCR engine revamp (multi-variant preprocessing, token fast-path), version centralization.

Use bump_version.py to update this file instead of manual edits when possible.
"""

__version__ = "2.0.0"

def get_version() -> str:
    """Return current application version."""
    return __version__
