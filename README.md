# RoleRadar 🎯

**Scan a job post before you apply. Research, red flags, fit score, cover letter — all in one.**

Live → [role-radar.onrender.com](https://role-radar.onrender.com)

---

## Why I built this

Job hunting is exhausting enough without applying to roles that are a bad fit,
poorly matched to your skills, or — worst case — outright scams.

I've caught recruitment fraud by hand. A fake training scheme charging candidate
fees. A phishing attempt disguised as a coding test. Every time, it cost me time
I didn't have.

RoleRadar encodes that instinct into an AI agent. Paste a job URL — or copy the
description if it's behind a login wall — and RoleRadar does the research so you
don't have to.

---

## How it works

1. 🔗 **Paste the URL** — or paste the job description directly for LinkedIn roles
2. 🔍 **Agent researches** — scrapes the post, reads your CV, searches the web
3. 🚨 **Flags red signals** — scam signals, vague descriptions, unrealistic salaries
4. 📊 **Scores your fit** — honest 0-100 match against your actual CV
5. ✉️ **Writes a cover letter** — tailored to your real skills, not a template

---

## What makes it an agent

RoleRadar uses Anthropic Claude's **tool use / function calling** — Claude doesn't
just respond, it decides which tools to call, in what order, across multiple steps.

```python
# The agent loop — Claude runs until it's done
while True:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        tools=TOOLS,
        messages=messages
    )
    if response.stop_reason == "end_turn":
        break
    if response.stop_reason == "tool_use":
        # run the tool, feed result back, loop again
```

This is the difference between a chatbot and an agent.

---

## Tools Claude can call

| Tool | What it does |
|------|-------------|
| `scrape_url` | Fetches and cleans the job post content |
| `web_search` | Researches the company via Serper API |
| `read_cv` | Reads your CV to assess fit |
| `score_job` | Structures the final assessment |

Claude decides which tools to call, in what order, how many times.

---

## Tech stack

| Layer | Tech |
|-------|------|
| Backend | Python, Flask |
| AI agent | Anthropic Claude API (tool use / function calling) |
| Web search | Serper API |
| Scraping | BeautifulSoup, Requests |
| Primary deployment | Render |
| Cloud deployment | AWS EC2 (Ubuntu, systemd, port 8001) |
| Database | None — stateless by design |

---

## Deployment

**Render** → [role-radar.onrender.com](https://role-radar.onrender.com) — primary live URL

**AWS EC2** → `http://52.56.60.114:8001` — running alongside BangLense on the same
EC2 instance in eu-west-2 (London). Managed as a persistent systemd service.

---

## Run it locally

```bash
git clone https://github.com/Sangima-Chowdhury/role-radar.git
cd role-radar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY and SERPER_API_KEY
# add your CV text to cv.txt
python app.py
```

Open `http://127.0.0.1:5000`

---

## Project structure

role-radar/
├── app.py          # Flask routes + the agent loop
├── tools.py        # four tools Claude can call
├── prompt.py       # system prompt defining agent behaviour
├── cv.txt          # your CV in plain text (gitignored)
├── gunicorn.conf.py # worker config for Render
├── static/
│   └── style.css   # purple crosshair design system
└── templates/
├── index.html  # landing page
└── result.html # results — score, flags, cover letter

---

Built in East London 🎯
