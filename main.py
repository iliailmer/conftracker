import os
from datetime import datetime
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Conference Deadline Tracker")

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Basic CSP - allows styles and scripts from same origin only
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'unsafe-inline' 'self'; script-src 'self'"
    return response

# GitHub repo URL for PR submissions (set via environment variable)
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "https://github.com/YOUR_USERNAME/conference-tracker")

# Setup templates
templates = Jinja2Templates(directory="templates")


def load_conferences():
    """Load conference data from YAML file."""
    config_path = Path(__file__).parent / "data" / "conferences.yaml"

    # Security: Ensure we're reading from our own directory only
    if not config_path.is_relative_to(Path(__file__).parent):
        raise ValueError("Invalid config path")

    with open(config_path) as f:
        data = yaml.safe_load(f)  # safe_load prevents code execution

    return data.get("conferences", [])


def parse_date(date_str):
    """Parse date string to datetime object."""
    if not date_str:
        return None
    return datetime.strptime(date_str, "%Y-%m-%d")


def days_until(date_str):
    """Calculate days until a deadline."""
    if not date_str:
        return None
    deadline = parse_date(date_str)
    today = datetime.now()
    delta = (deadline - today).days
    return delta


def enrich_conference_data(conferences):
    """Add computed fields like days until deadline."""
    enriched = []
    today = datetime.now()

    for conf in conferences:
        conf_copy = conf.copy()

        # Find the earliest upcoming deadline
        all_deadlines = []
        for deadline_type, date_str in conf.get("deadlines", {}).items():
            days = days_until(date_str)
            if days is not None:
                all_deadlines.append({
                    "type": deadline_type,
                    "date": date_str,
                    "days": days
                })

        # Sort by days remaining
        all_deadlines.sort(key=lambda x: x["days"])

        conf_copy["all_deadlines"] = all_deadlines
        conf_copy["next_deadline"] = all_deadlines[0] if all_deadlines else None
        conf_copy["conference_days"] = days_until(conf.get("conference_date"))

        enriched.append(conf_copy)

    # Sort conferences by next deadline
    # Upcoming deadlines (days >= 0) come first, passed deadlines (days < 0) go to bottom
    def sort_key(conf):
        if not conf["next_deadline"]:
            return float('inf')  # No deadline = end of list
        days = conf["next_deadline"]["days"]
        if days < 0:
            # Passed deadlines go to bottom, but sorted by how long ago (most recent last)
            return 10000 + abs(days)
        return days  # Upcoming deadlines sorted by proximity

    enriched.sort(key=sort_key)

    return enriched


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main page."""
    conferences = load_conferences()
    conferences = enrich_conference_data(conferences)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "conferences": conferences,
            "github_repo_url": GITHUB_REPO_URL
        }
    )


@app.get("/api/conferences")
async def get_conferences():
    """API endpoint to get conference data."""
    conferences = load_conferences()
    return enrich_conference_data(conferences)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
