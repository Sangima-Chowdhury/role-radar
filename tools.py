import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


SERPER_API_KEY = os.environ.get("SERPER_API_KEY")


# Scrape the internet to fetch the content of a job post & returns clean text. Clause calls this first to read the actual job description.
def scrape_url(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script & style tags
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        text = soup.get_text(separator="\n")

        # clean up all the blank lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean = "\n".join(lines)

        # cap at 8000 characters - enough for any job post
        return clean[:8000]

    except Exception as e:
        return f"Could not scrape URL: {str(e)}"


# Web search using Serper API & returns top results in clean text. Claude will call this to research the company, check for scams or danger, verifies the recruiter- claude decides.
def web_search(query: str) -> str:
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json"
            },
            json={"q": query, "num": 5}
        )
        data = response.json()

        results = []
        for item in data.get("organic", []):
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            results.append(f"{title}\n{snippet}\n{link}")

        return "\n\n".join(results) if results else "No results found."

    except Exception as e:
        return f"Search failed: {str(e)}"


# Reads my CV from cv.txt & returns is as a string, thrn Claude compares my skills against the job requirements.
def read_cv() -> str:
    # on Render, CV is stored as an environment variable
    cv_content = os.environ.get("CV_CONTENT")
    if cv_content:
        return cv_content
    try:
        with open("cv.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "cv.txt not found. Please add your CV to cv.txt."

# Takes Claude's assesment and packages into a structured dictionary to display in the result page.


def score_job(
        fit_score: int,
        red_flags: list,
        green_flags: list,
        recommendation: str) -> dict:

    return {
        "fit_score": fit_score,
        "red_flags": red_flags,
        "green_flags": green_flags,
        "recommendation": recommendation
    }
