"""
Root entry point for KhmerLink FastAPI app.

This file imports the FastAPI `app` instance from the api/index.py module so that
Vercel's Python runtime can detect it as the entrypoint.
"""

from api.index import app
