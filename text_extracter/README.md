# FlexConnect — Candidate Profile Extractor (Rule-Based)

Builds a structured **student profile** JSON from whichever sources you
give it — **no LLM involved**. Every field is produced by plain Python
logic: GitHub API field lookups, keyword matching, and text heuristics.

```
GitHub username -----\
Resume (PDF/DOCX) ----> rule_engine.py (pure Python) -> structured JSON
Portfolio URL --------/
```

This is separate from `flexconnect-module/` (which extracts
**opportunity** listings and still uses Gemini) — the two are
independent projects.

> **LinkedIn is not supported yet.** It's login-walled and JS-rendered,
> so plain scraping returns almost no text. Skipped for now.

## Why rule-based instead of an LLM?

- **No API key, no cost, no network dependency for the "thinking" step**
  — only the source fetches (GitHub API, portfolio scrape) need network.
- **Fully deterministic and debuggable** — every field in the output can
  be traced to the exact line of code that produced it, which is much
  easier to demo/explain live than "the model decided this."
- **Trade-off:** it only recognizes what it's explicitly told to look
  for (the `SKILL_KEYWORDS` list, a few regex patterns for education/
  experience). It won't understand phrasing outside those rules the way
  an LLM would. Extend `SKILL_KEYWORDS` in `rule_engine.py` any time you
  notice a skill that should've been picked up but wasn't.

## Folder structure

```
profile-extractor/
├── main.py                    # run this — combine sources into one profile
├── requirements.txt
├── .env.example                 # optional GITHUB_TOKEN only (no LLM key needed)
├── README.md
└── profile_extractor/
    ├── __init__.py
    ├── github_source.py        # GitHub public REST API (structured data)
    ├── resume_source.py         # PDF/DOCX text extraction
    ├── portfolio_source.py      # website scraping (requests + trafilatura)
    ├── cleaner.py                  # text cleaning helpers
    ├── rule_engine.py                # <-- the "brain": builds profile fields, no LLM
    └── schema.py                      # Pydantic CandidateProfile schema
```

## Setup

```bash
cd profile-extractor
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# only needed if you hit GitHub API rate limits — add a GITHUB_TOKEN
```

## Run it

```bash
# All three sources
python main.py --github abinasri --resume resume.pdf --portfolio https://myportfolio.com

# Just GitHub
python main.py --github "https://github.com/Abinasri"

# Just a resume
python main.py --resume "C:\Users\HP\Downloads\resume.pdf"
```

### Example output

```json
{
  "success": true,
  "sources_used": ["github"],
  "profile": {
    "name": "Abinasri",
    "headline": "AI & Data Science student building full-stack ML apps",
    "summary": "AI & Data Science student building full-stack ML apps. Abinasri has 12 public GitHub repositories, primarily working with Python, JavaScript.",
    "skills": ["Python", "JavaScript", "Data Science", "machine-learning", "flask", "pytorch", "React"],
    "top_languages": ["Python", "JavaScript"],
    "projects": [
      {
        "name": "FisherGuard-AI",
        "description": "Maritime safety web app using ML",
        "tech_stack": ["Python", "machine-learning", "flask"],
        "link": "https://github.com/Abinasri/FisherGuard-AI"
      }
    ],
    "experience": [],
    "education": "Not specified",
    "github_url": "https://github.com/Abinasri",
    "portfolio_url": "Not specified"
  },
  "error": null
}
```

## How each part works

| Field | Rule |
|---|---|
| `name` | GitHub: `profile["name"]` (fallback `login`). Resume: first short, alphabetic, title-case-ish line near the top of the file. |
| `headline` | GitHub bio if present, else `"<top language> developer"`, else `"Software developer"`. |
| `summary` | Bio (if any) + a generated sentence: `"<name> has <N> public repos, primarily working with <top 3 languages>."` For resume-only, falls back to a skills-based sentence. |
| `skills` | Union of: GitHub top languages + `SKILL_KEYWORDS` matches found in bio/repo descriptions/topics + resume text + portfolio text. Deduplicated case-insensitively. |
| `top_languages` | Frequency count of the `language` field across a user's repos, top 5. |
| `projects` | Every fetched GitHub repo (capped at 8, ranked by stars then recency) becomes a `Project` — `tech_stack` = repo language + topics. |
| `experience` | Resume lines containing `intern`, `engineer`, `developer`, `analyst`, or `trainee` (capped at 5 — this heuristic over-matches on long resumes, so review the output). |
| `education` | First resume line containing an education keyword (`B.Tech`, `Bachelor`, `University`, `College`, etc.). |

**Merging across sources:** for single-value fields (name, summary,
education...), the first source in the merge order to produce a real
value wins (GitHub → resume → portfolio). For list fields (skills,
projects...), everything is unioned and deduplicated — nothing is lost.

## Testing individual pieces

```bash
python -m profile_extractor.github_source      # test GitHub API fetch only
python -m profile_extractor.resume_source        # test PDF/DOCX extraction only
python -m profile_extractor.portfolio_source       # test website scraping only
```

To test the rule engine directly without hitting any network:

```python
from profile_extractor.rule_engine import build_profile_rule_based

profile = build_profile_rule_based(resume_text="Abinasri\nB.Tech AI and Data Science...")
print(profile.model_dump_json(indent=2))
```

## GitHub rate limits

60 unauthenticated requests/hour per IP, shared across everyone on that
IP. If you hit it: create a classic token (no scopes needed) at
https://github.com/settings/tokens and add it as `GITHUB_TOKEN` in
`.env` — raises the limit to 5,000/hour.

## Connecting to the FlexConnect UI

- `main.build_profile(github=..., resume=..., portfolio=...) -> ProfileResult`
  is the one function to call. It never raises.
- For a web form, `resume` should be the path to a temporarily-saved
  upload (save the file to disk first, then pass its path).
- `result.model_dump()` gives a plain dict for `jsonify()`/`json.dumps()`.

## Improving accuracy later

If the rule-based output feels too rough for the final demo, the
highest-leverage next steps (in order of effort):
1. Expand `SKILL_KEYWORDS` in `rule_engine.py` — 30 seconds per skill.
2. Tighten the resume `name`/`education`/`experience` regexes once you
   see real resume formats students actually submit.
3. If quality still isn't enough, this can be swapped back to the
   Gemini-based version (same schema/output shape) with much less
   rework than starting over — the source-fetching modules
   (`github_source.py`, `resume_source.py`, `portfolio_source.py`)
   don't change at all.
