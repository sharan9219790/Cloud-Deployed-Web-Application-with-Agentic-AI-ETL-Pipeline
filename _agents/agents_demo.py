#!/usr/bin/env python3
"""
agents_demo.py
Planner -> Reviewer -> Finalizer flow using local Ollama (smollm:1.7b).
Output: strict JSON with exactly 3 topical tags and a <=25-word summary.

Usage (non-interactive):
  python3 agents_demo.py --title "My Blog Title" --content "Your blog content ..."

Usage (interactive):
  python3 agents_demo.py
  (then follow prompts; finish content with Ctrl+D on mac/linux, Ctrl+Z then Enter on Windows)
"""
import argparse
import json
import re
import sys
import time
import urllib.request
from datetime import datetime
from typing import Any, Dict, Tuple

# ---- CONFIG ----
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "smollm:1.7b"

# ---- Utilities ----
def ollama_generate(prompt: str, temperature: float = 0.3, timeout: int = 180) -> str:
    """Call Ollama /api/generate and return the generated text (best-effort)."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            obj = json.loads(body)
            # Many Ollama responses provide "response" key for textual content
            # or "output" depending on version; try common keys.
            if isinstance(obj, dict):
                for key in ("response", "output", "message", "result"):
                    if key in obj:
                        val = obj[key]
                        if isinstance(val, str):
                            return val
                        # sometimes nested
                        if isinstance(val, dict) and "content" in val:
                            return val["content"]
                        # sometimes list of dicts
                        if isinstance(val, list) and len(val) and isinstance(val[0], dict) and "content" in val[0]:
                            return val[0]["content"]
            # fallback: stringify entire object
            return json.dumps(obj, ensure_ascii=False)
    except Exception as e:
        print("ERROR: Could not call Ollama at http://localhost:11434.", file=sys.stderr)
        print("Checklist:", file=sys.stderr)
        print("1) Is Ollama running? (open Ollama app or run the service).", file=sys.stderr)
        print("2) Have you pulled the model? `ollama pull smollm:1.7b`", file=sys.stderr)
        print("3) Can you `curl http://localhost:11434/` ?", file=sys.stderr)
        raise

def extract_json_object(text: str) -> Dict[str, Any]:
    """
    Extract the first JSON object from text robustly.
    Accepts fenced ```json { ... } ``` or plain {...} inside text.
    Raises ValueError if none found or cannot parse.
    """
    if not text:
        raise ValueError("Empty model output")

    # try fenced code block first
    fenced = re.search(r"```(?:json)?\s*({.*?})\s*```", text, flags=re.DOTALL)
    if fenced:
        candidate = fenced.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # fallback: find first {...}
    m = re.search(r"({.*})", text, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON object found in model output.")
    candidate = m.group(1).strip()
    # trim to last matching brace
    last = candidate.rfind("}")
    candidate = candidate[: last + 1]
    return json.loads(candidate)

def word_count(s: str) -> int:
    return len([w for w in s.strip().split() if w])

def enforce_constraints(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce:
      - Exactly 3 tags (strings)
      - summary is a string with <= 25 words (hard cutoff)
      - Return only the two keys: tags, summary
    """
    tags = obj.get("tags", [])
    summary = obj.get("summary", "")

    if not isinstance(tags, list):
        tags = []
    tags = [str(t).strip() for t in tags if str(t).strip()]
    tags = tags[:3]
    while len(tags) < 3:
        tags.append("tag")

    summary = str(summary).strip()
    if word_count(summary) > 25:
        summary = " ".join(summary.split()[:25])

    return {"tags": tags, "summary": summary}

# ---- Agents ----
def planner_agent(title: str, content: str) -> Tuple[str, Dict[str, Any]]:
    system = (
        "You are Planner. Create a first draft for tags + summary.\n"
        "Return ONLY a JSON object with keys: tags, summary.\n"
        "Constraints:\n"
        "- tags: array of exactly 3 short topical tags (2-4 words each if possible)\n"
        "- summary: ONE sentence, <= 25 words\n"
        "- No extra keys, no commentary, no markdown.\n"
        "Do not hardcode any domain; infer from the given title/content.\n"
    )
    user = f"TITLE:\n{title}\n\nCONTENT:\n{content}\n\nReturn the JSON now."
    prompt = system + "\n\n" + user
    raw = ollama_generate(prompt, temperature=0.4)
    try:
        obj = extract_json_object(raw)
    except Exception:
        # fallback: try to parse raw as JSON directly
        try:
            obj = json.loads(raw)
        except Exception:
            obj = {}
    obj = enforce_constraints(obj)
    return raw, obj

def reviewer_agent(title: str, content: str, draft: Dict[str, Any]) -> Tuple[str, Dict[str, Any], bool]:
    """
    Robust reviewer: retries up to max_retries if the model doesn't return expected keys.
    Returns (raw_text, parsed_obj, changed_bool).
    """
    base_system = (
        "You are Reviewer. Review Planner's JSON and improve relevance/clarity.\n"
        "RETURN EXACTLY and ONLY a JSON object with keys: tags, summary.\n"
        "- tags: an array of exactly 3 topical tags (strings).\n"
        "- summary: ONE sentence, 25 words max.\n"
        "NO extra keys, NO commentary, NO markdown, NO surrounding text.\n"
        "Infer tags & summary only from TITLE and CONTENT provided.\n"
    )

    user_block = (
        f"TITLE:\n{title}\n\nCONTENT:\n{content}\n\n"
        f"PLANNER_JSON:\n{json.dumps(draft, ensure_ascii=False)}\n\nReturn the improved JSON now."
    )

    attempt = 0
    max_retries = 2
    last_raw = ""
    while attempt <= max_retries:
        attempt += 1
        prompt = base_system + "\n\n" + user_block
        raw = ollama_generate(prompt, temperature=0.25)
        last_raw = raw
        try:
            parsed = extract_json_object(raw)
        except Exception:
            parsed = {}

        # quick validity checks
        tags_ok = isinstance(parsed.get("tags"), list) and len([t for t in parsed.get("tags", []) if str(t).strip()]) >= 1
        summary_ok = isinstance(parsed.get("summary"), str) and len(parsed.get("summary", "").strip()) > 0

        if tags_ok and summary_ok:
            parsed = enforce_constraints(parsed)
            changed = (parsed != draft)
            return raw, parsed, changed

        # prepare a stricter retry message
        user_block = (
            "IMPORTANT: The previous output did not follow the required JSON shape. "
            "Return ONLY and EXACTLY: {\"tags\": [\"tag1\",\"tag2\",\"tag3\"], \"summary\": \"one sentence <=25 words\"}. "
            "Do not include any other keys or commentary. Repair the JSON now.\n\n"
            f"TITLE:\n{title}\n\nCONTENT:\n{content}\n\nPLANNER_JSON:\n{json.dumps(draft, ensure_ascii=False)}\n\n"
        )
        time.sleep(0.6)  # brief pause

    # All retries failed — fall back to planner draft (normalized)
    fallback = enforce_constraints(draft)
    return last_raw, fallback, (fallback != draft)

def finalizer(reviewed: Dict[str, Any]) -> Dict[str, Any]:
    """Final enforcement - returns strict JSON."""
    return enforce_constraints(reviewed)

# ---- Main ----
def main():
    parser = argparse.ArgumentParser(description="Planner -> Reviewer -> Finalizer with Ollama (smollm:1.7b).")
    parser.add_argument("--title", type=str, help="Blog title")
    parser.add_argument("--content", type=str, help="Blog content")
    args = parser.parse_args()

    title = args.title
    content = args.content

    if not title:
        title = input("Enter blog title: ").strip()
    if not content:
        print("Enter blog content (finish with Ctrl+D on mac/Linux, Ctrl+Z then Enter on Windows):")
        content = sys.stdin.read().strip()

    print("\n=== Planner Output (raw) ===")
    planner_raw, planner_json = planner_agent(title, content)
    print(planner_raw.strip())

    print("\n=== Planner Output (parsed+normalized) ===")
    print(json.dumps(planner_json, indent=2, ensure_ascii=False))

    print("\n=== Reviewer Output (raw) ===")
    reviewer_raw, reviewer_json, changed = reviewer_agent(title, content, planner_json)
    print(reviewer_raw.strip())

    print("\n=== Reviewer Output (parsed+normalized) ===")
    print(json.dumps(reviewer_json, indent=2, ensure_ascii=False))

    final = finalizer(reviewer_json)

    print("\n=== Final Publish JSON (STRICT) ===")
    print(json.dumps(final, ensure_ascii=False))

    print("\n=== Short Answers Helper ===")
    print("Q1 tags:", final["tags"])
    print("Q2 summary:", final["summary"])
    print("Q3 reviewer changed anything?:", "yes" if changed else "no")

    print("\n(run timestamp:", datetime.now().isoformat(timespec="seconds") + ")")

if __name__ == "__main__":
    main()


