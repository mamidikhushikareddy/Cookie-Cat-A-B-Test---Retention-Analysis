"""Cookie Cat analytical core. Importable without the web app, MCP server or agent."""
from .legacy import *  # noqa: F401,F403  (backwards-compatible exports for app.py / api / old tests)
from .legacy import load_and_validate, analyze  # noqa: F401
