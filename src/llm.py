import json
import os

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

GROQ_MODEL = "openai/gpt-oss-120b"


# ============================================================
# GROQ CLIENT
# ============================================================

def get_groq_client():
    """
    Create and return the Groq client.

    GROQ_API_KEY is loaded from the project's .env file.
    The key is never hard-coded or printed.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. "
            "Add it to the .env file at the project root."
        )

    return Groq(api_key=api_key)


# ============================================================
# GROUNDED GENERATION PROMPT
# ============================================================

GROUNDING_SYSTEM_PROMPT = """
You are an insurance evidence-answering assistant.

You will receive:

1. A QUESTION
2. EVIDENCE extracted from insurance product brochures.

Each evidence excerpt contains its source PDF filename and page number.

STRICT RULES:

1. Use ONLY the supplied EVIDENCE for policy-specific facts.
   Do not use outside knowledge.

2. If the evidence is insufficient, do not guess.
   Return:
   "Insufficient evidence in supplied documents."

3. Never combine benefits from different insurance companies or
   products as though they belong to one policy.

4. Break factual information into ATOMIC CLAIMS.

An atomic claim contains only ONE independently verifiable fact.

GOOD:
"The initial waiting period is 30 days."

GOOD:
"Air ambulance coverage is up to ₹5 lakh per year."

BAD:
"The policy has a 30-day waiting period, ₹5 lakh ambulance
coverage, and lifelong renewal."

5. Every atomic claim must contain the exact source PDF filename
   and page number that supports it.

6. Do not invent an accuracy score or confidence percentage.

7. Be conservative when PDF-extracted text appears malformed,
   ambiguous, merged with footnote markers, or incomplete.
   Do not silently repair uncertain numbers.

8. Return ONLY valid JSON in this format:

{
  "answer": "<short overall answer>",
  "supported": true,
  "claims": [
    {
      "claim": "<one factual policy claim>",
      "file": "<source PDF filename>",
      "page": 1
    }
  ],
  "notes": ""
}

If there is not enough evidence, return:

{
  "answer": "Insufficient evidence in supplied documents.",
  "supported": false,
  "claims": [],
  "notes": "<brief explanation of what information is missing>"
}
"""


# ============================================================
# GROUNDED ANSWER GENERATION
# ============================================================

def generate_grounded_answer(query, evidence):
    """
    Generate an answer using ONLY retrieved policy evidence.

    Input:
        query    -> user's question
        evidence -> pages returned by the retrieval system

    Output:
        structured Python dictionary containing:
        - answer
        - supported
        - atomic claims
        - source/page citations
        - notes
    """

    client = get_groq_client()

    evidence_block = "\n\n".join(
        (
            f"[Source: {page['file']}, Page {page['page']}]\n"
            f"{page['text']}"
        )
        for page in evidence
    )

    user_prompt = (
        f"QUESTION:\n{query}\n\n"
        f"EVIDENCE:\n{evidence_block}"
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        response_format={"type": "json_object"},
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": GROUNDING_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    return json.loads(
        response.choices[0].message.content
    )