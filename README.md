# Conference Deadline Tracker

A minimal web app to track deadlines for major ML/AI and Python conferences. Zero cost - runs locally or on Render's free tier.

## Features

- Clean, minimal UI showing upcoming conference deadlines
- Color-coded urgency indicators (red <7 days, yellow <30 days)
- Auto-sorted by deadline proximity
- LLM-assisted deadline extraction from conference websites (optional)
- Zero API costs - uses local Llama 3.2 via llama.cpp

## Quick Start (Local)

1. Install dependencies:
```bash
uv sync
```

2. Run the server:
```bash
uv run uvicorn main:app --reload
```

3. Open http://localhost:8000

## Updating Conference Deadlines

### Option 1: Manual Edit (Recommended)
Edit `data/conferences.yaml` directly:

```yaml
conferences:
  - name: NeurIPS
    full_name: "Conference on Neural Information Processing Systems"
    website: "https://neurips.cc"
    deadlines:
      abstract: "2024-05-15"
      paper: "2024-05-22"
    conference_date: "2024-12-10"
```

### Option 2: LLM-Assisted Extraction (For Easy Updates)

The `update_deadlines.py` script uses a local Llama model to extract deadlines from conference websites:

1. Install scraper dependencies:
```bash
uv pip install --extra scraper
```

2. Download a model (one-time, ~2GB):
```bash
python update_deadlines.py --download-model
```
Follow the instructions to download a GGUF model to `./models/`

3. Extract deadlines from a URL:
```bash
uv run python update_deadlines.py https://neurips.cc
```

The script will output suggested YAML that you can review and copy into `data/conferences.yaml`.

**Benefits**: No API costs, runs entirely locally, maintains privacy

## Deploying to Render (Free Tier)

1. Push this repo to GitHub

2. Create new Web Service on [Render](https://dashboard.render.com/):
   - Connect your GitHub repository
   - Render auto-detects `render.yaml`
   - Click "Create Web Service"

3. Your site will be live at `https://your-app-name.onrender.com`

**Note**: Render free tier spins down after inactivity. First load may take 30s.

## Tech Stack

- **Backend**: FastAPI (async, fast, minimal)
- **Frontend**: Jinja2 templates + vanilla CSS (no build step)
- **Config**: YAML (human-editable)
- **LLM Helper**: llama.cpp + Llama 3.2 (local, zero cost)
- **Hosting**: Render (free tier)

## Cost Breakdown

- **Hosting**: $0 (Render free tier)
- **LLM API**: $0 (runs locally via llama.cpp)
- **Total**: $0/month
