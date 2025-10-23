"""
KhmerLink – a simple Khmer‑language URL shortener built with FastAPI.

This service lets users choose a Khmer word (slug) and map it to a long URL.
When someone visits https://yourdomain.com/<slug>, they are redirected to the
corresponding long URL.  All mappings are stored in a local JSON file.

To deploy on Vercel, keep this file in an `api/` folder and ensure that
`app` is the FastAPI instance as documented by Vercel’s Python runtime.
For Render, you can point the start command at `api.index:app`.
"""

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import quote
import json
import os

# Create a FastAPI application instance
app = FastAPI()

# Enable CORS so the form can be used from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to the JSON file that stores slug → destination mappings
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'mapping.json')


def load_mappings() -> dict:
    """Load existing slug mappings from the JSON file (or return empty dict)."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If the JSON file is empty or malformed, reset to empty dict
            return {}
    return {}


def save_mappings(data: dict) -> None:
    """Persist slug mappings to the JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        # ensure_ascii=False allows Khmer Unicode characters to be saved
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, message: str = None, error: str = None) -> HTMLResponse:
    """
    Render a simple HTML form for creating new short links.

    Parameters:
    - message: success message to display
    - error: error message to display (e.g., slug already exists)
    """
    # Basic HTML – kept inline for simplicity (no external templates needed)
    html_template = """
    <!DOCTYPE html>
    <html lang="km">
    <head>
        <meta charset="UTF-8">
        <title>KhmerLink URL Shortener</title>
    </head>
    <body>
        <h1>KhmerLink</h1>
        <form method="post" action="/create">
            <label for="slug">ខ្លិ សពអច់ (Khmer short word):</label><br>
            <input type="text" id="slug" name="slug" required><br><br>
            <label for="url">Destination URL:</label><br>
            <input type="url" id="url" name="url" required><br><br>
            <button type="submit">Create Link</button>
        </form>
        {message_block}
        {error_block}
    </body>
    </html>
    """
    # Build success / error blocks if provided
    message_block = f"<p style='color:green;'>{message}</p>" if message else ""
    error_block = f"<p style='color:red;'>{error}</p>" if error else ""
    return HTMLResponse(html_template.format(message_block=message_block, error_block=error_block))


@app.post("/create", response_class=HTMLResponse)
async def create_link(
    request: Request,
    slug: str = Form(...),
    url: str = Form(...)
) -> HTMLResponse:
    """
    Handle form submissions to create a new short link.

    If the slug already exists, an error message is returned.
    Otherwise, the mapping is saved and a success message with the new URL is shown.
    """
    slug = slug.strip()
    url = url.strip()

    data = load_mappings()
    if slug in data:
        # Return error if slug already exists
        return await home(request, error="❌ Slug already exists. Please choose another.")

    # Save the new mapping
    data[slug] = url
    save_mappings(data)

    # Build the full URL (use encodeURIComponent equivalent via urllib.parse.quote)
    base_url = str(request.base_url).rstrip("/")
    encoded_slug = quote(slug, safe="")
    new_link = f"{base_url}/{encoded_slug}"

    # Display success message with clickable link
    success_message = (
        f"✅ Link created successfully!<br>"
        f"New Link: <a href='{new_link}' target='_blank'>{new_link}</a>"
    )
    return await home(request, message=success_message)


@app.get("/{slug}", include_in_schema=False)
async def redirect_to_destination(slug: str):
    """
    Redirect the user to the destination URL for a given slug.
    If the slug isn't found, return a 404.
    """
    data = load_mappings()
    if slug not in data:
        raise HTTPException(status_code=404, detail="Slug not found")
    return RedirectResponse(data[slug])
