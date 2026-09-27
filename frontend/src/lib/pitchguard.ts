/**
 * INSUREAI — shared frontend domain types.
 *
 * Policy facts, claims, audit results and recommendations come
 * from the FastAPI backend. The frontend does not hard-code
 * insurance benefits or factual policy claims.
 */

export type ClaimStatus =
  | "VERIFIED"
  | "REVIEW"
  | "CONTRADICTED";


/* ============================================================
   POLICY OPTIONS
   ============================================================ */

export interface PolicyOption {
  id: string;
  insurer: string;
  product: string;

  /**
   * True when the corresponding source policy document is
   * available to the backend for retrieval and verification.
   */
  sourceDocumentAvailable: boolean;
}


/**
 * The four medical-policy documents supplied for the
 * Marsh case study.
 */
export const POLICY_OPTIONS: PolicyOption[] = [
  {
    id: "aditya-birla-activ-one",
    insurer: "Aditya Birla Health Insurance",
    product: "Activ One",
    sourceDocumentAvailable: true,
  },
  {
    id: "care-health",
    insurer: "Care Health Insurance",
    product: "Care Health Insurance",
    sourceDocumentAvailable: true,
  },
  {
    id: "hdfc-ergo-optima-secure-plus",
    insurer: "HDFC ERGO",
    product: "Optima Secure+",
    sourceDocumentAvailable: true,
  },
  {
    id: "niva-bupa-reassure-2",
    insurer: "Niva Bupa",
    product: "ReAssure 2.0",
    sourceDocumentAvailable: true,
  },
];


/* ============================================================
   COMPANY INTELLIGENCE
   ============================================================ */

export interface ClientIntelligence {
  company: string;

  /**
   * Automatically researched by the backend.
   */
  industry: string;

  /**
   * Automatically researched by the backend.
   */
  companySize: string;

  /**
   * Contextual business/workforce exposures derived from
   * researched company information.
   *
   * These are not presented as confirmed client requirements.
   */
  exposures: string[];

  /**
   * Any assumptions are explicitly surfaced for advisor review.
   */
  assumptions: string[];
}


/* ============================================================
   POLICY COMPARISON
   ============================================================ */

export interface NeedBenefitMapping {
  need: string;

  benefit: string;

  policyId: string;

  /**
   * True only when the factual benefit/claim passed the
   * independent audit against the supplied policy document.
   */
  verified: boolean;
}


/* ============================================================
   RECOMMENDATION
   ============================================================ */

export interface Recommendation {
  policyId: string;

  policyLabel: string;

  reasoning: string;

  mapping: NeedBenefitMapping[];
}


/* ============================================================
   CLAIM AUDIT
   ============================================================ */

export interface NumericValidation {
  label: string;

  claimedValue: string;

  sourceValue: string;

  matches: boolean;
}


export interface ClaimEvidence {
  policyLabel: string;

  page: string;

  retrievedPassage: string;

  /**
   * 0–1 TF-IDF retrieval similarity between the generated
   * claim and the evidence passage.
   *
   * This is NOT an AI factual-confidence score.
   */
  semanticMatch: number;

  numericValidation: NumericValidation[];
}


export interface AuditedClaim {
  id: string;

  claim: string;

  policyLabel: string;

  status: ClaimStatus;

  /**
   * Currently stores the evidence retrieval similarity.
   *
   * This should be interpreted as evidence-match strength,
   * not model confidence.
   */
  confidence: number;

  evidence: ClaimEvidence;
}


/* ============================================================
   AUDIT SUMMARY
   ============================================================ */

export interface AuditSummary {
  totalClaims: number;

  verified: number;

  needsReview: number;

  contradicted: number;

  /**
   * Proportion of audited claims that passed verification:
   *
   * verified / total claims
   *
   * Despite the legacy property name, this is a verification
   * pass rate rather than an LLM confidence score.
   */
  confidenceScore: number;
}


/* ============================================================
   COMPLETE UI RESULT
   ============================================================ */

export interface PitchResult {
  isPlaceholderData: boolean;

  intelligence: ClientIntelligence;

  comparison: NeedBenefitMapping[];

  recommendation: Recommendation;

  claims: AuditedClaim[];

  audit: AuditSummary;
}


/* ============================================================
   GENERATION INPUT
   ============================================================ */

/**
 * Information supplied manually by the advisor.
 *
 * Industry, company size and key exposures are deliberately
 * absent because the backend researches them automatically.
 */
export interface GeneratePitchInput {
  companyName: string;

  /**
   * Only genuine requirements communicated by the client or
   * entered by the advisor.
   */
  priorities: string[];

  /**
   * Policies selected from the four supplied case-study
   * documents.
   */
  policyIds: string[];
}


/* ============================================================
   ADVISOR REVIEW
   ============================================================ */

export type AdvisorDecision =
  | "approved"
  | "editing"
  | "rejected";


/* ============================================================
   WORKFLOW STAGES
   ============================================================ */

export const STAGES = [
  {
    id: 1,
    label: "Company Intelligence",
  },
  {
    id: 2,
    label: "Policy Comparison",
  },
  {
    id: 3,
    label: "AI Pitch",
  },
  {
    id: 4,
    label: "Claim Audit",
  },
] as const;


/* ============================================================
   DISPLAY HELPERS
   ============================================================ */

export function statusLabel(
  status: ClaimStatus,
): string {
  if (status === "VERIFIED") {
    return "✓ VERIFIED";
  }

  if (status === "REVIEW") {
    return "⚠ REVIEW";
  }

  return "✕ CONTRADICTED";
}


export function policyLabel(
  option: PolicyOption,
): string {
  return option.insurer === option.product
    ? option.insurer
    : `${option.insurer} — ${option.product}`;
}


export function formatPercent(
  value: number,
): string {
  return `${Math.round(value * 100)}%`;
}