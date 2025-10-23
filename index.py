"""
Root entry point for KhmerLink FastAPI app.

This file imports the FastAPI `app` instance from the api/fixed_index module so that Vercel's Python runtime can detect it as the entrypoint.
Vercel's Python runtime can detect it as the entrypoint.
"""

from api.fixed_index import app
