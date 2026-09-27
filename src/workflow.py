from src.company_profile import generateCompanyProfile
from src.retrieval import load_policy_pages
from src.pitch import (
    create_pitch,
    revisePitchContent,
)
from src.audit import (
    retrieve_claim_evidence,
    audit_claims,
    build_audit_summary,
)

# ============================================================
# RECOMMENDATION EVIDENCE LINKING
# ============================================================

def link_recommendation_to_audit(
    pitch,
    audited_claims,
):
    """
    Link recommendation selling points back to independently
    audited policy claims.

    This does not create new policy facts and does not change
    the audit result. It only annotates recommendation content
    so downstream exports can distinguish supported selling
    points from items requiring advisor review.
    """

    if not isinstance(pitch, dict):
        return pitch

    recommended = pitch.get(
        "recommended_policy",
        {},
    )

    if not isinstance(recommended, dict):
        return pitch

    selling_points = recommended.get(
        "selling_points",
        [],
    )

    if not isinstance(selling_points, list):
        selling_points = []

    linked_points = []

    for point in selling_points:

        if not isinstance(point, dict):
            continue

        benefit = str(
            point.get("benefit", "")
        ).strip()

        source_file = str(
            point.get("file", "")
        ).strip()

        source_page = point.get(
            "page"
        )

        matched_audit = None

        # ----------------------------------------------------
        # Prefer exact claim + source match.
        # ----------------------------------------------------

        for audited in audited_claims:

            audited_claim = str(
                audited.get("claim", "")
            ).strip()

            audited_source = str(
                audited.get("source", "")
            ).strip()

            if (
                benefit
                and audited_claim == benefit
                and (
                    not source_file
                    or audited_source == source_file
                )
            ):
                matched_audit = audited
                break

        # ----------------------------------------------------
        # Fallback:
        # exact claim text alone.
        # ----------------------------------------------------

        if matched_audit is None:

            for audited in audited_claims:

                audited_claim = str(
                    audited.get("claim", "")
                ).strip()

                if (
                    benefit
                    and audited_claim == benefit
                ):
                    matched_audit = audited
                    break

        linked_point = dict(point)

        if matched_audit is not None:

            audit_status = str(
                matched_audit.get(
                    "status",
                    "NEEDS_REVIEW",
                )
            ).upper()

            linked_point[
                "audit_status"
            ] = audit_status

            linked_point[
                "audit_verified"
            ] = (
                audit_status == "SUPPORTED"
            )

            linked_point[
                "audit_reason"
            ] = matched_audit.get(
                "reason",
                "",
            )

            linked_point[
                "audit_evidence_quote"
            ] = matched_audit.get(
                "evidence_quote",
                "",
            )

            linked_point[
                "audit_retrieval_similarity"
            ] = matched_audit.get(
                "retrieval_similarity",
                0,
            )

        else:

            # A presentation selling point that cannot be
            # linked to an audited atomic claim must not be
            # presented as verified.
            linked_point[
                "audit_status"
            ] = "NEEDS_REVIEW"

            linked_point[
                "audit_verified"
            ] = False

            linked_point[
                "audit_reason"
            ] = (
                "Selling point could not be linked to an "
                "independently audited atomic policy claim."
            )

            linked_point[
                "audit_evidence_quote"
            ] = ""

            linked_point[
                "audit_retrieval_similarity"
            ] = 0

        linked_points.append(
            linked_point
        )

    recommended[
        "selling_points"
    ] = linked_points

    pitch[
        "recommended_policy"
    ] = recommended

    return pitch

def run_pitch_workflow(client_context, selected_insurers):
    """
    Run the complete INSUREAI workflow.

    Flow:
        Company name
            ↓
        Company intelligence
            ↓
        Policy documents
            ↓
        Evidence-grounded pitch
            ↓
        Atomic factual claims
            ↓
        Independent evidence retrieval
            ↓
        Claim-level audit
            ↓
        Human advisor review
    """

    # --------------------------------------------------------
    # 1. VALIDATE COMPANY NAME
    # --------------------------------------------------------

    company_name = (
        client_context.get("company_name", "")
        .strip()
    )

    if not company_name:
        raise ValueError(
            "Company name is required."
        )

    if not selected_insurers:
        raise ValueError(
            "Select at least one policy to compare."
        )

    # --------------------------------------------------------
    # 2. OBJECTIVE 1.2 — COMPANY INTELLIGENCE
    # --------------------------------------------------------

    company_profile = generateCompanyProfile(
        company_name
    )

    # Build the context supplied to the pitch generator.
    #
    # Company facts now come from researched/cached company
    # intelligence rather than requiring the advisor to
    # manually enter industry and workforce information.
    enriched_client_context = {
        "company_name": company_name,
        "industry": company_profile.get(
            "industry",
            "",
        ),
        "company_size": company_profile.get(
            "company_size",
            "",
        ),
        "company_overview": company_profile.get(
            "company_overview",
            "",
        ),
        "key_risks": company_profile.get(
            "key_risks",
            [],
        ),
        "assumptions": company_profile.get(
            "assumptions",
            [],
        ),
        "company_sources": company_profile.get(
            "sources",
            [],
        ),

        # Keep priorities temporarily because the existing
        # pitch generator may still use this field.
        # We can redesign/remove it after verifying the
        # integrated workflow.
        "priorities": client_context.get(
            "priorities",
            [],
        ),
    }

    # --------------------------------------------------------
    # 3. LOAD SOURCE POLICY DOCUMENTS
    # --------------------------------------------------------

    pages = load_policy_pages()

    if not pages:
        raise ValueError(
            "No policy pages were found in the data folder."
        )

    # --------------------------------------------------------
    # 4. GENERATE EVIDENCE-GROUNDED PITCH
    # --------------------------------------------------------

    pitch_result = create_pitch(
        enriched_client_context,
        selected_insurers,
    )

    pitch = pitch_result["pitch"]
    claims = pitch_result["claims"]

    # --------------------------------------------------------
    # 5. RETRIEVE EVIDENCE FOR EVERY GENERATED CLAIM
    # --------------------------------------------------------

    retrieved_claims = retrieve_claim_evidence(
        claims,
        pages,
    )

    # --------------------------------------------------------
    # 6. INDEPENDENTLY AUDIT GENERATED CLAIMS
    # --------------------------------------------------------

    audited_claims = audit_claims(
        retrieved_claims,
    )

    # --------------------------------------------------------
    # 7. LINK RECOMMENDATION TO AUDITED CLAIMS
    # --------------------------------------------------------

    pitch = link_recommendation_to_audit(
        pitch,
        audited_claims,
    )

    # --------------------------------------------------------
    # 8. BUILD AUDIT SUMMARY
    # --------------------------------------------------------

    audit_summary = build_audit_summary(
        audited_claims
    )

    # --------------------------------------------------------
    # 8. RETURN STRUCTURED WORKFLOW RESULT
    # --------------------------------------------------------

    return {
        "client": enriched_client_context,

        # Keep the complete researched profile available
        # separately for the frontend, exports and audit trail.
        "company_profile": company_profile,

        "selected_insurers": selected_insurers,

        "pitch": pitch,

        "claims": audited_claims,

        "audit_summary": audit_summary,

        "advisor_status": "PENDING_REVIEW",
    }

# ============================================================
# ADVISOR REVISION WORKFLOW
# ============================================================

def revise_pitch_workflow(
    workflow_result,
    advisor_instructions,
):
    """
    Revise an existing pitch following advisor instructions
    and independently re-audit every factual policy claim.

    Flow:

    existing reviewed pitch
        ↓
    advisor revision instructions
        ↓
    revised pitch
        ↓
    extract revised factual claims
        ↓
    independent evidence retrieval
        ↓
    claim-level audit
        ↓
    new audit summary
        ↓
    return to advisor for final review
    """

    if not workflow_result:
        raise ValueError(
            "An existing workflow result is required."
        )

    instructions = str(
        advisor_instructions
    ).strip()

    if not instructions:
        raise ValueError(
            "Advisor revision instructions are required."
        )

    existing_pitch = workflow_result.get(
        "pitch"
    )

    client_context = workflow_result.get(
        "client"
    )

    selected_insurers = workflow_result.get(
        "selected_insurers",
        [],
    )

    if not existing_pitch:
        raise ValueError(
            "The workflow result does not contain a pitch."
        )

    if not client_context:
        raise ValueError(
            "The workflow result does not contain client context."
        )

    if not selected_insurers:
        raise ValueError(
            "The workflow result does not contain selected insurers."
        )

    # --------------------------------------------------------
    # 1. REVISE THE PITCH
    # --------------------------------------------------------

    revision_result = revisePitchContent(
        existing_pitch=existing_pitch,
        advisor_instructions=instructions,
        client_context=client_context,
        selected_insurers=selected_insurers,
    )

    revised_pitch = revision_result[
        "pitch"
    ]

    revised_claims = revision_result[
        "claims"
    ]

    # --------------------------------------------------------
    # 2. LOAD ORIGINAL POLICY DOCUMENTS
    # --------------------------------------------------------

    pages = load_policy_pages()

    if not pages:
        raise ValueError(
            "No policy pages were found in the data folder."
        )

    # --------------------------------------------------------
    # 3. INDEPENDENTLY RETRIEVE EVIDENCE FOR REVISED CLAIMS
    # --------------------------------------------------------

    if revised_claims:

        retrieved_claims = (
            retrieve_claim_evidence(
                revised_claims,
                pages,
            )
        )

        # ----------------------------------------------------
        # 4. RE-AUDIT EVERY REVISED FACTUAL CLAIM
        # ----------------------------------------------------

        audited_claims = audit_claims(
            retrieved_claims
        )

    else:

        audited_claims = []
    # --------------------------------------------------------
    # 5. LINK REVISED RECOMMENDATION TO NEW AUDIT
    # --------------------------------------------------------

    revised_pitch = (
        link_recommendation_to_audit(
            revised_pitch,
            audited_claims,
        )
    )
    # --------------------------------------------------------
    # 5. BUILD NEW AUDIT SUMMARY
    # --------------------------------------------------------

    audit_summary = build_audit_summary(
        audited_claims
    )

    # --------------------------------------------------------
    # 6. RETURN REVISED WORKFLOW RESULT
    # --------------------------------------------------------

    revised_result = dict(
        workflow_result
    )

    revised_result["pitch"] = (
        revised_pitch
    )

    revised_result["claims"] = (
        audited_claims
    )

    revised_result["audit_summary"] = (
        audit_summary
    )

    revised_result["advisor_status"] = (
        "PENDING_REVIEW"
    )

    revised_result["revision"] = {
        "edited": True,
        "instructions": instructions,
        "reaudited": True,
    }

    return revised_result