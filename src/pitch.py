import json
from typing import Any, Dict, List
import re

from src.llm import GROQ_MODEL, get_groq_client
from src.retrieval import (
    load_policy_pages,
    build_retriever,
    search_policies,
)


# ============================================================
# 1. CASE-STUDY POLICY CORPUS
# ============================================================

# These are the four medical-policy documents supplied for the
# Marsh case study. INSUREAI does not search the web for other
# insurance products.

CASE_STUDY_INSURERS = {
    "HDFC": "HDFC",
    "Care Health": "Care Health",
    "Niva Bupa": "Niva Bupa",
    "ABHI": "ABHI",
}


# ============================================================
# 2. PITCH GENERATION PROMPT
# ============================================================

PITCH_SYSTEM_PROMPT = """
You are the marketing-pitch generation component of INSUREAI,
an evidence-grounded insurance advisory system.

You will receive:

1. RESEARCHED CLIENT CONTEXT
2. SELECTED INSURERS
3. POLICY EVIDENCE extracted ONLY from the four medical-policy
   documents supplied for the Marsh case study.

Your task is to compare the selected candidate policies against
the client's researched context and produce structured content
for a concise 3-5 slide insurance pitch.

The policy recommendation must be grounded ONLY in the supplied
policy-document evidence.

============================================================
CORE GROUNDING RULES
============================================================

1. Use ONLY the supplied POLICY EVIDENCE for policy-specific
   factual statements.

2. Never use web knowledge, model memory or general insurance
   knowledge to invent policy information.

3. Never invent:

   - benefits
   - limits
   - percentages
   - monetary amounts
   - waiting periods
   - exclusions
   - eligibility rules
   - coverage conditions
   - product features

4. Every policy-specific factual claim must contain:

   - exactly one independently verifiable factual statement
   - exact source PDF filename
   - exact source page number

5. Never cite a page unless the supplied evidence from that
   page directly supports the factual claim.

6. Never transfer a benefit belonging to one insurer to another
   insurer.

7. The four supplied policy documents are the complete insurance
   product corpus for this case study.

============================================================
CLIENT CONTEXT RULES
============================================================

The researched company context may contain:

- industry
- company size
- company overview
- potential key risks/exposures
- assumptions
- optional advisor/client priorities

Company context helps explain WHY a documented policy feature
may be relevant.

Potential exposures are NOT confirmed client requirements.

Assumptions are NOT verified facts.

Do not turn an assumption into a factual statement.

Do not invent workforce characteristics, medical conditions,
accident rates, illness rates or insurance requirements.

Example:

Allowed:
"A documented emergency-transport benefit may be relevant to
the potential transportation exposure identified in the
company profile."

Not allowed:
"The company's employees frequently suffer transport
accidents."

unless such a fact was explicitly established in the supplied
client context.

============================================================
ATOMIC POLICY CLAIM RULE
============================================================

Each policy claim must contain exactly ONE independently
verifiable fact.

GOOD:

"Air ambulance coverage is up to INR 5,00,000."

GOOD:

"Pre-hospitalisation expenses are covered for 60 days."

BAD:

"Air ambulance is covered up to INR 5,00,000 and
pre-hospitalisation expenses are covered for 60 days."

That must become TWO separate claims.

If one sentence contains multiple independently verifiable
benefits, amounts, limits, periods or conditions, split it into
separate claims.

============================================================
SELECTED POLICY COMPARISON
============================================================

The advisor chooses candidate policies from the four supplied
case-study policies.

Every selected insurer must appear in insurer_comparison.

Compare selected insurers using only:

- documented benefits in the supplied evidence
- relevance of those documented benefits to the researched
  company context
- identified evidence gaps or limitations

Do not silently omit a selected insurer.

If useful evidence is limited, explicitly state that the
available retrieved evidence is limited.

Do NOT propose purchasing or combining multiple insurers as one
solution unless the supplied client context explicitly requires
such a structure.

============================================================
BEST-FIT RECOMMENDATION
============================================================

Choose ONE recommended_policy from the SELECTED INSURERS.

This means:

"best-fit candidate among the advisor-selected policies based
on the available documented evidence and researched client
context."

It does NOT mean:

- universally best insurance policy
- cheapest policy
- safest policy
- best policy in the market

unless evidence explicitly establishes such a fact.

The recommendation must be explainable.

Use:

1. relevance of documented policy benefits to identified client
   exposures/needs;

2. strength and usefulness of available supporting evidence;

3. important evidence gaps or limitations.

Do not invent numerical scores or percentages.

Do not fabricate a ranking formula.

Do not recommend an insurer merely because more text happened
to be retrieved.

The rationale must explain the evidence-based fit.

Do not infer that another insurer lacks a benefit merely because the
retrieved evidence does not mention it.

Prefer positive evidence-based comparison language such as:
"The retrieved evidence for Niva Bupa explicitly documents air
ambulance coverage."

Avoid unsupported absence claims such as:
"Other insurers do not provide air ambulance coverage."

Only state that another policy excludes or lacks a benefit when the
supplied evidence explicitly establishes that fact.

============================================================
WHY MARSH
============================================================

The pitch should contain a short "why_marsh" section suitable
for the presentation.

Keep this generic and non-factual unless specific Marsh evidence
has been supplied.

Do NOT invent Marsh statistics, rankings, client numbers,
market-share claims or capabilities that were not provided.

Safe framing includes the value of:

- structured comparison
- evidence-grounded advice
- transparent assumptions
- human advisor review

============================================================
CLIENT PRESENTATION CONTENT
============================================================

The recommended_policy section will be used to build the
client-facing recommendation slide.

SELLING POINTS

selling_points should explain the strongest documented reasons
the recommended candidate may be relevant to this client.

CRITICAL RECOMMENDATION ISOLATION RULE:

Every item in recommended_policy.selling_points MUST belong to
recommended_policy.insurer.

Never place a factual benefit from another insurer inside the
recommended policy's selling_points.

Example:
If recommended_policy.insurer is "Niva Bupa", every selling point
must cite the Niva Bupa source document.

Benefits from competing insurers belong only in insurer_comparison,
not in recommended_policy.selling_points.

Missing evidence for the recommended insurer must not be filled using
a competitor's benefit.

Each selling point must contain:

- benefit: one documented policy-specific factual statement;
- client_relevance: why that documented benefit may be relevant
  to the researched client context;
- file: exact supporting PDF filename;
- page: exact supporting page number.

Do not use generic marketing language such as "best coverage",
"most comprehensive", "superior policy" or "ideal solution"
unless the supplied evidence directly establishes that statement.

POLICY SNAPSHOT

Populate policy_snapshot only when the retrieved policy evidence
directly establishes the information.

Possible fields include:

- sum insured
- premium
- policy term
- hospitalisation
- waiting period

Never infer or calculate a missing value.

Premium is especially important:
do NOT invent a premium from general insurance knowledge.

If a value is not established by the supplied evidence, return:

"Not established in supplied policy evidence"

WORKFORCE RELEVANCE

workforce_relevance should explain how documented policy benefits
may be relevant across different potential employee groups.

Do not invent the company's workforce composition.

Employee groups may only be derived from researched client
context or clearly labelled as potential/general groups.

Do not claim that an employee group has a particular medical
condition, accident frequency or insurance requirement unless
the client context establishes that fact.

Use cautious advisory wording such as:

"may be relevant"
"could support"
"potential need"
"subject to advisor/client confirmation"

The purpose is to create useful selling points while keeping the
recommendation evidence-grounded and suitable for human advisor
review.

============================================================
ADVISOR NOTES
============================================================

advisor_notes should identify:

- assumptions requiring confirmation
- evidence gaps
- limitations
- matters requiring policy-wording review
- items requiring human advisor judgement

Do not invent underwriting requirements.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON using exactly this structure:

{
  "client": {
    "company_name": "",
    "industry": "",
    "company_size": "",
    "company_overview": "",
    "key_risks": [],
    "assumptions": []
  },

  "executive_summary": "",

  "client_needs": [
    ""
  ],

  "why_marsh": "",

  "insurer_comparison": [
    {
      "insurer": "",
      "relevance": "",
      "claims": [
        {
          "claim": "",
          "file": "",
          "page": 1
        }
      ],
      "limitations": []
    }
  ],

  "recommended_policy": {
    "insurer": "",
    "rationale": "",

    "selling_points": [
      {
        "benefit": "",
        "client_relevance": "",
        "file": "",
        "page": 1
      }
    ],

    "policy_snapshot": {
        "sum_insured": "Not established in supplied policy evidence",
        "premium": "Not established in supplied policy evidence",
        "policy_term": "Not established in supplied policy evidence",
        "hospitalisation": "Not established in supplied policy evidence",
        "waiting_period": "Not established in supplied policy evidence"
    },

    "workforce_relevance": [
      {
        "employee_group": "",
        "potential_need": "",
        "policy_relevance": ""
      }
    ],

    "evidence_basis": [
      ""
    ],

    "limitations": [
      ""
    ]
},

  "advisor_notes": [
    ""
  ]
}

============================================================
PITCH SIZE
============================================================

Keep the result concise enough for a 3-5 slide presentation.

For each selected insurer:

- normally include at most 2 high-value factual claims;
- prioritize evidence relevant to the company context;
- do not list every feature in the brochure.

The final recommendation must contain ONE insurer from the
advisor-selected candidates.

The human advisor still approves, edits or rejects the generated
pitch after the independent audit.
"""


# ============================================================
# 3. BUILD COMPANY-TO-POLICY RETRIEVAL QUERY
# ============================================================

def build_pitch_query(
    client_context: Dict[str, Any],
) -> str:
    """
    Convert researched company intelligence into a compact
    retrieval query.

    Workforce context has intentionally been removed.

    Retrieval now uses:
    - industry
    - company overview
    - potential key risks/exposures
    - optional advisor/client priorities
    """

    industry = client_context.get(
        "industry",
        "",
    )

    company_overview = client_context.get(
        "company_overview",
        "",
    )

    key_risks = client_context.get(
        "key_risks",
        [],
    )

    priorities = client_context.get(
        "priorities",
        [],
    )

    risk_text = " ".join(
        str(item)
        for item in key_risks
        if item
    )

    priority_text = " ".join(
        str(item)
        for item in priorities
        if item
    )

    query = (
        f"{industry} "
        f"{company_overview} "
        f"{risk_text} "
        f"{priority_text}"
    ).strip()

    # Health-insurance terminology helps retrieve useful policy
    # clauses even when the researched company description itself
    # does not contain insurance vocabulary.
    insurance_terms = (
        "hospitalisation medical expenses ambulance emergency "
        "transport pre hospitalisation post hospitalisation "
        "room rent ICU treatment waiting period health coverage"
    )

    if query:
        query = f"{query} {insurance_terms}"
    else:
        query = insurance_terms

    return query


# ============================================================
# 4. VALIDATE SELECTED INSURERS
# ============================================================

def validate_selected_insurers(
    selected_insurers: List[str],
) -> List[str]:
    """
    Ensure the advisor is comparing only products belonging to
    the four medical-policy documents supplied in the case study.
    """

    if not selected_insurers:
        raise ValueError(
            "Select at least one of the four case-study policies."
        )

    cleaned = []

    for insurer in selected_insurers:

        if insurer not in CASE_STUDY_INSURERS:
            raise ValueError(
                f"Unsupported insurer '{insurer}'. "
                f"Use only the four supplied case-study policies."
            )

        if insurer not in cleaned:
            cleaned.append(insurer)

    return cleaned


# ============================================================
# 5. FILTER PAGES FOR ONE INSURER
# ============================================================

def get_insurer_pages(
    pages: List[Dict[str, Any]],
    insurer: str,
) -> List[Dict[str, Any]]:
    """
    Return only pages belonging to one selected insurer.

    Filename matching is appropriate here because the case study
    uses a small, fixed collection of four known PDF brochures.
    """

    keyword = CASE_STUDY_INSURERS.get(
        insurer
    )

    if not keyword:
        return []

    keyword_lower = keyword.lower()

    return [
        page
        for page in pages
        if keyword_lower
        in str(
            page.get("file", "")
        ).lower()
    ]


# ============================================================
# 6. RETRIEVE EVIDENCE PER SELECTED INSURER
# ============================================================

def retrieve_pitch_evidence(
    client_context: Dict[str, Any],
    selected_insurers: List[str],
    top_k_per_insurer: int = 2,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant evidence separately for every selected
    insurer.

    This prevents one insurer from occupying all top TF-IDF
    results and gives every selected policy a fair opportunity
    to contribute evidence to the comparison.
    """

    selected_insurers = (
        validate_selected_insurers(
            selected_insurers
        )
    )

    all_pages = load_policy_pages()

    if not all_pages:
        raise ValueError(
            "No policy pages were found in the data folder."
        )

    query = build_pitch_query(
        client_context
    )

    combined_evidence: List[
        Dict[str, Any]
    ] = []

    for insurer in selected_insurers:

        insurer_pages = get_insurer_pages(
            all_pages,
            insurer,
        )

        if not insurer_pages:
            continue

        vectorizer, page_vectors = (
            build_retriever(
                insurer_pages
            )
        )

        insurer_evidence = search_policies(
            query,
            insurer_pages,
            vectorizer,
            page_vectors,
            top_k=min(
                top_k_per_insurer,
                len(insurer_pages),
            ),
        )

        for item in insurer_evidence:

            evidence_item = dict(item)

            # Add insurer metadata for easier debugging and
            # transparent prompt construction.
            evidence_item["insurer"] = (
                insurer
            )

            combined_evidence.append(
                evidence_item
            )

    if not combined_evidence:
        raise ValueError(
            "No relevant policy evidence could be retrieved "
            "from the selected case-study documents."
        )

    return combined_evidence


# ============================================================
# 7. FORMAT POLICY EVIDENCE
# ============================================================

def build_evidence_block(
    evidence: List[Dict[str, Any]],
    max_chars_per_page: int = 2000,
) -> str:
    """
    Convert retrieved policy pages into a compact evidence block.

    Retrieval still selects the most relevant pages per insurer,
    but very long PDF pages are capped before being sent to the LLM.

    This reduces token usage while preserving:
    - insurer
    - filename
    - page number
    - retrieval similarity
    - the beginning of the retrieved evidence

    The original PDF text is NOT modified in storage.
    """

    blocks = []

    for item in evidence:

        insurer = item.get(
            "insurer",
            "Unknown insurer",
        )

        filename = item.get(
            "file",
            "Unknown file",
        )

        page = item.get(
            "page",
            "?",
        )

        score = item.get(
            "score",
            0,
        )

        text = str(
            item.get("text", "")
        ).strip()

        # Prevent unusually large PDF pages from overflowing
        # the Groq TPM/request budget.
        if len(text) > max_chars_per_page:
            text = (
                text[:max_chars_per_page].rstrip()
                + "\n[Page text truncated for prompt-size control]"
            )

        blocks.append(
            (
                f"INSURER: {insurer}\n"
                f"SOURCE: {filename}\n"
                f"PAGE: {page}\n"
                f"RETRIEVAL SIMILARITY: {score}\n"
                f"EVIDENCE:\n{text}"
            )
        )

    return "\n\n---\n\n".join(blocks)


# ============================================================
# 8. NORMALISE GENERATED PITCH
# ============================================================

def normalise_pitch(
    pitch: Dict[str, Any],
    client_context: Dict[str, Any],
    selected_insurers: List[str],
) -> Dict[str, Any]:
    """
    Add structural safeguards after LLM generation.

    This does not invent content. It simply guarantees that
    expected fields exist and removes legacy workforce_context.
    """

    pitch.setdefault(
        "client",
        {},
    )

    pitch["client"] = {
        "company_name": client_context.get(
            "company_name",
            "",
        ),
        "industry": client_context.get(
            "industry",
            "",
        ),
        "company_size": client_context.get(
            "company_size",
            "",
        ),
        "company_overview": client_context.get(
            "company_overview",
            "",
        ),
        "key_risks": client_context.get(
            "key_risks",
            [],
        ),
        "assumptions": client_context.get(
            "assumptions",
            [],
        ),
    }

    pitch.setdefault(
        "executive_summary",
        "",
    )

    pitch.setdefault(
        "client_needs",
        [],
    )

    pitch.setdefault(
        "why_marsh",
        "",
    )

    pitch.setdefault(
        "insurer_comparison",
        [],
    )

    pitch.setdefault(
        "recommended_policy",
        {
            "insurer": "",
            "rationale": "",
            "selling_points": [],
            "policy_snapshot": {
                "sum_insured": "Not established in supplied policy evidence",
                "premium": "Not established in supplied policy evidence",
                "policy_term": "Not established in supplied policy evidence",
                "hospitalisation": "Not established in supplied policy evidence",
                "waiting_period": "Not established in supplied policy evidence",
            },
            "workforce_relevance": [],
            "evidence_basis": [],
            "limitations": [],
        },
    )

    pitch.setdefault(
        "advisor_notes",
        [],
    )

    # --------------------------------------------------------
    # Ensure all selected insurers are represented.
    # --------------------------------------------------------

    comparison_by_insurer = {}

    for item in pitch.get(
        "insurer_comparison",
        [],
    ):

        insurer = item.get(
            "insurer",
            "",
        )

        if insurer in selected_insurers:
            comparison_by_insurer[
                insurer
            ] = item

    ordered_comparison = []

    for insurer in selected_insurers:

        item = comparison_by_insurer.get(
            insurer
        )

        if item is None:

            item = {
                "insurer": insurer,
                "relevance": (
                    "Insufficient structured comparison "
                    "was generated from the retrieved evidence."
                ),
                "claims": [],
                "limitations": [
                    (
                        "Advisor should review the retrieved "
                        "brochure evidence before relying on "
                        "this option."
                    )
                ],
            }

        item.setdefault(
            "relevance",
            "",
        )

        item.setdefault(
            "claims",
            [],
        )

        item.setdefault(
            "limitations",
            [],
        )

        ordered_comparison.append(
            item
        )

    pitch["insurer_comparison"] = (
        ordered_comparison
    )

    # --------------------------------------------------------
    # Recommendation must come from selected candidates.
    # --------------------------------------------------------

    recommended = pitch.get(
        "recommended_policy",
        {},
    )

    recommended_insurer = (
        str(recommended.get("insurer", "")).strip()
        if isinstance(recommended, dict)
        else ""
    )

        # --------------------------------------------------------
    # Normalise insurer / product-name variations returned
    # by the LLM.
    #
    # The model may return:
    #   "ABHI"
    #   "Aditya Birla Health Insurance"
    #   "Aditya Birla Health Insurance — Activ One"
    #   "HDFC ERGO Optima Secure+"
    #
    # We map these back to the canonical insurer identifiers
    # used internally by the workflow.
    # --------------------------------------------------------

    def _canonical_insurer_name(value: str) -> str:
        raw = str(value or "").strip()
        lowered = raw.lower()

        if not lowered:
            return ""

        # Aditya Birla / ABHI
        if (
            lowered == "abhi"
            or "aditya birla" in lowered
            or "activ one" in lowered
        ):
            return "ABHI"

        # HDFC ERGO
        if (
            lowered == "hdfc"
            or "hdfc ergo" in lowered
            or "optima secure" in lowered
        ):
            return "HDFC"

        # Care Health
        if (
            lowered == "care"
            or "care health" in lowered
        ):
            return "Care Health"

        # Niva Bupa
        if (
            "niva bupa" in lowered
            or "reassure" in lowered
        ):
            return "Niva Bupa"

        return raw

    normalised_recommendation = (
        _canonical_insurer_name(
            recommended_insurer
        )
    )

    if normalised_recommendation in selected_insurers:

        recommended["insurer"] = normalised_recommendation

        recommended.setdefault(
            "rationale",
            "",
        )

        recommended.setdefault(
            "selling_points",
            [],
        )
        # ----------------------------------------------------
        # Recommendation integrity:
        # selling points must belong ONLY to the recommended
        # insurer.
        #
        # The LLM compares multiple insurers in one prompt and
        # may occasionally place a competitor's factual claim
        # inside recommended_policy.selling_points.
        #
        # Never allow that cross-insurer contamination into the
        # client-facing recommendation.
        # ----------------------------------------------------

        insurer_file_markers = {
            "ABHI": (
                "abhi",
                "aditya birla",
            ),
            "Care Health": (
                "care health",
                "care",
            ),
            "HDFC": (
                "hdfc",
            ),
            "Niva Bupa": (
                "niva bupa",
                "niva",
            ),
        }

        allowed_markers = insurer_file_markers.get(
            normalised_recommendation,
            (),
        )

        clean_selling_points = []
        seen_selling_points = set()

        for point in recommended.get(
            "selling_points",
            [],
        ):

            if not isinstance(point, dict):
                continue

            benefit = str(
                point.get("benefit", "")
            ).strip()

            source_file = str(
                point.get("file", "")
            ).strip()

            source_page = point.get("page")

            if not benefit or not source_file:
                continue

            source_lower = source_file.lower()

            belongs_to_recommended = any(
                marker in source_lower
                for marker in allowed_markers
            )

            if not belongs_to_recommended:
                continue

            # Keep only structurally valid sourced points.
            try:
                source_page = int(source_page)
            except (TypeError, ValueError):
                continue

            if source_page < 1:
                continue

            # Deduplicate repeated benefits while preserving the first
            # valid source-backed occurrence. Normalising punctuation and
            # whitespace prevents cosmetic LLM variations from appearing
            # twice in the client-facing recommendation.
            dedupe_key = re.sub(
                r"[^a-z0-9]+",
                " ",
                benefit.lower(),
            ).strip()

            if dedupe_key in seen_selling_points:
                continue

            seen_selling_points.add(dedupe_key)

            clean_point = dict(point)

            clean_point["benefit"] = benefit
            clean_point["file"] = source_file
            clean_point["page"] = source_page

            clean_selling_points.append(
                clean_point
            )

        recommended["selling_points"] = (
            clean_selling_points
        )
        recommended.setdefault(
            "policy_snapshot",
            {},
        )

        # Ensure policy_snapshot is always a dictionary.
        if not isinstance(
            recommended["policy_snapshot"],
            dict,
        ):
            recommended["policy_snapshot"] = {}

        snapshot = recommended[
            "policy_snapshot"
        ]

        snapshot.setdefault(
            "sum_insured",
            "Not established in supplied policy evidence",
        )

        snapshot.setdefault(
            "premium",
            "Not established in supplied policy evidence",
        )

        snapshot.setdefault(
            "policy_term",
            "Not established in supplied policy evidence",
        )

        snapshot.setdefault(
            "hospitalisation",
            "Not established in supplied policy evidence",
        )

        snapshot.setdefault(
            "waiting_period",
            "Not established in supplied policy evidence",
        )

        recommended.setdefault(
            "workforce_relevance",
            [],
        )

        recommended.setdefault(
            "evidence_basis",
            [],
        )

        recommended.setdefault(
            "limitations",
            [],
        )

        pitch["recommended_policy"] = recommended


    else:

        pitch["recommended_policy"] = {
            "insurer": "",

            "rationale": (
                "No valid best-fit recommendation was generated "
                "from the selected candidates."
            ),

            "selling_points": [],

            "policy_snapshot": {
                "sum_insured":
                    "Not established in supplied policy evidence",

                "premium":
                    "Not established in supplied policy evidence",

                "policy_term":
                    "Not established in supplied policy evidence",

                "hospitalisation":
                    "Not established in supplied policy evidence",

                "waiting_period":
                    "Not established in supplied policy evidence",
            },

            "workforce_relevance": [],

            "evidence_basis": [],

            "limitations": [
                (
                    "Human advisor review is required before a "
                    "final recommendation is made."
                )
            ],
        }

    return pitch


# ============================================================
# 9. GENERATE STRUCTURED MARKETING PITCH
# ============================================================

def generate_pitch(
    client_context: Dict[str, Any],
    selected_insurers: List[str],
    evidence: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Generate structured pitch content using only the supplied
    client context and evidence retrieved from the four
    case-study medical-policy documents.
    """

    selected_insurers = (
        validate_selected_insurers(
            selected_insurers
        )
    )

    client = get_groq_client()

    evidence_block = (
        build_evidence_block(
            evidence
        )
    )

    client_block = json.dumps(
        client_context,
        indent=2,
        ensure_ascii=False,
    )

    insurer_block = json.dumps(
        selected_insurers,
        indent=2,
        ensure_ascii=False,
    )

    user_prompt = f"""
RESEARCHED CLIENT CONTEXT:
{client_block}

SELECTED INSURERS:
{insurer_block}

POLICY EVIDENCE FROM THE FOUR SUPPLIED CASE-STUDY DOCUMENTS:
{evidence_block}

Generate the structured marketing pitch.

Remember:

- compare every selected candidate;
- use only supplied policy evidence for policy facts;
- choose exactly one best-fit recommended_policy from the
  selected candidates;
- recommended_policy.insurer MUST be exactly one of the strings
  listed in SELECTED INSURERS above;
- do not return a product name in recommended_policy.insurer;
- do not return an insurer that was not selected;
- do not invent numerical ranking scores;
- clearly identify limitations and assumptions;
- the recommendation remains subject to independent claim audit
  and human advisor approval.
"""

    response = (
        client.chat.completions.create(
            model=GROQ_MODEL,
            response_format={
                "type": "json_object"
            },
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        PITCH_SYSTEM_PROMPT
                    ),
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )
    )

    content = (
        response.choices[0]
        .message.content
    )

    if not content:
        raise ValueError(
            "Pitch generation returned no content."
        )

    pitch = json.loads(
        content
    )

    return normalise_pitch(
        pitch,
        client_context,
        selected_insurers,
    )


# ============================================================
# 10. EXTRACT ALL POLICY-SPECIFIC CLAIMS
# ============================================================

def extract_pitch_claims(
    pitch: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Collect policy-specific factual claims from the comparison.

    These atomic claims are sent to the independent audit layer.

    We deliberately audit claims rather than trusting the pitch
    simply because an LLM generated it.
    """

    claims = []

    for insurer_item in pitch.get(
        "insurer_comparison",
        [],
    ):

        for claim in insurer_item.get(
            "claims",
            [],
        ):

            claim_text = str(
                claim.get(
                    "claim",
                    "",
                )
            ).strip()

            filename = str(
                claim.get(
                    "file",
                    "",
                )
            ).strip()

            page = claim.get(
                "page"
            )

            # Do not create artificial factual claims for
            # evidence-gap messages.
            if not claim_text:
                continue

            if not filename or not page:
                continue

            claims.append(
                {
                    "claim": claim_text,
                    "file": filename,
                    "page": page,
                }
            )

    return claims


# ============================================================
# 11. OBJECTIVE 1.3 — GENERATE MARKETING PITCH
# ============================================================

def generateMarketingPitch(
    client_context: Dict[str, Any],
    selected_insurers: List[str],
) -> Dict[str, Any]:
    """
    Objective 1.3 — generateMarketingPitch()

    Produce structured content for a 3-5 slide marketing pitch
    covering:

    - company overview
    - contextual risks/exposures
    - why Marsh / evidence-grounded advisory approach
    - selected policy comparison
    - policy benefits mapped to client context
    - one final best-fit policy recommendation

    Policy facts are grounded only in the four medical-policy
    documents supplied for the Marsh case study.

    The generated policy claims are NOT considered trusted yet.
    They must pass through the independent audit layer before
    advisor approval.
    """

    selected_insurers = (
        validate_selected_insurers(
            selected_insurers
        )
    )

    evidence = retrieve_pitch_evidence(
        client_context,
        selected_insurers,
        top_k_per_insurer=2,
    )

    pitch = generate_pitch(
        client_context,
        selected_insurers,
        evidence,
    )

    claims = extract_pitch_claims(
        pitch
    )

    return {
        "pitch": pitch,
        "claims": claims,
        "evidence": evidence,
    }


# ============================================================
# 12. BACKWARD-COMPATIBLE WRAPPER
# ============================================================

def create_pitch(
    client_context: Dict[str, Any],
    selected_insurers: List[str],
) -> Dict[str, Any]:
    """
    Backward-compatible wrapper used by the existing workflow.

    Keeping this function means workflow.py does not need to be
    changed immediately.

    Internally it now implements Objective 1.3 through
    generateMarketingPitch().
    """

    return generateMarketingPitch(
        client_context,
        selected_insurers,
    )

# ============================================================
# 13. ADVISOR PITCH REVISION
# ============================================================

REVISION_SYSTEM_PROMPT = """
You are the advisor-revision component of INSUREAI.

You will receive:

1. an existing insurance pitch;
2. advisor revision instructions;
3. policy evidence from the four supplied case-study documents.

Your task is to revise the pitch according to the advisor's
instructions while preserving factual grounding.

IMPORTANT RULES:

1. Follow the advisor's requested wording, structure or emphasis
   changes where possible.

2. Policy-specific factual statements must be supported ONLY by
   the supplied policy evidence.

3. Never invent:
   - benefits
   - coverage amounts
   - limits
   - percentages
   - waiting periods
   - exclusions
   - eligibility rules
   - policy conditions

4. Every policy-specific factual claim in insurer_comparison
   must remain atomic and contain:
   - one factual statement
   - exact source PDF filename
   - exact source page number

5. Do not convert assumptions into facts.

6. Do not invent new client requirements.

7. Do not introduce policy information from model memory or
   general insurance knowledge.

8. Keep the recommendation limited to the advisor-selected
   insurers.

9. If the advisor asks for a factual change that is not supported
   by the supplied evidence, do NOT fabricate it. Preserve the
   supported version or identify the issue in advisor_notes.

10. Return ONLY valid JSON using the same structure as the
    supplied existing pitch.

The revised pitch will be independently audited again after this
step, so do not assume that generated claims are automatically
trusted.
"""


def revisePitchContent(
    existing_pitch: Dict[str, Any],
    advisor_instructions: str,
    client_context: Dict[str, Any],
    selected_insurers: List[str],
) -> Dict[str, Any]:
    """
    Revise an existing INSUREAI pitch following human-advisor
    instructions.

    The revised pitch is NOT automatically trusted.

    After revision:
        1. factual policy claims are extracted again;
        2. the workflow independently retrieves evidence again;
        3. the audit layer verifies the revised claims again.

    This prevents advisor edits from bypassing the factual
    verification layer.
    """

    instructions = str(
        advisor_instructions
    ).strip()

    if not instructions:
        raise ValueError(
            "Advisor revision instructions are required."
        )

    selected_insurers = (
        validate_selected_insurers(
            selected_insurers
        )
    )

    if not existing_pitch:
        raise ValueError(
            "An existing pitch is required for revision."
        )

    # --------------------------------------------------------
    # Retrieve policy evidence again from the four supplied PDFs
    # --------------------------------------------------------

    evidence = retrieve_pitch_evidence(
        client_context,
        selected_insurers,
        top_k_per_insurer=2,
    )

    evidence_block = build_evidence_block(
        evidence
    )

    existing_pitch_block = json.dumps(
        existing_pitch,
        indent=2,
        ensure_ascii=False,
    )

    client_block = json.dumps(
        client_context,
        indent=2,
        ensure_ascii=False,
    )

    selected_block = json.dumps(
        selected_insurers,
        indent=2,
        ensure_ascii=False,
    )

    user_prompt = f"""
EXISTING PITCH:

{existing_pitch_block}


ADVISOR REVISION INSTRUCTIONS:

{instructions}


CLIENT CONTEXT:

{client_block}


SELECTED INSURERS:

{selected_block}


POLICY EVIDENCE FROM THE FOUR SUPPLIED CASE-STUDY DOCUMENTS:

{evidence_block}


Revise the existing pitch according to the advisor instructions.

Return the COMPLETE revised pitch, not only the changed section.

Remember:

- preserve the same JSON structure;
- use only supplied evidence for policy facts;
- every policy claim must remain atomic;
- every factual policy claim must include source filename and page;
- unsupported requested factual changes must not be invented;
- recommendation must remain within the selected insurers;
- the revised claims will be independently audited again.
"""

    client = get_groq_client()

    response = (
        client.chat.completions.create(
            model=GROQ_MODEL,
            response_format={
                "type": "json_object"
            },
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": REVISION_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )
    )

    content = (
        response.choices[0]
        .message.content
    )

    if not content:
        raise ValueError(
            "Pitch revision returned no content."
        )

    revised_pitch = json.loads(
        content
    )

    # Reapply all structural safeguards used during normal
    # generation.
    revised_pitch = normalise_pitch(
        revised_pitch,
        client_context,
        selected_insurers,
    )

    # Extract the factual policy claims again.
    revised_claims = extract_pitch_claims(
        revised_pitch
    )

    return {
        "pitch": revised_pitch,
        "claims": revised_claims,
        "evidence": evidence,
        "advisor_instructions": instructions,
    }