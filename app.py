import os
import json
from flask import Flask, request, render_template
from dotenv import load_dotenv
import anthropic

from tools import scrape_url, web_search, read_cv, score_job
from prompt import SYSTEM_PROMPT
import re


load_dotenv()

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def clean_cover_letter(text):
    if not text:
        return text
    text = re.sub(r'#{1,3}\s*', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'---+', '', text)
    text = re.sub(r'✅|🎯|🏢|⚠️|❌|🔍|🎯', '', text)
    text = '\n'.join(line for line in text.splitlines() if line.strip())
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    return text.strip()


TOOLS = [
    {
        "name": "scrape_url",
        "description": "Fetches the content of a job post URL and returns clean readable text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL of the job post to scrape"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "web_search",
        "description": "Searches the web using Serper API. Use this to research the company, check for scams, verify the recruiter, or look up salary benchmarks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query to run"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_cv",
        "description": "Read the user's CV from cv.txt and returns it as a string.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "score_job",
        "description": "Packages Claude's assesment into a structured score. Call this after researching the company and reading the CV.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fit_score": {"type": "integer", "description": "How well the user fits the role, 0-100"},
                "red_flags": {"type": "array", "items": {"type": "string"}, "description": "List of warning signals"},
                "green_flags": {"type": "array", "items": {"type": "string"}, "description": "List of positive signals"},
                "recommendation": {"type": "string", "description": "One of: apply, proceed with caution, avoid"}
            },
            "required": ["fit_score", "red_flags", "green_flags", "recommendation"]
        }
    }
]


def run_tool(tool_name, tool_input):
    if tool_name == "scrape_url":
        return scrape_url(tool_input["url"])
    elif tool_name == "web_search":
        return web_search(tool_input["query"])
    elif tool_name == "read_cv":
        return read_cv()
    elif tool_name == "score_job":
        result = score_job(
            fit_score=tool_input["fit_score"],
            red_flags=tool_input["red_flags"],
            green_flags=tool_input["green_flags"],
            recommendation=tool_input["recommendation"]
        )

        return json.dumps(result)
    else:
        return f"Unknown tool: {tool_name}"


def run_agent(job_url, job_description=None):
    if job_description and job_description.strip():
        initial_message = f"""Please analyse this job post and help me decide wether to apply.
        
Job URL: {job_url}

Job description: (already extracted):
{job_description}

You do not need to scrape the URL - the job description is already provided.
Please read my CV, research the company, score the role, and write a cover letter."""
    else:
        initial_message = f"Please analyse this job post and help me decide whether to apply: {job_url}"

    messages = [
        {"role": "user", "content": initial_message}]
    score_result = None

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            return score_result, final_text

        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    print(f"Claude calling: {tool_name}")

                    result = run_tool(tool_name, tool_input)

                    if tool_name == "score_job":
                        score_result = json.loads(result)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })
            messages.append({"role": "user", "content": tool_results})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyse", methods=["POST"])
def analyse():
    job_url = request.form.get("job_url")
    job_description = request.form.get("job_description", "").strip()

    if not job_url:
        return render_template("index.html", error="Please paste a job URL first.")

    try:
        score, cover_letter = run_agent(
            job_url, job_description=job_description)
        cover_letter = clean_cover_letter(cover_letter)

        return render_template(
            "result.html",
            score=score,
            cover_letter=cover_letter,
            job_url=job_url
        )

    except Exception as e:
        print("Agent error:", e)
        return render_template("index.html", error="Something went wrong, please try again.")


if __name__ == "__main__":
    app.run(debug=True)
