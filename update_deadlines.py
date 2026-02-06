#!/usr/bin/env python3
"""
Helper script to extract conference deadlines from websites using local LLM.

Requirements:
    - llama-cpp-python: uv pip install llama-cpp-python
    - A GGUF model file (e.g., Llama 3.2 3B or 1B)

Usage:
    # First time: download a model
    python update_deadlines.py --download-model

    # Extract deadlines from a URL
    uv run python update_deadlines.py https://neurips.cc

    # Specify custom model path
    uv run python update_deadlines.py https://neurips.cc --model-path ./models/llama-3.2-3b.gguf
"""

import sys
import os
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_SCRAPING = True
except ImportError:
    HAS_SCRAPING = False

try:
    from llama_cpp import Llama
    HAS_LLAMA = True
except ImportError:
    HAS_LLAMA = False


def download_model():
    """Download a small Llama model for deadline extraction."""
    print("Recommended models for this task:")
    print("\n1. Llama 3.2 3B (Recommended - good quality, ~2GB)")
    print("   https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF")
    print("   Download: Llama-3.2-3B-Instruct-Q4_K_M.gguf")
    print("\n2. Llama 3.2 1B (Faster, smaller - ~1GB)")
    print("   https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF")
    print("   Download: Llama-3.2-1B-Instruct-Q4_K_M.gguf")
    print("\nSave the .gguf file to: ./models/")
    print("Then run: uv run python update_deadlines.py https://conference-url")


def find_model():
    """Find a GGUF model in common locations."""
    search_paths = [
        Path("./models"),
        Path("~/.cache/llama-models").expanduser(),
        Path("./"),
    ]

    for search_path in search_paths:
        if not search_path.exists():
            continue

        for model_file in search_path.glob("*.gguf"):
            return str(model_file)

    return None


def fetch_webpage(url):
    """Fetch and parse a webpage."""
    if not HAS_SCRAPING:
        print("Error: requests and beautifulsoup4 not installed.")
        print("Install with: uv pip install requests beautifulsoup4")
        sys.exit(1)

    # Security: Validate URL to prevent SSRF
    if not url.startswith(('http://', 'https://')):
        print("Error: URL must start with http:// or https://")
        sys.exit(1)

    # Block common internal/private addresses
    blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '169.254', '192.168', '10.', '172.16']
    if any(blocked in url.lower() for blocked in blocked_hosts):
        print("Error: Cannot fetch from local/internal addresses")
        sys.exit(1)

    print("Fetching webpage...")
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; ConferenceTracker/1.0)'
    }, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Remove script, style, nav, footer elements
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    text = soup.get_text()

    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)

    # Limit text length for smaller context window
    return text[:3000]


def extract_with_llama(url, text, model_path):
    """Use local Llama via llama.cpp to extract conference information."""
    if not HAS_LLAMA:
        print("Error: llama-cpp-python not installed.")
        print("Install with: uv pip install llama-cpp-python")
        sys.exit(1)

    print(f"Loading model from {model_path}...")
    llm = Llama(
        model_path=model_path,
        n_ctx=4096,  # Context window
        n_threads=4,  # CPU threads
        verbose=False
    )

    prompt = f"""Extract conference deadline information from this webpage.

URL: {url}

Webpage content:
{text}

Find:
1. Conference name (short acronym and full name)
2. Submission deadlines (abstract, paper, workshop, etc.) in YYYY-MM-DD format
3. Conference date in YYYY-MM-DD format

Output YAML format:
```yaml
- name: ACRONYM
  full_name: "Full Name"
  website: "{url}"
  deadlines:
    abstract: "YYYY-MM-DD"
    paper: "YYYY-MM-DD"
  conference_date: "YYYY-MM-DD"
```

Only output the YAML block. If a date is not found, omit that field."""

    print("Analyzing with local LLM...")

    output = llm(
        prompt,
        max_tokens=512,
        temperature=0.3,
        stop=["```\n\n", "\n\nNote:"],
        echo=False
    )

    return output['choices'][0]['text']


def main():
    if "--download-model" in sys.argv:
        download_model()
        sys.exit(0)

    if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
        print("Usage: uv run python update_deadlines.py <conference_url> [options]")
        print("\nExample:")
        print("  uv run python update_deadlines.py https://neurips.cc")
        print("\nOptions:")
        print("  --download-model     Show model download instructions")
        print("  --model-path PATH    Use specific model file")
        print("\nSetup:")
        print("  1. Install dependencies: uv pip install llama-cpp-python requests beautifulsoup4")
        print("  2. Download a model: python update_deadlines.py --download-model")
        sys.exit(1)

    url = sys.argv[1]

    # Find model
    model_path = None
    if "--model-path" in sys.argv:
        idx = sys.argv.index("--model-path")
        if idx + 1 < len(sys.argv):
            model_path = sys.argv[idx + 1]
    else:
        model_path = find_model()

    if not model_path or not Path(model_path).exists():
        print("Error: No GGUF model found.")
        print("\nRun: python update_deadlines.py --download-model")
        print("to see download instructions.")
        sys.exit(1)

    try:
        text = fetch_webpage(url)
    except Exception as e:
        print(f"Error fetching webpage: {e}")
        sys.exit(1)

    try:
        result = extract_with_llama(url, text, model_path)

        print("\n" + "="*70)
        print("SUGGESTED YAML (review before adding to conferences.yaml):")
        print("="*70)
        print(result)
        print("="*70)
        print("\nNote: LLM output may need manual review and correction.")
        print("Check dates carefully before adding to conferences.yaml")

    except Exception as e:
        print(f"Error extracting with LLM: {e}")
        print("\nFallback: Search the content manually for keywords:")
        print("  deadline, submission, abstract, paper, camera-ready")
        sys.exit(1)


if __name__ == "__main__":
    main()
