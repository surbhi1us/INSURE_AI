from typing import Any, Dict, List

from src.llm import generate_grounded_answer
from src.retrieval import (
    build_retriever,
    load_policy_pages,
    search_policies,
)


# ============================================================
# CONFIGURATION
# ============================================================

TOP_K = 5

# Retrieval similarity is NOT confidence.
# This threshold is only a guard against obviously irrelevant
# retrieval results.
MIN_RETRIEVAL_SCORE = 0.03


# ============================================================
# DOMAIN GUARDRAIL
# ============================================================

INSURANCE_TERMS = {
    "insurance",
    "insurer",
    "policy",
    "policies",
    "coverage",
    "cover",
    "benefit",
    "benefits",
    "premium",
    "claim",
    "claims",
    "hospital",
    "hospitalisation",
    "hospitalization",
    "ambulance",
    "medical",
    "health",
    "waiting",
    "period",
    "exclusion",
    "exclusions",
    "sum",
    "insured",
    "employee",
    "employees",
    "workforce",
    "room",
    "rent",
    "maternity",
    "treatment",
    "renewal",
    "deductible",
    "copay",
    "co-pay",
    "hdfc",
    "abhi",
}


def _is_insurance_question(question: str) -> bool:
    """
    Lightweight domain guardrail.

    The chatbot is intended for insurance-policy questions,
    not as a general-purpose assistant.
    """

    lowered = question.lower()

    return any(
        term in lowered
        for term in INSURANCE_TERMS
    )


# ============================================================
# SOURCE CLEANING
# ============================================================

def _build_sources(
    evidence: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Return compact source metadata for the frontend.

    Full PDF page text is deliberately not returned to the UI.
    """

    sources = []

    seen = set()

    for item in evidence:

        key = (
            item.get("file"),
            item.get("page"),
        )

        if key in seen:
            continue

        seen.add(key)

        sources.append(
            {
                "file": item.get("file"),
                "page": item.get("page"),
                "retrieval_similarity":
                    item.get("score", 0),
            }
        )

    return sources


# ============================================================
# CHATBOT
# ============================================================

def answer_policy_question(
    question: str,
) -> Dict[str, Any]:
    """
    Answer an insurance-policy question using only evidence
    retrieved from the supplied policy PDFs.

    Guardrails:
    - insurance-domain only
    - no answer without retrieved evidence
    - no fabricated policy facts
    - source/page provenance
    - abstention when evidence is insufficient
    """

    question = str(question).strip()

    if not question:
        return {
            "answer":
                "Please enter an insurance-policy question.",
            "supported": False,
            "claims": [],
            "sources": [],
            "notes": "No question was provided.",
        }

    # --------------------------------------------------------
    # 1. DOMAIN GUARDRAIL
    # --------------------------------------------------------

    if not _is_insurance_question(
        question
    ):
        return {
            "answer": (
                "I can only answer questions about the "
                "available insurance policies and related "
                "coverage evidence."
            ),
            "supported": False,
            "claims": [],
            "sources": [],
            "notes":
                "Question is outside the INSUREAI domain.",
        }

    # --------------------------------------------------------
    # 2. LOAD POLICY EVIDENCE
    # --------------------------------------------------------

    pages = load_policy_pages()

    if not pages:
        return {
            "answer":
                "I don't have enough information in the "
                "available policy evidence to answer that.",
            "supported": False,
            "claims": [],
            "sources": [],
            "notes":
                "No policy documents are available.",
        }

    # --------------------------------------------------------
    # 3. BUILD RETRIEVER
    # --------------------------------------------------------

    vectorizer, page_vectors = (
        build_retriever(
            pages
        )
    )

    # --------------------------------------------------------
    # 4. RETRIEVE RELEVANT PAGES
    # --------------------------------------------------------

    evidence = search_policies(
        query=question,
        pages=pages,
        vectorizer=vectorizer,
        page_vectors=page_vectors,
        top_k=TOP_K,
    )

    # Remove obviously irrelevant retrieval results.
    relevant_evidence = [
        item
        for item in evidence
        if item.get(
            "score",
            0,
        ) >= MIN_RETRIEVAL_SCORE
    ]

    if not relevant_evidence:
        return {
            "answer": (
                "I don't have enough information in the "
                "available policy evidence to answer that."
            ),
            "supported": False,
            "claims": [],
            "sources": [],
            "notes": (
                "No sufficiently relevant policy evidence "
                "was retrieved."
            ),
        }

    # --------------------------------------------------------
    # 5. GROUNDED LLM ANSWER
    # --------------------------------------------------------

    result = generate_grounded_answer(
        question,
        relevant_evidence,
    )

    # --------------------------------------------------------
    # 6. NORMALISE RESPONSE
    # --------------------------------------------------------

    supported = bool(
        result.get(
            "supported",
            False,
        )
    )

    answer = str(
        result.get(
            "answer",
            "",
        )
    ).strip()

    claims = result.get(
        "claims",
        [],
    )

    notes = str(
        result.get(
            "notes",
            "",
        )
    ).strip()

    # --------------------------------------------------------
    # 7. ABSTENTION GUARDRAIL
    # --------------------------------------------------------

    if not supported:
        return {
            "answer": (
                "I don't have enough information in the "
                "available policy evidence to answer that."
            ),
            "supported": False,
            "claims": [],
            "sources":
                _build_sources(
                    relevant_evidence
                ),
            "notes":
                notes
                or (
                    "The retrieved documents did not provide "
                    "enough evidence for a supported answer."
                ),
        }

    if not answer or not claims:
        return {
            "answer": (
                "I don't have enough information in the "
                "available policy evidence to answer that."
            ),
            "supported": False,
            "claims": [],
            "sources":
                _build_sources(
                    relevant_evidence
                ),
            "notes": (
                "The model did not return supported factual "
                "claims."
            ),
        }

    # --------------------------------------------------------
    # 8. SUCCESS
    # --------------------------------------------------------

    return {
        "answer": answer,
        "supported": True,
        "claims": claims,
        "sources":
            _build_sources(
                relevant_evidence
            ),
        "notes": notes,
    }