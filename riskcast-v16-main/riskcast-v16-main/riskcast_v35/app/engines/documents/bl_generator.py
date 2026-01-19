from datetime import datetime


def build_draft_bl_from_si(si_content: dict) -> dict:
    """
    Build a draft B/L structure using SI content as base.
    TODO: Add numbering and carrier-specific fields.
    """
    draft = dict(si_content or {})
    draft.update(
        {
            "bl_number": None,
            "issue_place": si_content.get("pol") if si_content else None,
            "issue_date": datetime.utcnow().isoformat(),
            "freight_term": "Prepaid",
        }
    )
    return draft

