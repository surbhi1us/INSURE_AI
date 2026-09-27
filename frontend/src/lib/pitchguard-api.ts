/**
 * INSUREAI — frontend/backend integration.
 *
 * Connects the React frontend to the FastAPI backend and maps
 * the backend workflow response into the PitchResult structure
 * expected by the existing UI components.
 */

import {
  POLICY_OPTIONS,
  policyLabel,
  type ClaimStatus,
  type GeneratePitchInput,
  type NeedBenefitMapping,
  type PitchResult,
} from "./pitchguard";


const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

let latestWorkflowResult: BackendWorkflowResult | null = null;


/* ============================================================
   POLICY ID → BACKEND INSURER NAME
   ============================================================ */

const INSURER_BY_POLICY_ID: Record<string, string> = {
  "aditya-birla-activ-one": "ABHI",
  "care-health": "Care Health",
  "hdfc-ergo-optima-secure-plus": "HDFC",
  "niva-bupa-reassure-2": "Niva Bupa",
};


/* ============================================================
   BACKEND RESPONSE TYPES
   ============================================================ */

interface BackendCompanyProfile {
  company: string;
  industry: string;
  company_size: string;
  company_overview: string;
  key_risks: string[];
  assumptions: string[];
  sources: string[];

  _cache?: {
    hit?: boolean;
    researched_at?: string;
    updated_at?: string;
    refreshed?: boolean;
  };
}


interface BackendPitchClaim {
  claim: string;
  file: string;
  page: number;
}


interface BackendInsurerComparison {
  insurer: string;
  relevance: string;
  claims: BackendPitchClaim[];
  limitations: string[];
}


interface BackendRecommendedPolicy {
  insurer: string;
  rationale: string;
  evidence_basis: string[];
  limitations: string[];
}


interface BackendPitch {
  client: {
    company_name: string;
    industry: string;
    company_size: string;
    company_overview: string;
    key_risks: string[];
    assumptions: string[];
  };

  executive_summary: string;

  client_needs: string[];

  why_marsh: string;

  insurer_comparison: BackendInsurerComparison[];

  recommended_policy: BackendRecommendedPolicy;

  advisor_notes: string[];
}


interface BackendAuditedClaim {
  claim: string;
  source: string;
  page: number;

  citation_match: boolean;

  retrieval_similarity: number;

  status:
    | "SUPPORTED"
    | "NEEDS_REVIEW"
    | "UNSUPPORTED"
    | "CONTRADICTED";

  reason: string;

  evidence_quote: string;
}


interface BackendWorkflowResult {
  client: {
    company_name: string;
    industry: string;
    company_size: string;
    company_overview: string;
    key_risks: string[];
    assumptions: string[];
    company_sources: string[];
    priorities: string[];
  };

  company_profile: BackendCompanyProfile;

  selected_insurers: string[];

  pitch: BackendPitch;

  claims: BackendAuditedClaim[];

  audit_summary: {
    total_claims: number;
    supported: number;
    contradicted: number;
    needs_review: number;
    unsupported: number;
  };

  advisor_status: string;
}


/* ============================================================
   HELPERS
   ============================================================ */

function optionForInsurer(insurer: string) {
  return POLICY_OPTIONS.find(
    (option) =>
      INSURER_BY_POLICY_ID[option.id] === insurer,
  );
}


function labelForInsurer(
  insurer: string,
): string {
  const option = optionForInsurer(insurer);

  return option
    ? policyLabel(option)
    : insurer;
}


function policyIdForInsurer(
  insurer: string,
): string {
  const option = optionForInsurer(insurer);

  return option?.id ?? insurer;
}


function policyLabelForSource(
  source: string,
): string {
  const lower = source.toLowerCase();

  if (lower.includes("hdfc")) {
    return labelForInsurer("HDFC");
  }

  if (lower.includes("care")) {
    return labelForInsurer("Care Health");
  }

  if (
    lower.includes("abhi") ||
    lower.includes("aditya")
  ) {
    return labelForInsurer("ABHI");
  }

  if (
    lower.includes("niva") ||
    lower.includes("bupa")
  ) {
    return labelForInsurer("Niva Bupa");
  }

  return source;
}


function frontendStatus(
  status: BackendAuditedClaim["status"],
): ClaimStatus {
  if (status === "SUPPORTED") {
    return "VERIFIED";
  }

  if (status === "CONTRADICTED") {
    return "CONTRADICTED";
  }

  return "REVIEW";
}


/* ============================================================
   GENERATE PITCH
   ============================================================ */

export async function generatePitch(
  input: GeneratePitchInput,
): Promise<PitchResult> {
  const companyName =
    input.companyName.trim();

  if (!companyName) {
    throw new Error(
      "Enter a client company name to generate a pitch.",
    );
  }

  if (input.policyIds.length === 0) {
    throw new Error(
      "Select at least one policy to compare and audit.",
    );
  }


  /* ----------------------------------------------------------
     MAP FRONTEND POLICY IDS TO BACKEND INSURER NAMES
     ---------------------------------------------------------- */

  const selectedInsurers =
    input.policyIds.map(
      (policyId) =>
        INSURER_BY_POLICY_ID[policyId] ??
        policyId,
    );


  /* ----------------------------------------------------------
     NEW API REQUEST

     Industry, company size, overview and risks are NOT entered
     manually anymore.

     The backend researches them through
     generateCompanyProfile().
     ---------------------------------------------------------- */

  const requestBody = {
    client_context: {
      company_name: companyName,

      priorities:
        input.priorities ?? [],
    },

    selected_insurers:
      selectedInsurers,
  };


  const response = await fetch(
    `${API_BASE_URL}/generate-pitch`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify(
        requestBody,
      ),
    },
  );


  if (!response.ok) {
    let message =
      `Pitch generation failed (${response.status}).`;

    try {
      const errorBody =
        await response.json();

      if (errorBody?.detail) {
        message = String(
          errorBody.detail,
        );
      }
    } catch {
      // Keep fallback message.
    }

    throw new Error(message);
  }


  const backend =
    (await response.json()) as BackendWorkflowResult;

  /*
   * Keep the exact backend result so exports use the same
   * generated/audited data without rerunning AI.
   */
  latestWorkflowResult = backend;


  /* ==========================================================
     COMPARISON / NEED-BENEFIT MAPPING
     ========================================================== */

  const comparison:
    NeedBenefitMapping[] = [];


  for (
    const insurerResult
    of backend.pitch.insurer_comparison
  ) {
    const policyId =
      policyIdForInsurer(
        insurerResult.insurer,
      );


    /*
     * If no factual claim was generated for a selected policy,
     * keep it visible as an evidence gap rather than silently
     * removing it.
     */
    if (
      insurerResult.claims.length === 0
    ) {
      comparison.push({
        need:
          backend.pitch.client_needs.join(
            ", ",
          ) ||
          "Company context",

        benefit:
          insurerResult.relevance ||
          "Insufficient policy evidence was retrieved.",

        policyId,

        verified: false,
      });

      continue;
    }


    for (
      const claim
      of insurerResult.claims
    ) {
      const auditedClaim =
        backend.claims.find(
          (item) =>
            item.claim === claim.claim,
        );

      comparison.push({
        need:
          backend.pitch.client_needs.join(
            ", ",
          ) ||
          "Company context",

        benefit:
          claim.claim,

        policyId,

        verified:
          auditedClaim?.status ===
          "SUPPORTED",
      });
    }
  }


  /* ==========================================================
     AUDITED CLAIMS
     ========================================================== */

  const claims =
    backend.claims.map(
      (claim, index) => {
        const status =
          frontendStatus(
            claim.status,
          );

        return {
          id:
            `claim-${index + 1}`,

          claim:
            claim.claim,

          policyLabel:
            policyLabelForSource(
              claim.source,
            ),

          status,

          /*
           * This remains a retrieval-similarity value,
           * NOT an LLM confidence score.
           */
          confidence:
            claim.retrieval_similarity ??
            0,

          evidence: {
            policyLabel:
              policyLabelForSource(
                claim.source,
              ),

            page:
              String(claim.page),

            retrievedPassage:
              claim.evidence_quote ||
              claim.reason ||
              "No supporting passage was returned.",

            semanticMatch:
              claim.retrieval_similarity ??
              0,

            numericValidation: [],
          },
        };
      },
    );


  /* ==========================================================
     FINAL RECOMMENDATION
     ========================================================== */

  const recommendedInsurer =
    backend.pitch.recommended_policy
      ?.insurer;


  const recommendedPolicyId =
    recommendedInsurer
      ? policyIdForInsurer(
          recommendedInsurer,
        )
      : input.policyIds[0]!;


  const recommendedPolicyOption =
    POLICY_OPTIONS.find(
      (option) =>
        option.id ===
        recommendedPolicyId,
    );


  const recommendationLabel =
    recommendedPolicyOption
      ? policyLabel(
          recommendedPolicyOption,
        )
      : recommendedInsurer ||
        "Advisor review required";


  const recommendationReason =
    backend.pitch.recommended_policy
      ?.rationale ||
    "The generated comparison requires advisor review before a final recommendation is made.";


  /* ==========================================================
     COMPANY INTELLIGENCE
     ========================================================== */

  const profile =
    backend.company_profile;


  const exposures =
    profile?.key_risks?.length
      ? profile.key_risks
      : backend.client.key_risks ??
        [];


  const assumptions = [
    ...(profile?.assumptions ?? []),

    ...(
      backend.pitch.advisor_notes ??
      []
    ),
  ];


  /* ==========================================================
     FINAL UI RESULT
     ========================================================== */

  return {
    isPlaceholderData: false,


    intelligence: {
      company:
        profile?.company ||
        backend.client.company_name,

      industry:
        profile?.industry ||
        backend.client.industry ||
        "Not available",

      companySize:
        profile?.company_size ||
        backend.client.company_size ||
        "Not available",

      exposures,

      assumptions,
    },


    comparison,


    recommendation: {
      policyId:
        recommendedPolicyId,

      policyLabel:
        recommendationLabel,

      reasoning:
        recommendationReason,

      mapping:
        comparison,
    },


    claims,


    audit: {
      totalClaims:
        backend.audit_summary
          .total_claims,

      verified:
        backend.audit_summary
          .supported,

      /*
       * NEEDS_REVIEW and UNSUPPORTED both require
       * human attention.
       */
      needsReview:
        backend.audit_summary
          .needs_review +
        backend.audit_summary
          .unsupported,

      contradicted:
        backend.audit_summary
          .contradicted,

      /*
       * This is a verification pass rate:
       *
       * supported claims / total audited claims
       *
       * It is NOT an AI confidence score.
       */
      confidenceScore:
        backend.audit_summary
          .total_claims > 0
          ? backend.audit_summary
              .supported /
            backend.audit_summary
              .total_claims
          : 0,
    },
  };
}

/* ============================================================
   MAP REVISED BACKEND RESULT TO UI
   ============================================================ */

function mapRevisedBackendResult(
  backend: BackendWorkflowResult,
): PitchResult {
  const comparison: NeedBenefitMapping[] = [];

  for (const insurerResult of backend.pitch.insurer_comparison) {
    const policyId = policyIdForInsurer(
      insurerResult.insurer,
    );

    if (insurerResult.claims.length === 0) {
      comparison.push({
        need:
          backend.pitch.client_needs.join(", ") ||
          "Company context",

        benefit:
          insurerResult.relevance ||
          "Insufficient policy evidence was retrieved.",

        policyId,
        verified: false,
      });

      continue;
    }

    for (const claim of insurerResult.claims) {
      const auditedClaim = backend.claims.find(
        (item) => item.claim === claim.claim,
      );

      comparison.push({
        need:
          backend.pitch.client_needs.join(", ") ||
          "Company context",

        benefit: claim.claim,

        policyId,

        verified:
          auditedClaim?.status === "SUPPORTED",
      });
    }
  }

  const claims = backend.claims.map(
    (claim, index) => ({
      id: `claim-${index + 1}`,

      claim: claim.claim,

      policyLabel: policyLabelForSource(
        claim.source,
      ),

      status: frontendStatus(
        claim.status,
      ),

      confidence:
        claim.retrieval_similarity ?? 0,

      evidence: {
        policyLabel: policyLabelForSource(
          claim.source,
        ),

        page: String(claim.page),

        retrievedPassage:
          claim.evidence_quote ||
          claim.reason ||
          "No supporting passage was returned.",

        semanticMatch:
          claim.retrieval_similarity ?? 0,

        numericValidation: [],
      },
    }),
  );

  const recommendedInsurer =
    backend.pitch.recommended_policy?.insurer;

  const recommendedPolicyId =
    recommendedInsurer
      ? policyIdForInsurer(recommendedInsurer)
      : backend.selected_insurers[0]
        ? policyIdForInsurer(
            backend.selected_insurers[0],
          )
        : "";

  const recommendedPolicyOption =
    POLICY_OPTIONS.find(
      (option) =>
        option.id === recommendedPolicyId,
    );

  const recommendationLabel =
    recommendedPolicyOption
      ? policyLabel(recommendedPolicyOption)
      : recommendedInsurer ||
        "Advisor review required";

  const recommendationReason =
    backend.pitch.recommended_policy?.rationale ||
    "The revised comparison requires advisor review.";

  const profile = backend.company_profile;

  const exposures =
    profile?.key_risks?.length
      ? profile.key_risks
      : backend.client.key_risks ?? [];

  const assumptions = [
    ...(profile?.assumptions ?? []),
    ...(backend.pitch.advisor_notes ?? []),
  ];

  return {
    isPlaceholderData: false,

    intelligence: {
      company:
        profile?.company ||
        backend.client.company_name,

      industry:
        profile?.industry ||
        backend.client.industry ||
        "Not available",

      companySize:
        profile?.company_size ||
        backend.client.company_size ||
        "Not available",

      exposures,
      assumptions,
    },

    comparison,

    recommendation: {
      policyId: recommendedPolicyId,
      policyLabel: recommendationLabel,
      reasoning: recommendationReason,
      mapping: comparison,
    },

    claims,

    audit: {
      totalClaims:
        backend.audit_summary.total_claims,

      verified:
        backend.audit_summary.supported,

      needsReview:
        backend.audit_summary.needs_review +
        backend.audit_summary.unsupported,

      contradicted:
        backend.audit_summary.contradicted,

      confidenceScore:
        backend.audit_summary.total_claims > 0
          ? backend.audit_summary.supported /
            backend.audit_summary.total_claims
          : 0,
    },
  };
}


/* ============================================================
   REVISE PITCH + RE-AUDIT
   ============================================================ */

export async function revisePitch(
  advisorInstructions: string,
): Promise<PitchResult> {
  const instructions =
    advisorInstructions.trim();

  if (!instructions) {
    throw new Error(
      "Enter revision instructions before saving changes.",
    );
  }

  if (!latestWorkflowResult) {
    throw new Error(
      "Generate a pitch before requesting revisions.",
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/revise-pitch`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        workflow_result:
          latestWorkflowResult,

        advisor_instructions:
          instructions,
      }),
    },
  );

  if (!response.ok) {
    let message =
      "Pitch revision failed.";

    try {
      const error =
        await response.json();

      if (error?.detail) {
        message = String(
          error.detail,
        );
      }
    } catch {
      // Keep fallback message.
    }

    throw new Error(message);
  }

  const backend =
    (await response.json()) as BackendWorkflowResult;

  /*
   * This is important:
   * exports now use the REVISED and RE-AUDITED result.
   */
  latestWorkflowResult = backend;

  return mapRevisedBackendResult(
    backend,
  );
}

/* ============================================================
   ADVISOR DECISION
   ============================================================ */

export async function submitAdvisorDecision(
  decision:
    | "approved"
    | "editing"
    | "rejected",
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/advisor-decision`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        decision,
      }),
    },
  );


  if (!response.ok) {
    let message =
      "Could not save advisor decision.";

    try {
      const error =
        await response.json();

      if (error?.detail) {
        message =
          String(error.detail);
      }
    } catch {
      // Keep fallback message.
    }

    throw new Error(message);
  }
}


/* ============================================================
   EXPORT CLIENT PITCH
   ============================================================ */

export async function downloadPitchPptx():
  Promise<void> {
  if (!latestWorkflowResult) {
    throw new Error(
      "Generate a pitch before downloading the client pitch.",
    );
  }


  const response = await fetch(
    `${API_BASE_URL}/export/pitch`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        workflow_result:
          latestWorkflowResult,
      }),
    },
  );


  if (!response.ok) {
    let message =
      "Client pitch export failed.";

    try {
      const error =
        await response.json();

      if (error?.detail) {
        message =
          String(error.detail);
      }
    } catch {
      // Keep fallback message.
    }

    throw new Error(message);
  }


  const blob =
    await response.blob();

  const url =
    window.URL.createObjectURL(
      blob,
    );

  const link =
    document.createElement("a");

  link.href = url;

  link.download =
    "insureai_client_pitch.pptx";

  document.body.appendChild(
    link,
  );

  link.click();

  link.remove();

  window.URL.revokeObjectURL(
    url,
  );
}


/* ============================================================
   EXPORT AUDIT REPORT
   ============================================================ */

export async function downloadAuditReport():
  Promise<void> {
  if (!latestWorkflowResult) {
    throw new Error(
      "Generate a pitch before downloading the audit report.",
    );
  }


  const response = await fetch(
    `${API_BASE_URL}/export/audit`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        workflow_result:
          latestWorkflowResult,
      }),
    },
  );


  if (!response.ok) {
    let message =
      "Audit report export failed.";

    try {
      const error =
        await response.json();

      if (error?.detail) {
        message =
          String(error.detail);
      }
    } catch {
      // Keep fallback message.
    }

    throw new Error(message);
  }


  const blob =
    await response.blob();

  const url =
    window.URL.createObjectURL(
      blob,
    );

  const link =
    document.createElement("a");

  link.href = url;

  link.download =
    "insureai_audit_report.pdf";

  document.body.appendChild(
    link,
  );

  link.click();

  link.remove();

  window.URL.revokeObjectURL(
    url,
  );
}

/* ============================================================
   GROUNDED INSUREAI ASSISTANT
   ============================================================ */

export interface ChatClaim {
  claim: string;
  file: string;
  page: number;
}

export interface ChatSource {
  file: string;
  page: number;
  retrieval_similarity: number;
}

export interface ChatResponse {
  answer: string;
  supported: boolean;
  claims: ChatClaim[];
  sources: ChatSource[];
  notes: string;
}

export async function askInsureAI(
  question: string,
): Promise<ChatResponse> {
  const cleanedQuestion = question.trim();

  if (!cleanedQuestion) {
    throw new Error(
      "Enter a question before sending.",
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/chat`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        question: cleanedQuestion,
      }),
    },
  );

  if (!response.ok) {
    let message =
      "INSUREAI assistant could not answer the question.";

    try {
      const error =
        await response.json();

      if (error?.detail) {
        message = String(error.detail);
      }
    } catch {
      // Keep fallback message.
    }

    throw new Error(message);
  }

  return (await response.json()) as ChatResponse;
}