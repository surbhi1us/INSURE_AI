import json
import os
from typing import Any, Dict, List
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient

from src.database import (
    get_company_profile,
    save_company_profile,
)
from src.llm import GROQ_MODEL, get_groq_client


load_dotenv()


# ============================================================
# CLIENTS
# ============================================================

groq_client = get_groq_client()

tavily_api_key = os.getenv("TAVILY_API_KEY")

if not tavily_api_key:
    raise RuntimeError(
        "TAVILY_API_KEY is missing. Add it to the .env file."
    )

tavily_client = TavilyClient(
    api_key=tavily_api_key
)


# ============================================================
# SOURCE HELPERS
# ============================================================

def get_domain(url: str) -> str:
    """
    Return a clean domain name from a URL.
    """

    try:
        return (
            urlparse(url)
            .netloc
            .lower()
            .replace("www.", "")
        )
    except Exception:
        return ""


def source_priority(url: str) -> int:
    """
    Give higher priority to sources that are generally more
    suitable for factual company research.

    This is only a ranking heuristic. Final factual statements
    must still be supported by the retrieved source content.
    """

    domain = get_domain(url)

    # Government / regulatory sources
    if domain.endswith(".gov") or ".gov." in domain:
        return 1

    # SEC filings
    if "sec.gov" in domain:
        return 1

    # Professional company-information sources
    if any(
        trusted in domain
        for trusted in [
            "reuters.com",
            "bloomberg.com",
            "forbes.com",
        ]
    ):
        return 3

    # General reference source
    if "wikipedia.org" in domain:
        return 5

    return 4


def deduplicate_results(
    results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Remove duplicate URLs while preserving the best available
    research result.
    """

    seen = set()
    unique = []

    for item in results:

        url = item.get("url", "").strip()

        if not url or url in seen:
            continue

        seen.add(url)
        unique.append(item)

    return unique


# ============================================================
# WEB RESEARCH
# ============================================================

def run_search(
    query: str,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Execute one Tavily search and normalise the results.
    """

    response = tavily_client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        include_answer=False,
    )

    results = []

    for item in response.get("results", []):

        url = item.get("url", "")

        results.append(
            {
                "title": item.get("title", ""),
                "url": url,
                "domain": get_domain(url),
                "content": item.get("content", ""),
                "score": item.get("score", 0),
                "source_priority": source_priority(url),
            }
        )

    return results


def research_company(
    company_name: str,
) -> List[Dict[str, Any]]:
    """
    Research factual company information from multiple targeted
    web searches.

    Separate searches are used because one generic search often
    returns low-quality aggregators instead of primary company
    sources.

    The research focuses on:
    - official company information
    - industry / business activities
    - company size / employee information
    - annual reports / investor information
    - operations relevant to understanding exposures
    """

    queries = [
        (
            f'"{company_name}" official company '
            f"about business operations"
        ),
        (
            f'"{company_name}" annual report '
            f"employees workforce company size"
        ),
        (
            f'"{company_name}" investor relations '
            f"company overview operations employees"
        ),
        (
            f'"{company_name}" industry business '
            f"operations company profile"
        ),
    ]

    all_results: List[Dict[str, Any]] = []

    for query in queries:
        all_results.extend(
            run_search(
                query,
                max_results=5,
            )
        )

    results = deduplicate_results(
        all_results
    )

    # First use our broad source-quality heuristic,
    # then Tavily relevance score.
    results.sort(
        key=lambda item: (
            item.get("source_priority", 99),
            -float(item.get("score", 0) or 0),
        )
    )

    # Avoid sending excessive web content to the LLM.
    return results[:12]


# ============================================================
# BUILD COMPANY PROFILE
# ============================================================

def build_company_profile(
    company_name: str,
    research_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Structure retrieved web evidence into company intelligence.

    Important distinction:

    VERIFIED FACT
        Directly supported by retrieved source material.

    INFERRED EXPOSURE
        Reasoned from verified operations/industry information,
        but not claimed as a confirmed client insurance need.

    ASSUMPTION
        Used only when required information cannot be established
        from the retrieved sources. Must be advisor-confirmed.
    """

    research_text = "\n\n".join(
        [
            (
                f"SOURCE {index + 1}\n"
                f"Title: {item.get('title', '')}\n"
                f"Domain: {item.get('domain', '')}\n"
                f"URL: {item.get('url', '')}\n"
                f"Content: {item.get('content', '')}"
            )
            for index, item in enumerate(
                research_results
            )
        ]
    )

    prompt = f"""
You are the company-intelligence component of INSUREAI,
an insurance advisory pitch-generation and auditing system.

Your task is to create a concise company profile for:

COMPANY:
{company_name}

The profile will later be used to understand the company
before comparing employee health-insurance products.

IMPORTANT GROUNDING RULE:

Use ONLY the supplied WEB RESEARCH for factual claims.

Do NOT use your own memory or pretrained knowledge to fill in
facts about the company.

WEB RESEARCH:

{research_text}

Return ONLY valid JSON using exactly this structure:

{{
  "company": "{company_name}",
  "industry": "",
  "company_size": "",
  "company_overview": "",
  "key_risks": [],
  "assumptions": [],
  "sources": []
}}

FIELD RULES:

1. industry

Return the industry only when supported by the supplied
research.

If it cannot be reliably established, return:

"Not reliably established from available sources"

and add an assumption/advisor note.

2. company_size

Use an employee count or another meaningful size indicator
only when explicitly supported by the supplied research.

Do NOT estimate an employee number.

If different sources provide different numbers, prefer the
most authoritative and recent source represented in the
research and avoid pretending the number is exact when the
source does not support that precision.

3. company_overview

Write a concise factual description of what the company does.

Only include business activities supported by the supplied
research.

4. key_risks

Return 3 to 5 contextual business/workforce exposures that
could be relevant when an advisor considers employee health
insurance.

IMPORTANT:

These are INFERRED EXPOSURES, not verified insurance needs.

Each item should therefore use cautious wording such as:

"Potential exposure: ..."

or

"Potential workforce consideration: ..."

Only infer an exposure when it logically follows from a
verified company operation or workforce characteristic in
the supplied research.

Do NOT invent:
- accident rates
- illness rates
- employee stress levels
- injury rates
- disease risks
- medical conditions
- insurance requirements

unless the source explicitly establishes the factual point.

5. assumptions

Use this field when important information cannot be
established from the retrieved evidence.

Every item must:

- begin with "Assumption — advisor to confirm:"
- clearly state what is unknown or inferred
- never present the assumption as a verified company fact

Do NOT create unnecessary assumptions when reliable evidence
already exists.

6. sources

Return only URLs from the supplied WEB RESEARCH that were
actually used to support the company profile.

Prefer, when available:

- official company websites
- official annual reports
- investor-relations materials
- regulatory/government filings

Reliable secondary sources may be used when primary evidence
is unavailable.

Do not return URLs that were not supplied above.

7. CLIENT REQUIREMENTS

Never invent the client's insurance priorities.

Company risks/exposures are contextual observations only.

They are NOT confirmed client requirements.

8. FACT VS INFERENCE

A company fact must come directly from source evidence.

A key risk may be an inference from verified company facts,
but must be clearly described as a potential exposure or
consideration.

An assumption must be explicitly labelled for advisor
confirmation.

Return JSON only.
"""

    completion = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.1,
        response_format={
            "type": "json_object"
        },
    )

    content = (
        completion.choices[0]
        .message.content
    )

    if not content:
        raise ValueError(
            "Company profile generation returned no content."
        )

    profile = json.loads(content)

    # Always use the user-supplied company name rather than
    # allowing the model to rename the client.
    profile["company"] = company_name.strip()

    # Ensure expected fields always exist.
    profile.setdefault("industry", "")
    profile.setdefault("company_size", "")
    profile.setdefault("company_overview", "")
    profile.setdefault("key_risks", [])
    profile.setdefault("assumptions", [])
    profile.setdefault("sources", [])

    return profile


# ============================================================
# OBJECTIVE 1.2
# ============================================================

def generateCompanyProfile(
    company_name: str,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    Objective 1.2 — generateCompanyProfile(company_name)

    Gather company information including:
    - industry
    - company size
    - company overview
    - key contextual risks/exposures

    Processing flow:

    1. Check the SQLite company-profile cache.
    2. If cached, return the existing profile.
    3. Otherwise research public web sources.
    4. Structure factual information using Groq.
    5. Clearly label unsupported assumptions.
    6. Store the result in SQLite for reuse.

    force_refresh=True bypasses the existing cached profile
    and updates it using fresh web research.
    """

    cleaned_name = company_name.strip()

    if not cleaned_name:
        raise ValueError(
            "Company name is required."
        )

    # --------------------------------------------------------
    # 1. CHECK SQLITE CACHE
    # --------------------------------------------------------

    if not force_refresh:

        cached = get_company_profile(
            cleaned_name
        )

        if cached is not None:
            return cached

    # --------------------------------------------------------
    # 2. RESEARCH PUBLIC SOURCES
    # --------------------------------------------------------

    research_results = research_company(
        cleaned_name
    )

    if not research_results:

        raise ValueError(
            f"No public company information could be "
            f"retrieved for {cleaned_name}."
        )

    # --------------------------------------------------------
    # 3. STRUCTURE FACTS + INFERRED EXPOSURES + ASSUMPTIONS
    # --------------------------------------------------------

    profile = build_company_profile(
        cleaned_name,
        research_results,
    )

    # --------------------------------------------------------
    # 4. SAVE / UPDATE SQLITE CACHE
    # --------------------------------------------------------

    save_company_profile(
        cleaned_name,
        profile,
    )

    profile["_cache"] = {
        "hit": False,
        "refreshed": force_refresh,
    }

    return profile