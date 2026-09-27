import json

from src.llm import GROQ_MODEL, get_groq_client
from src.retrieval import build_retriever, search_policies


# ============================================================
# 1. SOURCE-RESTRICTED CLAIM RETRIEVAL
# ============================================================

def retrieve_claim_evidence(claims, pages):
    """
    Independently retrieve evidence for every AI-generated claim.

    The search is restricted to the PDF that the LLM cited.

    Why?

    Different insurance brochures can contain similar wording.
    If a claim says it came from Care Health, we should verify
    it against Care Health rather than accidentally using a
    similar HDFC or ABHI page.

    This function does NOT decide whether a claim is factually
    correct. It only finds the best evidence for verification.
    """

    retrieved_claims = []

    for claim_item in claims:

        claim_text = claim_item["claim"]

        llm_source = claim_item.get("file")
        llm_page = claim_item.get("page")

        # ----------------------------------------------------
        # Restrict the search to the cited PDF
        # ----------------------------------------------------

        source_pages = [
            page
            for page in pages
            if page["file"] == llm_source
        ]

        # If the LLM cited a file that does not exist in our
        # corpus, the claim cannot currently be verified.
        if not source_pages:

            retrieved_claims.append(
                {
                    "claim": claim_text,

                    "llm_source": llm_source,
                    "llm_page": llm_page,

                    "retrieved_source": None,
                    "retrieved_page": None,

                    "similarity": 0.0,
                    "citation_match": False,

                    "evidence": "",
                }
            )

            continue

        # ----------------------------------------------------
        # Build a temporary TF-IDF index for this PDF only
        # ----------------------------------------------------

        source_vectorizer, source_vectors = build_retriever(
            source_pages
        )

        evidence_results = search_policies(
            claim_text,
            source_pages,
            source_vectorizer,
            source_vectors,
            top_k=min(3, len(source_pages)),
        )

        # ----------------------------------------------------
        # Check whether the LLM's exact cited page appears
        # among the independently retrieved candidates
        # ----------------------------------------------------

        cited_evidence = None

        for result in evidence_results:

            if result["page"] == llm_page:
                cited_evidence = result
                break

        if cited_evidence:

            selected_evidence = cited_evidence
            citation_match = True

        else:

            selected_evidence = evidence_results[0]
            citation_match = False

        retrieved_claims.append(
            {
                "claim": claim_text,

                "llm_source": llm_source,
                "llm_page": llm_page,

                "retrieved_source": selected_evidence["file"],
                "retrieved_page": selected_evidence["page"],

                "similarity": selected_evidence["score"],
                "citation_match": citation_match,

                "evidence": selected_evidence["text"],
            }
        )

    return retrieved_claims


# ============================================================
# 2. FACTUAL VERIFICATION PROMPT
# ============================================================

VERIFICATION_SYSTEM_PROMPT = """
You are a strict insurance claim auditor.

You will receive:

1. ONE generated insurance claim.
2. ONE evidence excerpt from an insurance brochure.

Your job is NOT to generate new insurance information.

Your only job is to determine whether the supplied evidence
supports the supplied claim.

Use ONLY the supplied evidence.

Return exactly one of these statuses:

SUPPORTED

Use SUPPORTED only when:
- the evidence clearly and directly supports the entire claim;
- important numbers, amounts, percentages, durations, limits
  and conditions agree with the evidence.

CONTRADICTED

Use CONTRADICTED when:
- the evidence clearly states something that conflicts with
  the generated claim;
- an important amount, percentage, duration, limit or
  condition is different.

NEEDS_REVIEW

Use NEEDS_REVIEW when:
- the evidence is relevant but ambiguous;
- PDF extraction appears malformed;
- footnote markers may have merged with numbers;
- the text is incomplete or difficult to interpret;
- the exact meaning cannot safely be determined.

Do NOT repair malformed PDF text yourself.

UNSUPPORTED

Use UNSUPPORTED when:
- the evidence does not contain enough information to support
  the claim;
- the page discusses a related topic but does not actually
  state the generated fact.

IMPORTANT RULES:

1. Never use outside insurance knowledge.

2. Do not assume similar wording means the claim is true.

3. Check numbers carefully.

4. Do not silently fix malformed extracted text.

5. A claim is SUPPORTED only when the ENTIRE claim is clearly
   supported by the evidence.

Return ONLY valid JSON in this format:

{
  "status": "SUPPORTED",
  "reason": "<one concise explanation>",
  "evidence_quote": "<short exact excerpt relevant to the decision>"
}

The status MUST be exactly one of:

SUPPORTED
CONTRADICTED
NEEDS_REVIEW
UNSUPPORTED
"""


# ============================================================
# 3. VERIFY ONE CLAIM
# ============================================================

def verify_single_claim(client, claim_item):
    """
    Verify one generated claim against independently retrieved
    brochure evidence.

    This is intentionally separate from claim generation.
    """

    # No source was found.
    if not claim_item["retrieved_source"]:

        return {
            "status": "UNSUPPORTED",
            "reason": (
                "The cited source document could not be found "
                "in the supplied policy corpus."
            ),
            "evidence_quote": "",
        }

    # The cited page was not independently recovered.
    if not claim_item["citation_match"]:

        return {
            "status": "NEEDS_REVIEW",
            "reason": (
                "The cited page was not independently retrieved "
                "among the most relevant pages from that source."
            ),
            "evidence_quote": "",
        }

    user_prompt = f"""
CLAIM:
{claim_item["claim"]}

SOURCE:
{claim_item["retrieved_source"]}

PAGE:
{claim_item["retrieved_page"]}

EVIDENCE:
{claim_item["evidence"]}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        response_format={"type": "json_object"},
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": VERIFICATION_SYSTEM_PROMPT,
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


# ============================================================
# 4. AUDIT ALL CLAIMS
# ============================================================

def audit_claims(retrieved_claims):
    """
    Verify every generated claim.

    Final possible statuses:

    SUPPORTED
    CONTRADICTED
    NEEDS_REVIEW
    UNSUPPORTED
    """

    client = get_groq_client()

    allowed_statuses = {
        "SUPPORTED",
        "CONTRADICTED",
        "NEEDS_REVIEW",
        "UNSUPPORTED",
    }

    audit_results = []

    for claim_item in retrieved_claims:

        verification = verify_single_claim(
            client,
            claim_item,
        )

        status = verification.get(
            "status",
            "NEEDS_REVIEW",
        )

        # Defensive fallback if the model unexpectedly returns
        # a status outside our allowed set.
        if status not in allowed_statuses:
            status = "NEEDS_REVIEW"

        audit_results.append(
            {
                "claim": claim_item["claim"],

                "source": claim_item[
                    "retrieved_source"
                ],

                "page": claim_item[
                    "retrieved_page"
                ],

                "citation_match": claim_item[
                    "citation_match"
                ],

                "retrieval_similarity": claim_item[
                    "similarity"
                ],

                "status": status,

                "reason": verification.get(
                    "reason",
                    "",
                ),

                "evidence_quote": verification.get(
                    "evidence_quote",
                    "",
                ),
            }
        )

    return audit_results


# ============================================================
# 5. AUDIT SUMMARY
# ============================================================

def build_audit_summary(audit_results):
    """
    Count the final claim statuses.

    This summary can later be displayed in the INSUREAI
    advisor-review screen.
    """

    summary = {
        "total_claims": len(audit_results),
        "supported": 0,
        "contradicted": 0,
        "needs_review": 0,
        "unsupported": 0,
    }

    for result in audit_results:

        status = result["status"]

        if status == "SUPPORTED":
            summary["supported"] += 1

        elif status == "CONTRADICTED":
            summary["contradicted"] += 1

        elif status == "NEEDS_REVIEW":
            summary["needs_review"] += 1

        elif status == "UNSUPPORTED":
            summary["unsupported"] += 1

    return summary