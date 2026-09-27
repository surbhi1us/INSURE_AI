from io import BytesIO
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# INSUREAI — AUDIT REPORT EXPORT
# ============================================================


def _safe(value: Any) -> str:
    """
    Convert values to display-safe strings for the PDF.
    """

    if value is None:
        return ""

    return str(value)


def _escape(value: Any) -> str:
    """
    Escape characters that ReportLab Paragraph treats as markup.
    """

    text = _safe(value)

    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _status_color(status: str):
    """
    Return a readable colour for each audit status.
    """

    status = status.upper()

    if status == "SUPPORTED":
        return colors.HexColor("#15803D")

    if status == "CONTRADICTED":
        return colors.HexColor("#B91C1C")

    if status == "UNSUPPORTED":
        return colors.HexColor("#B45309")

    return colors.HexColor("#A16207")


def generate_audit_pdf(
    workflow_result: Dict[str, Any],
) -> bytes:
    """
    Generate an INSUREAI claim-audit PDF from an already generated
    workflow result.

    Important:
    This function does NOT call Groq and does NOT rerun retrieval.
    It exports the exact audited result supplied to it.

    Returns:
        PDF file contents as bytes.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="INSUREAI Claim Audit Report",
        author="INSUREAI",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "InsureAITitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=27,
        textColor=colors.HexColor("#173B70"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "InsureAISubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
        alignment=TA_CENTER,
        spaceAfter=18,
    )

    heading_style = ParagraphStyle(
        "InsureAIHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#173B70"),
        spaceBefore=10,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "InsureAINormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )

    small_style = ParagraphStyle(
        "InsureAISmall",
        parent=normal_style,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748B"),
    )

    claim_style = ParagraphStyle(
        "InsureAIClaim",
        parent=normal_style,
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#173B70"),
    )

    story = []

    # ========================================================
    # HEADER
    # ========================================================

    story.append(
        Paragraph(
            "INSUREAI",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Evidence-Grounded Insurance Pitch — Claim Audit Report",
            subtitle_style,
        )
    )

    # ========================================================
    # CLIENT INFORMATION
    # ========================================================

    client = workflow_result.get("client", {})

    story.append(
        Paragraph(
            "Client Context",
            heading_style,
        )
    )

    client_rows = [
        [
            Paragraph("<b>Company</b>", normal_style),
            Paragraph(
                _escape(
                    client.get(
                        "company_name",
                        "Not provided",
                    )
                ),
                normal_style,
            ),
        ],
        [
            Paragraph("<b>Industry</b>", normal_style),
            Paragraph(
                _escape(
                    client.get("industry")
                    or "Not provided"
                ),
                normal_style,
            ),
        ],
        [
            Paragraph("<b>Workforce context</b>", normal_style),
            Paragraph(
                _escape(
                    client.get("workforce_context")
                    or "Not provided"
                ),
                normal_style,
            ),
        ],
    ]

    client_table = Table(
        client_rows,
        colWidths=[42 * mm, 118 * mm],
    )

    client_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#F1F5F9"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.HexColor("#E2E8F0"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(client_table)
    story.append(Spacer(1, 6 * mm))

    # ========================================================
    # AUDIT SUMMARY
    # ========================================================

    summary = workflow_result.get(
        "audit_summary",
        {},
    )

    total_claims = int(
        summary.get("total_claims", 0)
        or 0
    )

    supported = int(
        summary.get("supported", 0)
        or 0
    )

    needs_review = int(
        summary.get("needs_review", 0)
        or 0
    )

    contradicted = int(
        summary.get("contradicted", 0)
        or 0
    )

    unsupported = int(
        summary.get("unsupported", 0)
        or 0
    )

    verification_rate = (
        supported / total_claims
        if total_claims
        else 0
    )

    story.append(
        Paragraph(
            "Audit Summary",
            heading_style,
        )
    )

    summary_data = [
        [
            "Total claims",
            "Supported",
            "Needs review",
            "Unsupported",
            "Contradicted",
            "Verification rate",
        ],
        [
            str(total_claims),
            str(supported),
            str(needs_review),
            str(unsupported),
            str(contradicted),
            f"{verification_rate:.0%}",
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            26 * mm,
            26 * mm,
            28 * mm,
            28 * mm,
            28 * mm,
            32 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#173B70"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, 1),
                    "Helvetica-Bold",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7.5,
                ),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 6 * mm))

    # ========================================================
    # ADVISOR STATUS
    # ========================================================

    advisor_status = workflow_result.get(
        "advisor_status",
        "PENDING_REVIEW",
    )

    story.append(
        Paragraph(
            "Advisor Review",
            heading_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Status:</b> {_escape(advisor_status)}",
            normal_style,
        )
    )

    story.append(Spacer(1, 5 * mm))

    # ========================================================
    # CLAIM-BY-CLAIM AUDIT
    # ========================================================

    claims = workflow_result.get(
        "claims",
        [],
    )

    story.append(
        Paragraph(
            "Claim-by-Claim Evidence Audit",
            heading_style,
        )
    )

    if not claims:
        story.append(
            Paragraph(
                "No audited claims were supplied.",
                normal_style,
            )
        )

    for index, claim in enumerate(
        claims,
        start=1,
    ):

        status = _safe(
            claim.get(
                "status",
                "NEEDS_REVIEW",
            )
        ).upper()

        claim_text = _escape(
            claim.get(
                "claim",
                "No claim text provided.",
            )
        )

        source = _escape(
            claim.get(
                "source",
                "Unknown source",
            )
        )

        page = _escape(
            claim.get(
                "page",
                "—",
            )
        )

        reason = _escape(
            claim.get(
                "reason",
                "",
            )
        )

        evidence_quote = _escape(
            claim.get(
                "evidence_quote",
                "",
            )
        )

        similarity = claim.get(
            "retrieval_similarity"
        )

        if isinstance(
            similarity,
            (int, float),
        ):
            similarity_display = (
                f"{similarity:.0%}"
            )
        else:
            similarity_display = "—"

        citation_match = claim.get(
            "citation_match"
        )

        if citation_match is True:
            citation_display = "Yes"
        elif citation_match is False:
            citation_display = "No"
        else:
            citation_display = "—"

        status_style = ParagraphStyle(
            f"Status{index}",
            parent=normal_style,
            fontName="Helvetica-Bold",
            textColor=_status_color(status),
        )

        claim_header = Table(
            [
                [
                    Paragraph(
                        f"Claim {index}",
                        claim_style,
                    ),
                    Paragraph(
                        _escape(status),
                        status_style,
                    ),
                ]
            ],
            colWidths=[
                125 * mm,
                35 * mm,
            ],
        )

        claim_header.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor(
                            "#F8FAFC"
                        ),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor(
                            "#CBD5E1"
                        ),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (1, 0),
                        (1, 0),
                        "RIGHT",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ]
            )
        )

        detail_rows = [
            [
                Paragraph(
                    "<b>Generated claim</b>",
                    small_style,
                ),
                Paragraph(
                    claim_text,
                    normal_style,
                ),
            ],
            [
                Paragraph(
                    "<b>Source</b>",
                    small_style,
                ),
                Paragraph(
                    f"{source} — page {page}",
                    normal_style,
                ),
            ],
            [
                Paragraph(
                    "<b>Citation match</b>",
                    small_style,
                ),
                Paragraph(
                    citation_display,
                    normal_style,
                ),
            ],
            [
                Paragraph(
                    "<b>Retrieval similarity</b>",
                    small_style,
                ),
                Paragraph(
                    similarity_display,
                    normal_style,
                ),
            ],
            [
                Paragraph(
                    "<b>Evidence</b>",
                    small_style,
                ),
                Paragraph(
                    evidence_quote
                    or "No evidence quote supplied.",
                    normal_style,
                ),
            ],
            [
                Paragraph(
                    "<b>Audit reason</b>",
                    small_style,
                ),
                Paragraph(
                    reason
                    or "No audit reason supplied.",
                    normal_style,
                ),
            ],
        ]

        detail_table = Table(
            detail_rows,
            colWidths=[
                38 * mm,
                122 * mm,
            ],
        )

        detail_table.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor(
                            "#CBD5E1"
                        ),
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.25,
                        colors.HexColor(
                            "#E2E8F0"
                        ),
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.HexColor(
                            "#F8FAFC"
                        ),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(
            KeepTogether(
                [
                    claim_header,
                    detail_table,
                    Spacer(1, 5 * mm),
                ]
            )
        )

    # ========================================================
    # FOOTER NOTE
    # ========================================================

    story.append(Spacer(1, 4 * mm))

    story.append(
        Paragraph(
            (
                "<b>Review note:</b> This report records the evidence "
                "verification performed by the INSUREAI prototype. "
                "Policy claims should be reviewed against official policy "
                "wordings before external client use."
            ),
            small_style,
        )
    )

    document.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes