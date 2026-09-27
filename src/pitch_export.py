from io import BytesIO



from pathlib import Path



from typing import Any, Dict, List, Optional



import re







from pptx import Presentation



from pptx.util import Inches, Pt











# ============================================================



# PATHS



# ============================================================







PROJECT_ROOT = Path(__file__).resolve().parent.parent







TEMPLATE_PATH = (



    PROJECT_ROOT



    / "templates"



    / "INSUREAI_Client_Pitch_Template.pptx"



)











# ============================================================



# BASIC HELPERS



# ============================================================







def _clean(value: Any) -> str:



    """



    Convert a value into clean single-spaced text suitable



    for a client-facing PowerPoint.



    """







    if value is None:



        return ""







    text = str(value)







    text = text.replace("\r", " ")



    text = text.replace("\n", " ")







    return " ".join(text.split()).strip()











def _shorten(



    value: Any,



    max_chars: int,



    fallback: str = "Not established from available evidence.",



) -> str:



    """



    Shorten long generated text without cutting through a word.



    """







    text = _clean(value)







    if not text:



        return fallback







    if len(text) <= max_chars:



        return text







    shortened = text[: max_chars - 1].rsplit(



        " ",



        1,



    )[0]







    return shortened.rstrip(" ,.;:-") + "…"











def _as_list(value: Any) -> List[Any]:



    if isinstance(value, list):



        return value







    return []











def _first_non_empty(*values: Any) -> str:



    for value in values:



        text = _clean(value)







        if text:



            return text







    return ""











def _normalise_name(value: Any) -> str:



    return re.sub(



        r"[^a-z0-9]+",



        "",



        _clean(value).lower(),



    )











def _display_policy_name(value: Any) -> str:



    """



    Convert internal insurer labels into clean client-facing



    policy/insurer names where possible.



    """







    text = _clean(value)







    if not text:



        return "Policy"







    aliases = {



        "hdfc": "HDFC ERGO",



        "hdfcergo": "HDFC ERGO",



        "abhi": "Aditya Birla Health Insurance",



        "adityabirla": "Aditya Birla Health Insurance",



        "adityabirlahealthinsurance":



            "Aditya Birla Health Insurance",



        "care": "Care Health Insurance",



        "carehealth": "Care Health Insurance",



        "carehealthinsurance":



            "Care Health Insurance",



        "nivabupa": "Niva Bupa",



        "niva": "Niva Bupa",



    }







    key = _normalise_name(text)







    return aliases.get(



        key,



        text,



    )











def _status_supported(value: Any) -> bool:



    return _clean(value).upper() == "SUPPORTED"











# ============================================================



# TEMPLATE VALIDATION



# ============================================================







def _validate_template(prs: Presentation) -> None:



    if not TEMPLATE_PATH.exists():



        raise FileNotFoundError(



            f"PowerPoint template not found: {TEMPLATE_PATH}"



        )







    if len(prs.slides) != 5:



        raise ValueError(



            "INSUREAI client template must contain exactly "



            f"5 slides. Found {len(prs.slides)}."



        )











# ============================================================



# TEXT REPLACEMENT



# ============================================================







def _replace_in_text_frame(



    text_frame,



    replacements: Dict[str, str],



) -> None:



    """



    Replace placeholders while preserving the existing



    paragraph/run formatting as much as possible.







    Important:



    We do NOT clear and rebuild every textbox because doing so



    destroys the template's human-designed formatting.



    """







    for paragraph in text_frame.paragraphs:







        # First try run-level replacement. This preserves



        # formatting when the placeholder lives in one run.



        for run in paragraph.runs:



            original = run.text



            updated = original







            for token, value in replacements.items():



                if token in updated:



                    updated = updated.replace(



                        token,



                        value,



                    )







            if updated != original:



                run.text = updated







        # Some PowerPoint placeholders can be split across



        # multiple runs. Handle that case carefully.



        paragraph_text = "".join(



            run.text



            for run in paragraph.runs



        )







        matching_tokens = [



            token



            for token in replacements



            if token in paragraph_text



        ]







        if matching_tokens:



            updated = paragraph_text







            for token in matching_tokens:



                updated = updated.replace(



                    token,



                    replacements[token],



                )







            if paragraph.runs:



                paragraph.runs[0].text = updated







                for run in paragraph.runs[1:]:



                    run.text = ""











def _replace_shape_text(



    shape,



    replacements: Dict[str, str],



) -> None:







    if getattr(shape, "has_text_frame", False):



        _replace_in_text_frame(



            shape.text_frame,



            replacements,



        )







    # Grouped shapes.



    if hasattr(shape, "shapes"):



        for child in shape.shapes:



            _replace_shape_text(



                child,



                replacements,



            )











def _replace_slide_text(



    slide,



    replacements: Dict[str, str],



) -> None:







    for shape in slide.shapes:



        _replace_shape_text(



            shape,



            replacements,



        )











# ============================================================



# FIND / REPLACE EXACT TEXT SHAPES



# ============================================================







def _shape_text(shape) -> str:



    if not getattr(



        shape,



        "has_text_frame",



        False,



    ):



        return ""







    return _clean(shape.text)











def _replace_exact_shape(



    slide,



    target: str,



    value: str,



) -> bool:



    """



    Replace a whole textbox whose text exactly matches target.







    Useful for Slide 3 because [BENEFIT] occurs multiple times.



    """







    for shape in slide.shapes:







        if _shape_text(shape) == target:



            if shape.text_frame.paragraphs:



                paragraph = (



                    shape.text_frame.paragraphs[0]



                )







                if paragraph.runs:



                    paragraph.runs[0].text = value







                    for run in paragraph.runs[1:]:



                        run.text = ""



                else:



                    paragraph.text = value







                return True







    return False











def _find_shapes_with_exact_text(



    slide,



    target: str,



) -> List[Any]:







    matches = []







    for shape in slide.shapes:



        if _shape_text(shape) == target:



            matches.append(shape)







    return matches











def _set_shape_text(



    shape,



    value: str,



) -> None:







    if not getattr(



        shape,



        "has_text_frame",



        False,



    ):



        return







    paragraphs = shape.text_frame.paragraphs







    if not paragraphs:



        shape.text = value



        return







    paragraph = paragraphs[0]







    if paragraph.runs:



        paragraph.runs[0].text = value







        for run in paragraph.runs[1:]:



            run.text = ""



    else:



        paragraph.text = value











# ============================================================



# DATA EXTRACTION



# ============================================================







def _get_company_data(



    workflow_result: Dict[str, Any],



) -> Dict[str, Any]:







    client = workflow_result.get(



        "client",



        {},



    ) or {}







    profile = workflow_result.get(



        "company_profile",



        {},



    ) or {}







    company = _first_non_empty(



        profile.get("company"),



        profile.get("company_name"),



        client.get("company_name"),



        "Client",



    )







    industry = _first_non_empty(



        profile.get("industry"),



        client.get("industry"),



        "Not established",



    )







    company_size = _first_non_empty(



        profile.get("company_size"),



        client.get("company_size"),



        "Not established",



    )







    workforce = _first_non_empty(



        client.get("workforce_context"),



        profile.get("workforce_context"),



        profile.get("company_overview"),



        client.get("company_overview"),



        "Workforce profile requires advisor confirmation.",



    )







    risks = (



        _as_list(profile.get("key_risks"))



        or _as_list(client.get("key_risks"))



    )







    clean_risks = []







    for risk in risks:



        text = _shorten(



            risk,



            115,



            "",



        )







        if text:



            clean_risks.append(text)







    while len(clean_risks) < 4:



        clean_risks.append(



            "Requires advisor confirmation."



        )







    return {



        "company": _shorten(



            company,



            65,



            "Client",



        ),



        "industry": _shorten(



            industry,



            55,



            "Not established",



        ),



        "company_size": _shorten(



            company_size,



            45,



            "Not established",



        ),



        "workforce": _shorten(



            workforce,



            115,



            "Requires advisor confirmation.",



        ),



        "risks": clean_risks[:4],



    }











def _get_recommendation(



    workflow_result: Dict[str, Any],



) -> Dict[str, Any]:







    pitch = workflow_result.get(



        "pitch",



        {},



    ) or {}







    recommendation = pitch.get(



        "recommended_policy",



        {},



    ) or {}







    return recommendation











def _get_recommended_name(



    workflow_result: Dict[str, Any],



) -> str:







    recommendation = _get_recommendation(



        workflow_result



    )







    return _display_policy_name(



        _first_non_empty(



            recommendation.get(



                "policy_name"



            ),



            recommendation.get(



                "product"



            ),



            recommendation.get(



                "insurer"



            ),



            "Advisor review required",



        )



    )











def _get_supported_selling_points(



    workflow_result: Dict[str, Any],



) -> List[str]:



    """



    Export only selling points that the workflow has linked to



    SUPPORTED audit evidence.







    If audit linkage is absent, do not silently present the



    generated statement as verified.



    """







    recommendation = _get_recommendation(



        workflow_result



    )







    raw_points = _as_list(



        recommendation.get(



            "selling_points"



        )



    )







    points = []







    for item in raw_points:







        if not isinstance(



            item,



            dict,



        ):



            continue







        status = item.get(



            "audit_status"



        )







        verified = item.get(



            "audit_verified"



        )







        if (



            verified is True



            or _status_supported(status)



        ):



            benefit = _first_non_empty(



                item.get("benefit"),



                item.get("claim"),



                item.get("text"),



            )







            relevance = _first_non_empty(



                item.get(



                    "client_relevance"



                ),



                item.get(



                    "relevance"



                ),



            )







            if benefit:



                if relevance:



                    text = (



                        f"{benefit} — {relevance}"



                    )



                else:



                    text = benefit







                points.append(



                    _shorten(



                        text,



                        145,



                        "",



                    )



                )







    # If explicit selling points were not linked, fall back to



    # independently audited SUPPORTED claims belonging to the



    # recommended policy.



    if not points:







        recommended_name = (



            _get_recommended_name(



                workflow_result



            )



        )







        recommended_key = (



            _normalise_name(



                recommended_name



            )



        )







        for claim in _as_list(



            workflow_result.get(



                "claims"



            )



        ):







            if not isinstance(



                claim,



                dict,



            ):



                continue







            if not _status_supported(



                claim.get("status")



            ):



                continue







            source = _normalise_name(



                claim.get("source")



            )







            # Prefer claims whose source appears associated



            # with the recommended insurer. If naming is too



            # different, still allow supported claims later.



            claim_text = _clean(



                claim.get("claim")



            )







            if not claim_text:



                continue







            if (



                recommended_key



                and (



                    recommended_key in source



                    or source in recommended_key



                )



            ):



                points.append(



                    _shorten(



                        claim_text,



                        145,



                        "",



                    )



                )







    if not points:



        points.append(



            "No policy benefit has yet been independently "



            "verified for client presentation."



        )







    while len(points) < 3:



        points.append(



            "Additional policy detail requires advisor review."



        )







    return points[:3]











def _get_policy_snapshot(workflow_result: Dict[str, Any]) -> Dict[str, str]:
    recommendation = _get_recommendation(workflow_result)
    snapshot = recommendation.get("policy_snapshot", {}) or {}
    recommended_key = _normalise_name(_get_recommended_name(workflow_result))

    verified = []
    for claim in _as_list(workflow_result.get("claims")):
        if not isinstance(claim, dict) or not _status_supported(claim.get("status")):
            continue
        text = _clean(claim.get("claim"))
        source = _normalise_name(claim.get("source"))
        if text and (not recommended_key or not source or recommended_key in source or source in recommended_key):
            verified.append(text)

    def explicit(*keys, max_chars=70):
        for key in keys:
            v = _clean(snapshot.get(key))
            if v and not (v.startswith("[") and v.endswith("]")) and "requires review" not in v.lower():
                return _shorten(v, max_chars, "")
        return ""

    def audited(groups, max_chars=70):
        for text in verified:
            low = text.lower()
            for group in groups:
                if all(k in low for k in group):
                    return _shorten(text, max_chars, "")
        return ""

    hospital = explicit("hospitalisation", "hospitalization", max_chars=70) or audited([
        ("hospitalisation",), ("hospitalization",), ("pre-hospitalisation",), ("post-hospitalisation",)
    ])
    waiting = explicit("waiting_period", "waiting", max_chars=70) or audited([("waiting period",)])
    other = explicit("other_key_benefit", "other_benefit", "key_benefit", max_chars=70) or audited([
        ("air-ambulance",), ("air ambulance",), ("shared accommodation",), ("daily cash",)
    ])

    return {
        "sum_insured": explicit("sum_insured", "coverage", "coverage_amount", max_chars=55) or "Requires advisor review",
        "premium": explicit("premium", "premium_details", "price", max_chars=55) or "Subject to quotation",
        "policy_term": explicit("policy_term", "term", "duration", max_chars=55) or "Requires advisor review",
        "hospitalisation": hospital or "Requires advisor review",
        "waiting_period": waiting or "Requires advisor review",
        "other_benefit": other or "Requires advisor review",
    }



def _get_workforce_relevance(workflow_result: Dict[str, Any]) -> List[Dict[str, str]]:
    recommendation = _get_recommendation(workflow_result)
    result = []
    for item in _as_list(recommendation.get("workforce_relevance")):
        if not isinstance(item, dict):
            continue
        group = _first_non_empty(item.get("employee_group"), item.get("group"), "Employees")
        rel = _first_non_empty(item.get("policy_relevance"), item.get("relevance"), item.get("potential_need"), item.get("benefit"), item.get("reason"))
        if rel:
            result.append({"group": _shorten(group, 32, "Employees"), "relevance": _shorten(rel, 90, "Advisor review")})
    if not result:
        points = _get_supported_selling_points(workflow_result)
        for point in points:
            if "additional policy detail" in point.lower() or "no policy benefit" in point.lower():
                continue
            low = point.lower()
            if "air ambulance" in low or "air-ambulance" in low:
                group = "Remote / mobile staff"
            elif "shared accommodation" in low or "daily cash" in low:
                group = "Hospitalised employees"
            else:
                group = "Covered employees"
            result.append({"group": group, "relevance": _shorten(point, 90, "Advisor review")})
    defaults = [
        {"group": "Operational employees", "relevance": "Review applicability against final policy terms."},
        {"group": "Office employees", "relevance": "Review applicability against final policy terms."},
        {"group": "Mixed workforce", "relevance": "Final suitability requires advisor review."},
    ]
    while len(result) < 3:
        result.append(defaults[len(result)])
    return result[:3]



def _get_comparison_entries(



    workflow_result: Dict[str, Any],



) -> List[Dict[str, Any]]:







    pitch = workflow_result.get(



        "pitch",



        {},



    ) or {}







    entries = _as_list(



        pitch.get(



            "insurer_comparison"



        )



    )







    return [



        item



        for item in entries



        if isinstance(item, dict)



    ]











def _entry_name(



    entry: Dict[str, Any],



) -> str:







    return _display_policy_name(



        _first_non_empty(



            entry.get("policy_name"),



            entry.get("product"),



            entry.get("insurer"),



            "Policy",



        )



    )











def _entry_benefits(entry: Dict[str, Any], workflow_result: Optional[Dict[str, Any]] = None) -> List[str]:
    benefits = []
    for key in ("claims", "benefits"):
        for item in _as_list(entry.get(key)):
            if isinstance(item, dict):
                text = _first_non_empty(item.get("claim"), item.get("benefit"), item.get("text"))
            else:
                text = _clean(item)
            if text:
                text = _shorten(text, 88, "")
                if text and text not in benefits:
                    benefits.append(text)
    if len(benefits) < 2 and workflow_result:
        entry_key = _normalise_name(_entry_name(entry))
        for claim in _as_list(workflow_result.get("claims")):
            if not isinstance(claim, dict) or not _status_supported(claim.get("status")):
                continue
            text = _clean(claim.get("claim"))
            source = _normalise_name(claim.get("source"))
            if text and source and (entry_key in source or source in entry_key):
                text = _shorten(text, 88, "")
                if text not in benefits:
                    benefits.append(text)
            if len(benefits) >= 2:
                break
    if not benefits:
        rel = _clean(entry.get("relevance"))
        if rel:
            benefits.append(_shorten(rel, 88, ""))
    while len(benefits) < 2:
        benefits.append("Review policy terms for additional benefits.")
    return benefits[:2]



def _entry_consideration(



    entry: Dict[str, Any],



) -> str:







    return _shorten(



        _first_non_empty(



            entry.get(



                "client_consideration"



            ),



            entry.get(



                "tradeoff"



            ),



            entry.get(



                "reason_not_recommended"



            ),



            entry.get(



                "why_not_recommended"



            ),



            entry.get(



                "relevance"



            ),



        ),



        150,



        (



            "Consider alongside the recommended option after "



            "reviewing terms, exclusions and insurer quotation."



        ),



    )











def _ordered_policies(



    workflow_result: Dict[str, Any],



) -> List[Dict[str, Any]]:



    """



    Recommended policy first, followed by the remaining



    comparison policies.



    """







    entries = _get_comparison_entries(



        workflow_result



    )







    recommended = _get_recommended_name(



        workflow_result



    )







    recommended_key = (



        _normalise_name(



            recommended



        )



    )







    first = []



    rest = []







    for entry in entries:



        name_key = _normalise_name(



            _entry_name(entry)



        )







        if (



            recommended_key



            and (



                name_key == recommended_key



                or name_key in recommended_key



                or recommended_key in name_key



            )



        ):



            first.append(entry)



        else:



            rest.append(entry)







    ordered = first + rest







    # If the recommended insurer wasn't present in comparison,



    # insert a minimal entry so Slide 4 still starts with it.



    if not first and recommended:



        ordered.insert(



            0,



            {



                "insurer": recommended,



                "claims": [],



                "relevance": (



                    _get_recommendation(



                        workflow_result



                    ).get(



                        "rationale",



                        "",



                    )



                ),



            },



        )







    return ordered[:4]












# ============================================================
# ROBUST POWERPOINT TOKEN HELPERS
# ============================================================

def _set_text_frame_text(text_frame, value: str) -> None:
    """Set a text frame's text while keeping the first run's formatting."""
    paragraphs = text_frame.paragraphs
    if not paragraphs:
        text_frame.text = value
        return
    first = paragraphs[0]
    if first.runs:
        first.runs[0].text = value
        for run in first.runs[1:]:
            run.text = ""
    else:
        first.text = value
    # Clear any extra paragraphs so old template text cannot remain.
    for paragraph in paragraphs[1:]:
        for run in paragraph.runs:
            run.text = ""
        if not paragraph.runs:
            paragraph.text = ""


def _iter_text_targets(shape):
    """Yield every text frame inside a shape, including groups and tables."""
    if getattr(shape, "has_text_frame", False):
        yield shape.text_frame
    if getattr(shape, "has_table", False):
        for row in shape.table.rows:
            for cell in row.cells:
                yield cell.text_frame
    if hasattr(shape, "shapes"):
        for child in shape.shapes:
            yield from _iter_text_targets(child)


def _replace_token_in_text_frame(text_frame, token: str, value: str) -> bool:
    """Replace a token even when PowerPoint split it across multiple runs."""
    changed = False
    for paragraph in text_frame.paragraphs:
        if paragraph.runs:
            full = "".join(run.text for run in paragraph.runs)
        else:
            full = paragraph.text
        if token not in full:
            continue
        updated = full.replace(token, value)
        if paragraph.runs:
            paragraph.runs[0].text = updated
            for run in paragraph.runs[1:]:
                run.text = ""
        else:
            paragraph.text = updated
        changed = True
    return changed


def _replace_token_anywhere(slide, token: str, value: str) -> None:
    """Replace token in normal shapes, grouped shapes, and table cells."""
    for shape in slide.shapes:
        for text_frame in _iter_text_targets(shape):
            _replace_token_in_text_frame(text_frame, token, value)


def _find_token_targets(slide, token: str) -> List[Any]:
    """Find text frames containing token, returned in visual top/left order."""
    found = []

    def walk(shape, inherited_left=0, inherited_top=0):
        left = inherited_left + int(getattr(shape, "left", 0) or 0)
        top = inherited_top + int(getattr(shape, "top", 0) or 0)
        if getattr(shape, "has_text_frame", False) and token in shape.text_frame.text:
            found.append((top, left, shape.text_frame))
        if getattr(shape, "has_table", False):
            for r_idx, row in enumerate(shape.table.rows):
                for c_idx, cell in enumerate(row.cells):
                    if token in cell.text_frame.text:
                        found.append((top + r_idx, left + c_idx, cell.text_frame))
        if hasattr(shape, "shapes"):
            for child in shape.shapes:
                walk(child, left, top)

    for shape in slide.shapes:
        walk(shape)
    found.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in found]

# ============================================================



# SLIDE 1



# ============================================================







def _populate_slide_1(



    slide,



    workflow_result: Dict[str, Any],



) -> None:







    company = _get_company_data(



        workflow_result



    )







    replacements = {



        "[COMPANY_NAME]":



            company["company"],







        "[INDUSTRY]":



            company["industry"],







        "[COMPANY_SIZE]":



            company["company_size"],







        "[WORKFORCE_CONTEXT]":



            company["workforce"],







        "[RISK_1]":



            company["risks"][0],







        "[RISK_2]":



            company["risks"][1],







        "[RISK_3]":



            company["risks"][2],







        "[RISK_4]":



            company["risks"][3],



    }







    _replace_slide_text(



        slide,



        replacements,



    )











# ============================================================



# SLIDE 2



# ============================================================







def _populate_slide_2(slide, workflow_result: Dict[str, Any]) -> None:
    company = _get_company_data(workflow_result)
    recommended = _get_recommended_name(workflow_result)
    selling = _get_supported_selling_points(workflow_result)
    snapshot = _get_policy_snapshot(workflow_result)
    workforce = _get_workforce_relevance(workflow_result)

    values = {
        "[RECOMMENDED_POLICY]": _shorten(recommended, 55, "Advisor review required"),
        "[COMPANY_NAME]": company["company"],
        "[SELLING_POINT_1]": selling[0], "[SELLING_POINT_2]": selling[1], "[SELLING_POINT_3]": selling[2],
        "[SUM_INSURED]": snapshot["sum_insured"], "[PREMIUM]": snapshot["premium"],
        "[POLICY_TERM]": snapshot["policy_term"], "[HOSPITALISATION]": snapshot["hospitalisation"],
        "[WAITING_PERIOD]": snapshot["waiting_period"], "[OTHER_KEY_BENEFIT]": snapshot["other_benefit"],
        "[EMPLOYEE_GROUP_1]": workforce[0]["group"], "[EMPLOYEE_GROUP_2]": workforce[1]["group"], "[EMPLOYEE_GROUP_3]": workforce[2]["group"],
    }
    for token, value in values.items():
        _replace_token_anywhere(slide, token, value)

    # Replace the three repeated relevance tokens in visual order.
    rel_targets = _find_token_targets(slide, "[RELEVANCE]")
    for i, tf in enumerate(rel_targets[:3]):
        full = tf.text
        _set_text_frame_text(tf, full.replace("[RELEVANCE]", workforce[i]["relevance"]))



def _populate_snapshot_values(



    slide,



    snapshot: Dict[str, str],



) -> None:



    """



    Template variants may have labels like 'Sum Insured' with



    the value textbox positioned underneath rather than a



    named placeholder. We therefore support both explicit



    placeholders and nearby value boxes.



    """







    explicit = {



        "[SUM_INSURED]":



            snapshot["sum_insured"],







        "[PREMIUM]":



            snapshot["premium"],







        "[POLICY_TERM]":



            snapshot["policy_term"],







        "[HOSPITALISATION]":



            snapshot["hospitalisation"],







        "[WAITING_PERIOD]":



            snapshot["waiting_period"],







        "[OTHER_KEY_BENEFIT]":



            snapshot["other_benefit"],



    }







    _replace_slide_text(



        slide,



        explicit,



    )







    label_values = {



        "Sum Insured":



            snapshot["sum_insured"],







        "Premium":



            snapshot["premium"],







        "Policy Term":



            snapshot["policy_term"],







        "Hospitalisation":



            snapshot["hospitalisation"],







        "Waiting Period":



            snapshot["waiting_period"],







        "Other Key Benefit":



            snapshot["other_benefit"],



    }







    text_shapes = [



        shape



        for shape in slide.shapes



        if getattr(



            shape,



            "has_text_frame",



            False,



        )



    ]







    for label, value in (



        label_values.items()



    ):







        label_shape = None







        for shape in text_shapes:



            if _shape_text(shape) == label:



                label_shape = shape



                break







        if label_shape is None:



            continue







        candidates = []







        label_bottom = (



            label_shape.top



            + label_shape.height



        )







        for shape in text_shapes:







            if shape is label_shape:



                continue







            text = _shape_text(shape)







            # Don't overwrite other labels.



            if text in label_values:



                continue







            # Candidate should be close to label horizontally.



            horizontal_distance = abs(



                shape.left



                - label_shape.left



            )







            vertical_distance = (



                shape.top



                - label_bottom



            )







            if (



                horizontal_distance



                < label_shape.width * 1.5



                and



                -100000



                <= vertical_distance



                <= 900000



            ):



                # The template may already contain fallback text such as



                # "Requires review" or "[VALUE / Subject to quotation]".



                # These are still value boxes and must be overwritten.







                lower_text = text.lower()







                if not text:



                    priority = -3



                elif (



                    text.startswith("[")



                    and text.endswith("]")



                ):



                    priority = -2



                elif lower_text in {



                    "requires review",



                    "advisor review",



                    "advisor review required",



                    "not established",



                    "not established in supplied policy evidence",



                    "[value / subject to quotation]",



                }:



                    priority = -1



                else:



                    continue







                candidates.append(



                    (



                        priority,



                        abs(vertical_distance),



                        horizontal_distance,



                        shape,



                    )



                )







        if candidates:



            candidates.sort(



                key=lambda item: (



                    item[0],



                    item[1],



                    item[2],



                )



            )







            _set_shape_text(



                candidates[0][3],



                value,



            )











# ============================================================



# SLIDE 3



# ============================================================







def _populate_slide_3(slide, workflow_result: Dict[str, Any]) -> None:
    recommended = _normalise_name(_get_recommended_name(workflow_result))
    alternatives = []
    for entry in _get_comparison_entries(workflow_result):
        key = _normalise_name(_entry_name(entry))
        if recommended and (key == recommended or key in recommended or recommended in key):
            continue
        alternatives.append(entry)
    alternatives = alternatives[:3]

    # Policy headings.
    for i, token in enumerate(("[POLICY_2]", "[POLICY_3]", "[POLICY_4]")):
        value = _shorten(_entry_name(alternatives[i]), 48, "Policy") if i < len(alternatives) else ""
        _replace_token_anywhere(slide, token, value)

    # Benefits: find every text frame containing BENEFIT, including groups/tables.
    benefit_targets = _find_token_targets(slide, "[BENEFIT]")
    benefit_values = []
    for entry in alternatives:
        b = _entry_benefits(entry, workflow_result)
        benefit_values.extend([f"• {b[0]}", f"• {b[1]}"])
    for i, tf in enumerate(benefit_targets):
        value = benefit_values[i] if i < len(benefit_values) else ""
        _set_text_frame_text(tf, value)

    consideration_targets = _find_token_targets(slide, "[WHY_NOT_RECOMMENDED]")
    for i, tf in enumerate(consideration_targets):
        value = _entry_consideration(alternatives[i]) if i < len(alternatives) else ""
        _set_text_frame_text(tf, value)

    # For unused cards, also remove their static labels so blank cards look intentionally empty.
    # We identify cards by horizontal thirds and clear text frames in unused card regions,
    # while preserving the slide title.
    if len(alternatives) < 3:
        # Card centers in the supplied template are roughly left/middle/right.
        all_tfs = []
        for shape in slide.shapes:
            for tf in _iter_text_targets(shape):
                all_tfs.append((getattr(shape, "left", 0), getattr(shape, "top", 0), tf))
        xs = sorted({x for x, y, tf in all_tfs if y > Inches(1.2) and _clean(tf.text)})
        # Static labels are cleared only if their containing region has no alternative.
        if xs:
            slide_width = max((getattr(sh, "left", 0) + getattr(sh, "width", 0) for sh in slide.shapes), default=Inches(10))
            for x, y, tf in all_tfs:
                if y <= Inches(1.2):
                    continue
                card_index = min(2, int((x / max(1, slide_width)) * 3))
                if card_index >= len(alternatives):
                    txt = _clean(tf.text)
                    if txt in {"Key documented benefits", "Client consideration"}:
                        _set_text_frame_text(tf, "")



def _get_client_needs(



    workflow_result: Dict[str, Any],



) -> List[str]:







    pitch = workflow_result.get(



        "pitch",



        {},



    ) or {}







    needs = []







    for need in _as_list(



        pitch.get(



            "client_needs"



        )



    ):



        text = _shorten(



            need,



            48,



            "",



        )







        if text:



            needs.append(text)







    # Add company risks when the model generated fewer than



    # four client needs.



    company = _get_company_data(



        workflow_result



    )







    for risk in company["risks"]:



        if len(needs) >= 4:



            break







        if (



            risk



            and risk not in needs



            and "advisor confirmation"



            not in risk.lower()



        ):



            needs.append(



                _shorten(



                    risk,



                    48,



                    "",



                )



            )







    defaults = [



        "Hospitalisation support",



        "Workforce relevance",



        "Coverage flexibility",



        "Identified client risks",



    ]







    for default in defaults:



        if len(needs) >= 4:



            break







        if default not in needs:



            needs.append(default)







    return needs[:4]











def _policy_cell_text(



    entry: Dict[str, Any],



    row_index: int,



) -> str:



    """



    Very compact comparison-table wording.







    Slide 4 is an executive comparison, not the detailed



    evidence slide. Keep every cell deliberately short.



    """







    benefits = _entry_benefits(



        entry



    )







    relevance = _clean(



        entry.get("relevance")



    )







    if row_index == 0:



        return _shorten(



            benefits[0],



            22,



            "See policy terms",



        )







    if row_index == 1:



        return _shorten(



            benefits[1],



            22,



            "See policy terms",



        )







    if row_index == 2:



        return _shorten(



            relevance,



            22,



            "Advisor review",



        )







    return _shorten(



        _first_non_empty(



            entry.get("client_consideration"),



            relevance,



        ),



        22,



        "Advisor review",



    )











def _policy_limitation(



    entry: Dict[str, Any],



) -> str:







    limitations = _as_list(



        entry.get("limitations")



    )







    if limitations:



        return _shorten(



            limitations[0],



            24,



            "Review full terms",



        )







    return "Review terms & exclusions"











def _populate_slide_4(



    slide,



    workflow_result: Dict[str, Any],



) -> None:







    needs = _get_client_needs(



        workflow_result



    )







    policies = _ordered_policies(



        workflow_result



    )







    # Use only policies actually selected by the advisor.



    policies = policies[:4]







    table_shape = None







    for shape in slide.shapes:



        if getattr(



            shape,



            "has_table",



            False,



        ):



            table_shape = shape



            break







    if table_shape is None:



        # Still populate NEED tokens if a template variant



        # doesn't contain an actual PowerPoint table.



        _replace_slide_text(



            slide,



            {



                "[NEED_1]": needs[0],



                "[NEED_2]": needs[1],



                "[NEED_3]": needs[2],



                "[NEED_4]": needs[3],



            },



        )



        return







    table = table_shape.table







    # Expected:



    #



    # row 0: header



    # row 1-4: needs



    # row 5: limitation



    #



    # col 0: row labels



    # col 1-4: policies







    if (



        len(table.rows) < 6



        or len(table.columns) < 5



    ):



        raise ValueError(



            "Slide 4 comparison table must contain at least "



            "6 rows and 5 columns."



        )







    # Header.



    table.cell(



        0,



        0,



    ).text = "Client Consideration"







    for column_index, entry in enumerate(



        policies,



        start=1,



    ):



        table.cell(



            0,



            column_index,



        ).text = _shorten(



            _entry_name(entry),



            30,



            "Policy",



        )







    # Clear unused template policy columns (e.g. Policy C / Policy D).
    for column_index in range(1 + len(policies), len(table.columns)):
        for row_index in range(len(table.rows)):
            table.cell(row_index, column_index).text = ""

    # Need rows.



    for row_index in range(4):







        table.cell(



            row_index + 1,



            0,



        ).text = needs[



            row_index



        ]







        for column_index, entry in enumerate(



            policies,



            start=1,



        ):



            table.cell(



                row_index + 1,



                column_index,



            ).text = (



                _policy_cell_text(



                    entry,



                    row_index,



                )



            )







    # Limitation row.



    table.cell(



        5,



        0,



    ).text = "Key limitation"







    for column_index, entry in enumerate(



        policies,



        start=1,



    ):



        table.cell(



            5,



            column_index,



        ).text = (



            _policy_limitation(



                entry



            )



        )







    _format_comparison_table(



        table



    )



    # Explicitly control the table's position.



    # Do not allow generated content to push the table into



    # the lower recommendation area.



    table_shape.left = Inches(0.45)



    table_shape.top = Inches(1.10)



    table_shape.width = Inches(9.10)



    table_shape.height = Inches(2.45)











def _format_comparison_table(



    table,



) -> None:



    """



    Format the Slide 4 comparison table so it remains compact



    and fits inside the fixed PowerPoint template.







    IMPORTANT:



    - Row heights are fixed.



    - Font sizes are deliberately small.



    - PowerPoint is not allowed to resize cells based on text.



    - The table is intended as an executive summary, not a



      detailed policy wording page.



    """







    # --------------------------------------------------------



    # FIXED ROW HEIGHTS



    # --------------------------------------------------------







    # Header



    table.rows[0].height = Inches(0.30)







    # Four comparison rows



    table.rows[1].height = Inches(0.40)



    table.rows[2].height = Inches(0.40)



    table.rows[3].height = Inches(0.40)



    table.rows[4].height = Inches(0.40)







    # Limitation row



    table.rows[5].height = Inches(0.38)







    # --------------------------------------------------------



    # CELL FORMATTING



    # --------------------------------------------------------







    for row_index, row in enumerate(table.rows):







        for column_index, cell in enumerate(row.cells):







            text_frame = cell.text_frame







            # Do not allow PowerPoint to automatically enlarge



            # the text box/table based on its contents.



            text_frame.auto_size = None



            text_frame.word_wrap = True







            # Compact margins.



            text_frame.margin_left = Inches(0.055)



            text_frame.margin_right = Inches(0.055)



            text_frame.margin_top = Inches(0.025)



            text_frame.margin_bottom = Inches(0.025)







            for paragraph in text_frame.paragraphs:







                paragraph.space_before = Pt(0)



                paragraph.space_after = Pt(0)







                # Keep line spacing compact.



                paragraph.line_spacing = 0.88







                for run in paragraph.runs:







                    if row_index == 0:



                        # Column headings.



                        run.font.size = Pt(7.5)



                        run.font.bold = True







                    elif column_index == 0:



                        # Client consideration labels.



                        run.font.size = Pt(6.5)







                    else:



                        # Policy comparison content.



                        run.font.size = Pt(6.5)











# ============================================================



# SLIDE 5 — RECOMMENDATION RATIONALE



# ============================================================











def _populate_slide_5(



    slide,



    workflow_result: Dict[str, Any],



) -> None:



    """



    Populate the final recommendation rationale slide.







    Slide 5 deliberately separates the recommendation rationale



    from the comparison table so Slide 4 remains clean and



    readable.







    The recommendation is advisory. It must not imply that the



    client has already selected or purchased the policy.



    """







    recommended = _get_recommended_name(



        workflow_result



    )







    recommendation = _get_recommendation(



        workflow_result



    )







    rationale = _shorten(



        recommendation.get("rationale"),



        420,



        (



            "Based on the available policy evidence and the "



            "client's identified workforce considerations, "



            "this policy merits consideration. Final policy "



            "selection remains with the client following "



            "review of terms, exclusions, pricing and insurer "



            "quotation."



        ),



    )







    replacements = {



        "[RECOMMENDED_POLICY]":



            _shorten(



                recommended,



                60,



                "Advisor review required",



            ),







        "[FINAL_RATIONALE]":



            rationale,



    }







    _replace_slide_text(



        slide,



        replacements,



    )











# ============================================================



# CLEAN REMAINING PLACEHOLDERS



# ============================================================







_PLACEHOLDER_PATTERN = re.compile(



    r"\[[A-Z0-9_]+\]"



)











def _clean_remaining_placeholders(prs: Presentation) -> None:
    """Never leave raw [PLACEHOLDER] tokens visible in the client deck."""
    pattern = re.compile(r"\[[A-Z0-9_]+\]")
    for slide in prs.slides:
        for shape in slide.shapes:
            for tf in _iter_text_targets(shape):
                for paragraph in tf.paragraphs:
                    full = "".join(run.text for run in paragraph.runs) if paragraph.runs else paragraph.text
                    if not pattern.search(full):
                        continue
                    updated = pattern.sub("", full)
                    if paragraph.runs:
                        paragraph.runs[0].text = updated
                        for run in paragraph.runs[1:]:
                            run.text = ""
                    else:
                        paragraph.text = updated



def generate_pitch_pptx(



    workflow_result: Dict[str, Any],



) -> BytesIO:



    """



    Populate the fixed INSUREAI client-facing PowerPoint



    template using an existing reviewed workflow result.







    No AI generation, retrieval or auditing occurs here.







    The exporter only formats information already contained



    in workflow_result.



    """







    if not workflow_result:



        raise ValueError(



            "No workflow result was supplied for pitch export."



        )







    if not TEMPLATE_PATH.exists():



        raise FileNotFoundError(



            f"PowerPoint template not found: {TEMPLATE_PATH}"



        )







    prs = Presentation(



        str(TEMPLATE_PATH)



    )







    _validate_template(



        prs



    )







    # --------------------------------------------------------



    # Populate each fixed template slide



    # --------------------------------------------------------







    _populate_slide_1(



        prs.slides[0],



        workflow_result,



    )







    _populate_slide_2(



        prs.slides[1],



        workflow_result,



    )







    _populate_slide_3(



        prs.slides[2],



        workflow_result,



    )







    _populate_slide_4(



        prs.slides[3],



        workflow_result,



    )







    _populate_slide_5(



        prs.slides[4],



        workflow_result,



    )







    # --------------------------------------------------------



    # Final safety cleanup



    # --------------------------------------------------------







    _clean_remaining_placeholders(



        prs



    )







    # --------------------------------------------------------



    # Save in memory for FastAPI StreamingResponse



    # --------------------------------------------------------







    output = BytesIO()







    prs.save(



        output



    )







    output.seek(0)







    return output