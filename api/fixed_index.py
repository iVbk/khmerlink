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
    Render the main page with a form to create short links.

    Parameters:
    - message: success message to display
    - error: error message to display (e.g., slug already exists)
    """
    html_template = '''
    <!DOCTYPE html>
    <html lang="km">
    <head>
        <meta charset="UTF-8">
        <title>KhmerLink – URL Shortener</title>
        <style>
            body {
                font-family: system-ui, Khmer UI, Arial, sans-serif;
                background-color: #f7f7f7;
                color: #333;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                text-align: center;
                margin-bottom: 24px;
            }
            form {
                margin-bottom: 16px;
            }
            input[type="text"], input[type="url"] {
                width: 100%;
                padding: 12px 14px;
                margin-bottom: 12px;
                border-radius: 8px;
                border: 1px solid #ccc;
                font-size: 16px;
            }
            button {
                padding: 12px 20px;
                background-color: #5ee2a0;
                border: none;
                border-radius: 8px;
                color: #04130a;
                font-size: 16px;
                cursor: pointer;
            }
            button:hover {
                background-color: #45c88f;
            }
            .message {
                padding: 12px 16px;
                border-radius: 6px;
                margin-top: 12px;
            }
            .success {
                background-color: #e6f5ef;
                color: #2b7a4b;
            }
            .error {
                background-color: #fcebea;
                color: #a94442;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>KhmerLink</h1>
            <form method="post" action="/create">
                <input type="text" id="slug" name="slug" placeholder="ខឍឲលែ កុងតាក៊ិស (Khmer short word)" required>
                <input type="url" id="url" name="url" placeholder="Destination URL" required>
                <button type="submit">Create Link</button>
            </form>
            {{MESSAGE_BLOCK}}
            {{ERROR_BLOCK}}
        </div>
    </body>
    </html>
    '''
    message_block = f"<div class='message success'>{message}</div>" if message else ""
    error_block = f"<div class='message error'>{error}</div>" if error else ""
    html = html_template.replace('{{MESSAGE_BLOCK}}', message_block).replace('{{ERROR_BLOCK}}', error_block)
    return HTMLResponse(html)


@app.post("/create", response_class=HTMLResponse)
async def create_link(
    request: Request,
    slug: str = Form(...),
    url: str = Form(...),
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
        return await home(request, error="Slug already exists. Please choose another.")

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
    """
    Redirect the user to the destination URL for a given slug.
    If the slug isn't found, return a 404.
    """
    data = load_mappings()
    if slug not in data:
        raise HTTPException(status_code=404, detail="Slug not found")

    return RedirectResponse(data[slug])
