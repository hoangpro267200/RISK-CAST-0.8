def compare_si_and_bl(si_content: dict, bl_content: dict) -> dict:
    """
    Compare key fields between SI and Draft B/L.
    """
    fields = [
        "shipper_name",
        "consignee_name",
        "pol",
        "pod",
        "goods_description",
        "weight",
        "volume",
    ]
    differences = []
    for field in fields:
        si_val = si_content.get(field) if si_content else None
        bl_val = bl_content.get(field) if bl_content else None
        if si_val != bl_val:
            differences.append({"field": field, "si": si_val, "bl": bl_val})
    return {"is_valid": len(differences) == 0, "differences": differences}

