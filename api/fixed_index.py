from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import quote
import json
import os

app = FastAPI()

# Enable CORS so the form can be used from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to the JSON file that stores slug → destination mappings
DATA_FILE = "mapping.json"


def load_mappings() -> dict:
    """Load existing slug mappings from the JSON file (or return empty dict)."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_mappings(data: dict) -> None:
    """Persist slug mappings to the JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, message: str = None, error: str = None) -> HTMLResponse:
    """
    Render a simple HTML form for creating new short links.

    Parameters:
    - message: success message to display
    - error: error message to display (e.g., slug already exists)
    """
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
            <label for="slug">ខ្ងិ សត្ពក្រ (Khmer short word):</label><br>
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
    message_block = f"<p style='color:green;'>{message}</p>" if message else ""
    error_block = f"<p style='color:red;'>{error}</p>" if error else ""
    return HTMLResponse(html_template.format(message_block=message_block, error_block=error_block))


@app.post("/create", response_class=HTMLResponse)
async def create_link(
    request: Request,
    slug: str = Form(...),
    url: str = Form(...)
) -> HTMLResponse:
    slug = slug.strip()
    url = url.strip()

    data = load_mappings()
    if slug in data:
        return await home(request, error="❌ Slug already exists. Please choose another.")

    data[slug] = url
    save_mappings(data)

    base_url = str(request.base_url).rstrip("/")
    encoded_slug = quote(slug, safe="")
    new_link = f"{base_url}/{encoded_slug}"

    success_message = (
        f"✅ Link created successfully!<br>"
        f"New Link: <a href='{new_link}' target='_blank'>{new_link}</a>"
    )
    return await home(request, message=success_message)


@app.get("/{slug}", include_in_schema=False)
async def redirect_to_destination(slug: str):
    data = load_mappings()
    if slug not in data:
        raise HTTPException(status_code=404, detail="Slug not found")
    return RedirectResponse(data[slug])
