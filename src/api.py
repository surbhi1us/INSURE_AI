from io import BytesIO
import os
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.company_profile import generateCompanyProfile
from src.export import generate_audit_pdf
from src.pitch_export import generate_pitch_pptx
from src.workflow import (
    run_pitch_workflow,
    revise_pitch_workflow,
)
from src.chatbot import answer_policy_question


# ============================================================
# 1. FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="INSUREAI API",
    description=(
        "AI-assisted insurance pitch generation, "
        "policy comparison and independent claim auditing."
    ),
    version="2.0.0",
)


# ============================================================
# 2. CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 3. REQUEST MODELS
# ============================================================

class ClientContext(BaseModel):
    """
    Information supplied by the advisor.

    Industry, company size, company overview and potential
    exposures are NOT manually entered anymore.

    They are produced by generateCompanyProfile().
    """

    company_name: str = Field(
        min_length=1
    )

    # Optional actual requirements communicated by the
    # client/advisor.
    priorities: List[str] = []


class CompanyProfileRequest(BaseModel):
    company_name: str = Field(
        min_length=1
    )

    force_refresh: bool = False


class PitchRequest(BaseModel):
    client_context: ClientContext

    selected_insurers: List[str] = Field(
        min_length=1
    )


class AdvisorDecisionRequest(BaseModel):
    """
    Human advisor action after reviewing the generated pitch.
    """

    decision: Literal[
        "approved",
        "editing",
        "rejected",
    ]

    notes: Optional[str] = None

class PitchRevisionRequest(BaseModel):
    """
    Revise an existing generated pitch using advisor
    instructions, then independently re-audit its factual
    policy claims.
    """

    workflow_result: Dict[str, Any]

    advisor_instructions: str = Field(
        min_length=1,
        max_length=3000,
    )

class AuditExportRequest(BaseModel):
    workflow_result: Dict[str, Any]


class PitchExportRequest(BaseModel):
    workflow_result: Dict[str, Any]

class ChatRequest(BaseModel):
    """
    Question submitted to the grounded INSUREAI assistant.
    """

    question: str = Field(
        min_length=1,
        max_length=1000,
    )
# ============================================================
# 4. SIMPLE PROTOTYPE REVIEW STATE
# ============================================================

# SQLite is already used for company-profile caching.
#
# Advisor review is kept in memory for now because we will
# later connect editing/review state to the final pitch before
# implementing persistent pitch/project storage.

advisor_review = {
    "decision": None,
    "notes": None,
}


# ============================================================
# 5. HEALTH CHECK
# ============================================================

@app.get("/")
def root():

    return {
        "app": "INSUREAI",
        "version": "2.0.0",
        "status": "running",
    }


@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }


# ============================================================
# 6. OBJECTIVE 1.2 — COMPANY PROFILE
# ============================================================

@app.post("/company-profile")
def company_profile_endpoint(
    request: CompanyProfileRequest
):
    """
    Research or retrieve a company profile.

    Flow:

        company name
            ↓
        SQLite cache
            ↓
        cached? → return existing profile
            ↓ no
        public web research
            ↓
        structured company intelligence
            ↓
        clearly labelled assumptions
            ↓
        SQLite

    force_refresh=True performs fresh research and replaces
    the cached profile.
    """

    try:

        return generateCompanyProfile(
            request.company_name,
            force_refresh=request.force_refresh,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Company research failed: {exc}"
            ),
        )


# ============================================================
# 7. OBJECTIVES 1.3 + 2 — GENERATE AND AUDIT PITCH
# ============================================================

@app.post("/generate-pitch")
def generate_pitch_endpoint(
    request: PitchRequest
):
    """
    Run the complete INSUREAI workflow.

    company name
        ↓
    researched/cached company profile
        ↓
    advisor-selected candidates from the four supplied
    medical-policy documents
        ↓
    per-policy evidence retrieval
        ↓
    evidence-grounded comparison
        ↓
    one best-fit recommendation
        ↓
    atomic factual claims
        ↓
    independent claim audit
        ↓
    advisor review
    """

    try:

        client_context = (
            request.client_context.model_dump()
        )

        selected_insurers = (
            request.selected_insurers
        )

        result = run_pitch_workflow(
            client_context,
            selected_insurers,
        )

        # Every newly generated pitch requires a fresh
        # human review.
        advisor_review["decision"] = None
        advisor_review["notes"] = None

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Pitch generation failed: {exc}"
            ),
        )


# ============================================================
# 8. HUMAN ADVISOR REVIEW
# ============================================================

@app.post("/advisor-decision")
def submit_advisor_decision(
    request: AdvisorDecisionRequest
):
    """
    Record the human advisor's review decision.

    APPROVED:
        Advisor accepts the reviewed pitch.

    EDITING:
        Advisor wants changes before approval.

    REJECTED:
        Advisor rejects the generated pitch.

    This endpoint itself does NOT call the LLM again.
    """

    advisor_review["decision"] = (
        request.decision
    )

    advisor_review["notes"] = (
        request.notes
    )

    status_map = {
        "approved": "APPROVED",
        "editing": "EDITING",
        "rejected": "REJECTED",
    }

    return {
        "status": "saved",
        "advisor_status": status_map[
            request.decision
        ],
        "notes": request.notes,
    }


@app.get("/advisor-decision")
def get_advisor_decision():

    decision = advisor_review[
        "decision"
    ]

    if decision is None:

        return {
            "advisor_status": (
                "PENDING_REVIEW"
            ),
            "notes": None,
        }

    status_map = {
        "approved": "APPROVED",
        "editing": "EDITING",
        "rejected": "REJECTED",
    }

    return {
        "advisor_status": status_map[
            decision
        ],
        "notes": advisor_review[
            "notes"
        ],
    }

# ============================================================
# ADVISOR PITCH REVISION + RE-AUDIT
# ============================================================

@app.post("/revise-pitch")
def revise_pitch_endpoint(
    request: PitchRevisionRequest
):
    try:
        revised_result = revise_pitch_workflow(
            workflow_result=request.workflow_result,
            advisor_instructions=request.advisor_instructions,
        )

        # Revised pitch needs fresh advisor approval.
        advisor_review["decision"] = None
        advisor_review["notes"] = None

        return revised_result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Pitch revision failed: {exc}",
        )

# ============================================================
# 9. GROUNDED INSURANCE ASSISTANT
# ============================================================

@app.post("/chat")
def grounded_chat_endpoint(
    request: ChatRequest,
):
    """
    Answer insurance-policy questions using only evidence
    retrieved from the supplied policy documents.

    Guardrails are implemented in src.chatbot:

    - insurance-domain restriction
    - retrieval grounding
    - abstention when evidence is insufficient
    - no fabricated policy values
    - source/page provenance
    """

    try:

        result = answer_policy_question(
            request.question
        )

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Grounded assistant failed: {exc}"
            ),
        )

# ============================================================
# 9. EXPORT AUDIT REPORT
# ============================================================

@app.post("/export/audit")
def export_audit_report(
    request: AuditExportRequest
):
    """
    Export the existing audit result.

    The AI workflow is NOT rerun.
    """

    try:

        workflow_result = (
            request.workflow_result
        )

        if not workflow_result:
            raise ValueError(
                "No workflow result was supplied "
                "for export."
            )

        pdf_bytes = generate_audit_pdf(
            workflow_result
        )

        if not pdf_bytes:
            raise ValueError(
                "Audit PDF generation returned "
                "an empty file."
            )

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    'attachment; '
                    'filename="insureai_audit_report.pdf"'
                )
            },
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Audit report export failed: {exc}"
            ),
        )


# ============================================================
# 10. EXPORT CLIENT PITCH
# ============================================================

@app.post("/export/pitch")
def export_client_pitch(
    request: PitchExportRequest
):
    """
    Export the already-generated reviewed pitch.

    Groq, retrieval and auditing are NOT rerun.
    """

    try:

        workflow_result = (
            request.workflow_result
        )

        if not workflow_result:
            raise ValueError(
                "No workflow result was supplied "
                "for export."
            )

        pptx_file = generate_pitch_pptx(
            workflow_result
        )

        pptx_file.seek(0)

        return StreamingResponse(
            pptx_file,
            media_type=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "presentationml.presentation"
            ),
            headers={
                "Content-Disposition": (
                    'attachment; '
                    'filename="insureai_client_pitch.pptx"'
                )
            },
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Client pitch export failed: {exc}"
            ),
        )