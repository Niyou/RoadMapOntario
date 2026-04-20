"""
backend/utils/jobbank.py

Fetches median hourly wage data from the Canada Job Bank website for Ontario.

Two-step process:
  1. Autocomplete API → resolve profession name to noc_job_title_concordance_id
  2. Wage report page → scrape Ontario median hourly wage from the HTML table
"""
import re
import httpx

_AUTOCOMPLETE_URL = (
    "https://www.jobbank.gc.ca/core/ta-jobtitle_en/select"
    "?q={q}&wt=json&rows=3&fq=noc_job_title_type_id:1"
)
_WAGE_REPORT_URL = "https://www.jobbank.gc.ca/wagereport/occupation/{cid}"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-CA,en;q=0.9",
}


async def fetch_ontario_median_wage(profession: str) -> str | None:
    """
    Returns the Ontario median hourly wage for a profession as a formatted string
    (e.g. "$53.85/hr"), or None if unavailable.
    """
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers=_HEADERS) as client:
            # ── Step 1: Look up the concordance ID ───────────────────────────
            search_url = _AUTOCOMPLETE_URL.format(q=profession.replace(" ", "+"))
            resp = await client.get(search_url)
            if resp.status_code != 200:
                return None

            docs = resp.json().get("response", {}).get("docs", [])
            if not docs:
                return None

            concordance_id = docs[0].get("noc_job_title_concordance_id")
            if not concordance_id:
                return None

            # ── Step 2: Scrape Ontario median wage from the wage report ───────
            wage_url = _WAGE_REPORT_URL.format(cid=concordance_id)
            wage_resp = await client.get(wage_url)
            if wage_resp.status_code != 200:
                return None

            html = wage_resp.text
            ontario_wage = _extract_ontario_median(html)
            return ontario_wage

    except Exception:
        return None


def _extract_ontario_median(html: str) -> str | None:
    """
    Extracts the Ontario median hourly wage from the Job Bank wage report HTML.

    The table cell we want has: headers="header_ON header_avg"
    Example: <td class="align-center" headers="header_ON header_avg">53.85
    """
    # Find the Ontario median cell (avg = median in Job Bank terminology)
    match = re.search(
        r'headers="header_ON header_avg"[^>]*>\s*([\d,\.]+)',
        html,
        re.IGNORECASE,
    )
    if match:
        raw = match.group(1).strip().replace(",", "")
        try:
            wage = float(raw)
            return f"${wage:.2f}/hr"
        except ValueError:
            return None

    return None
