"""
Compatibilità retroattiva.

La GUI desktop principale vive in `src/gui/app.py`.
Questo modulo rimane come wrapper per eventuali import vecchi (es. `logic.app`).
"""

from gui.app import GUI, start_application

__all__ = ["GUI", "start_application"]

