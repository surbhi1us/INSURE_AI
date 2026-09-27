import json

from src.retrieval import (
    load_policy_pages,
    build_retriever,
    search_policies,
)

from src.llm import generate_grounded_answer

from src.audit import (
    retrieve_claim_evidence,
    audit_claims,
    build_audit_summary,
)


# ============================================================
# INSUREAI — CORE PIPELINE
# ============================================================

def run_insureai_query(query, top_k=5):
    """
    Run the complete INSUREAI evidence-grounded query pipeline.

    Flow:

    PDFs
        ↓
    Page-aware retrieval
        ↓
    Grounded LLM generation
        ↓
    Atomic claims
        ↓
    Independent evidence retrieval
        ↓
    Claim-level factual audit
        ↓
    Final audit summary

    This function coordinates the individual modules.
    It does not contain the retrieval, LLM, or audit logic itself.
    """

    # --------------------------------------------------------
    # 1. Load policy brochure pages
    # --------------------------------------------------------

    pages = load_policy_pages()

    # --------------------------------------------------------
    # 2. Build TF-IDF retrieval index
    # --------------------------------------------------------

    vectorizer, page_vectors = build_retriever(
        pages
    )

    # --------------------------------------------------------
    # 3. Retrieve evidence relevant to the user's query
    # --------------------------------------------------------

    evidence = search_policies(
        query,
        pages,
        vectorizer,
        page_vectors,
        top_k=top_k,
    )

    # --------------------------------------------------------
    # 4. Generate an evidence-grounded answer
    # --------------------------------------------------------

    generated = generate_grounded_answer(
        query,
        evidence,
    )

    generated_claims = generated.get(
        "claims",
        [],
    )

    # --------------------------------------------------------
    # 5. If no claims were generated, return safely
    # --------------------------------------------------------

    if not generated_claims:

        return {
            "query": query,
            "answer": generated.get(
                "answer",
                "",
            ),
            "supported": generated.get(
                "supported",
                False,
            ),
            "claims": [],
            "audit_summary": {
                "total_claims": 0,
                "supported": 0,
                "contradicted": 0,
                "needs_review": 0,
                "unsupported": 0,
            },
            "notes": generated.get(
                "notes",
                "",
            ),
        }

    # --------------------------------------------------------
    # 6. Independently retrieve evidence for every claim
    # --------------------------------------------------------

    retrieved_claims = retrieve_claim_evidence(
        generated_claims,
        pages,
    )

    # --------------------------------------------------------
    # 7. Fact-check every claim
    # --------------------------------------------------------

    audited_claims = audit_claims(
        retrieved_claims
    )

    # --------------------------------------------------------
    # 8. Build audit summary
    # --------------------------------------------------------

    audit_summary = build_audit_summary(
        audited_claims
    )

    # --------------------------------------------------------
    # 9. Return one clean result object
    # --------------------------------------------------------

    return {
        "query": query,

        "answer": generated.get(
            "answer",
            "",
        ),

        "supported": generated.get(
            "supported",
            False,
        ),

        "claims": audited_claims,

        "audit_summary": audit_summary,

        "notes": generated.get(
            "notes",
            "",
        ),
    }


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    test_query = (
        "What air ambulance coverage is available?"
    )

    print("\n" + "=" * 70)
    print("INSUREAI")
    print("=" * 70)

    print(
        f"\nQuestion:\n{test_query}\n"
    )

    result = run_insureai_query(
        test_query
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )