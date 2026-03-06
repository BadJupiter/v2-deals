"""
deal_generator.py
-----------------
Generates a deal JSON file (and scaffolded CSS file) from a simple config file.

Usage:
    python deal_generator.py configs/trc-wrangler-config.json

Output:
    ../deals/{deal_id}.json
    ../deals/{deal_id}.css  (if css section present in config)
"""

import json
import sys
import os
import re
from copy import deepcopy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_location_abbrev(name):
    """Auto-generate a short ID from a location name. E.g. 'Coos Bay' -> 'CB', 'Florence' -> 'FL'."""
    words = name.split()
    if len(words) == 1:
        return name[:2].upper()
    return "".join(w[0].upper() for w in words)


def build_context_vars(context_vars):
    """Hidden sticky/disabled fields that carry per-user context from the QR slug."""
    fields = []
    for cv in context_vars:
        fields.append({
            "id": cv["id"],
            "label": cv.get("label", cv["id"]),
            "type": "text",
            "sticky": True,
            "disabled": True,
            "hidden": True
        })
    return fields


def build_header_blocks(header_blocks):
    """Info (display-only) fields for the form header."""
    fields = []
    for block in header_blocks:
        f = {"type": "info", "markdown": block["markdown"]}
        if "justify" in block:
            f["justify"] = block["justify"]
        fields.append(f)
    return fields


def build_attend_field(attend_cfg):
    """The primary attend/RSVP Yes/No question."""
    f = {
        "id": "attend",
        "label": attend_cfg["label"],
        "type": "select",
        "range": ["Yes", "No"],
        "required": True
    }
    if attend_cfg.get("use_capacity_map"):
        f["global"] = True
        f["capacity_map"] = {"Yes": 1, "No": 0}
    return f


def build_location_field(locations, attend_field_id="attend"):
    """Location selector, shown only when attend = Yes."""
    return {
        "id": "location",
        "label": "Which location would you like to attend?",
        "type": "select",
        "range": [loc["id"] for loc in locations],
        "required": True,
        "conditional": {
            "field": attend_field_id,
            "value": "Yes"
        }
    }


def build_day_field(days, attend_field_id="attend"):
    """Day selector, shown only when attend = Yes."""
    return {
        "id": "day",
        "label": "What day would you like to attend?",
        "type": "select",
        "range": [d["label"] for d in days],
        "required": True,
        "conditional": {
            "field": attend_field_id,
            "value": "Yes"
        }
    }


def build_time_slot_fields(config):
    """
    Generate one time-slot select field per (location x day) combination.
    If no locations defined, generates one field per day (or one field total if no days either).
    Field IDs follow the pattern: {LOC_ABBREV}day{N}time  (e.g. FLday1time, CBday2time)
    If no locations: day{N}time
    If no days and no locations: time
    """
    ts_cfg = config.get("time_slots")
    if not ts_cfg:
        return []

    values = ts_cfg["values"]
    cap = ts_cfg.get("capacity", {})
    total_cap = cap.get("total_per_slot_field")
    per_option_cap = cap.get("per_option")
    count_from = ts_cfg.get("count_from", "attend")

    locations = config.get("locations", [])
    days = config.get("days", [])

    def make_range(values, per_option_cap):
        if per_option_cap is not None:
            return [{"value": v, "limit": per_option_cap} for v in values]
        return list(values)

    def make_field(field_id, conditions):
        f = {
            "id": field_id,
            "label": "What time would you like to attend?",
            "type": "select",
            "count_from": count_from,
            "range": make_range(values, per_option_cap),
            "required": True,
            "conditional": conditions
        }
        if total_cap is not None:
            f["limit"] = total_cap
        return f

    fields = []

    if locations and days:
        # One field per (location x day) combination
        for loc in locations:
            loc_abbrev = loc.get("abbrev") or make_location_abbrev(loc["id"])
            for day_idx, day in enumerate(days, start=1):
                field_id = f"{loc_abbrev}day{day_idx}time"
                conditions = [
                    {"field": "attend", "value": "Yes"},
                    {"field": "day", "value": day["label"]},
                    {"field": "location", "value": loc["id"]}
                ]
                fields.append(make_field(field_id, conditions))

    elif days:
        # One field per day, no location dimension
        for day_idx, day in enumerate(days, start=1):
            field_id = f"day{day_idx}time"
            conditions = [
                {"field": "attend", "value": "Yes"},
                {"field": "day", "value": day["label"]}
            ]
            fields.append(make_field(field_id, conditions))

    elif locations:
        # One field per location, no day dimension
        for loc in locations:
            loc_abbrev = loc.get("abbrev") or make_location_abbrev(loc["id"])
            field_id = f"{loc_abbrev}time"
            conditions = [
                {"field": "attend", "value": "Yes"},
                {"field": "location", "value": loc["id"]}
            ]
            fields.append(make_field(field_id, conditions))

    else:
        # Simple: single time slot field, conditional only on attend
        fields.append(make_field("time", {"field": "attend", "value": "Yes"}))

    return fields


def build_per_location_day_fields(config):
    """
    When locations define per-location day capacity, generate one day-select field
    per location (instead of a single shared day field).

    Each field is conditional on attend=Yes AND location=<that location>, and each
    day option carries its own capacity limit.

    Returns (fields, loc_to_day_field_id) where loc_to_day_field_id maps
    location id -> field id  (e.g. {"Florence": "FLday", "Coos Bay": "CBday"})
    """
    locations = config.get("locations", [])
    days = config.get("days", [])

    # Only activate this path when at least one location has day_capacity defined
    if not any(loc.get("day_capacity") is not None for loc in locations):
        return [], {}

    fields = []
    loc_to_field_id = {}

    for loc in locations:
        loc_abbrev = loc.get("abbrev") or make_location_abbrev(loc["id"])
        field_id = f"{loc_abbrev}day"
        loc_to_field_id[loc["id"]] = field_id

        day_cap = loc.get("day_capacity")

        # Build range: per-option limits when capacity is set, plain strings otherwise
        if day_cap is not None:
            range_options = [{"value": d["label"], "limit": day_cap} for d in days]
        else:
            range_options = [d["label"] for d in days]

        f = {
            "id": field_id,
            "label": "What day would you like to attend?",
            "type": "select",
            "count_from": "attend",
            "range": range_options,
            "required": True,
            "conditional": [
                {"field": "attend", "value": "Yes"},
                {"field": "location", "value": loc["id"]}
            ]
        }

        # Optional total capacity cap across all days for this location
        total_cap = loc.get("day_capacity_total")
        if total_cap is not None:
            f["limit"] = total_cap

        fields.append(f)

    return fields, loc_to_field_id


def build_hotel_room_field(hotel_cfg, locations, config=None, loc_to_day_field=None):
    """
    Optional hotel room assistance question.
    Shown when: attend=Yes, location in eligible_locations, Hotel context var = Y.
    eligible_days can optionally further restrict by day.

    loc_to_day_field: mapping of location id -> day field id, used when per-location
    day fields are in use (so the day condition references the correct field).
    """
    if not hotel_cfg or not hotel_cfg.get("enabled"):
        return None

    eligible_locs = hotel_cfg.get("eligible_locations", [])
    eligible_days = hotel_cfg.get("eligible_days")  # None = all days

    # Use "value" for single match, "values" for multiple — matching platform convention
    loc_condition = (
        {"field": "location", "value": eligible_locs[0]}
        if len(eligible_locs) == 1
        else {"field": "location", "values": eligible_locs}
    )

    conditions = [
        {"field": "attend", "value": "Yes"},
        loc_condition,
        {"field": "Hotel", "values": ["Y"]}
    ]

    # Resolve which day field to reference for the day condition
    all_days = [d["label"] for d in (config or {}).get("days", [])]
    days_to_check = eligible_days or all_days

    if days_to_check:
        # When per-location day fields exist, reference the eligible location's day field
        eligible_loc = eligible_locs[0] if len(eligible_locs) == 1 else None
        day_field_id = (
            loc_to_day_field.get(eligible_loc)
            if loc_to_day_field and eligible_loc
            else "day"
        )
        conditions.insert(2, {"field": day_field_id, "values": days_to_check})

    return {
        "id": "room",
        "label": hotel_cfg.get("label", "Would you like to be contacted for a room reservation?"),
        "type": "select",
        "range": ["Yes", "No"],
        "required": True,
        "conditional": conditions
    }


def build_custom_questions(custom_questions):
    """
    Arbitrary event-specific questions with their own display conditions.
    Each question in config:
        id, type, label, options (for select/multi-select),
        required, conditions (list of {field, value} or {field, values})
    """
    fields = []
    for q in custom_questions:
        f = {
            "id": q["id"],
            "label": q["label"],
            "type": q.get("type", "select"),
            "required": q.get("required", False)
        }
        if "options" in q:
            f["range"] = q["options"]
        if "rows" in q:
            f["rows"] = q["rows"]
        if "placeholder" in q:
            f["placeholder"] = q["placeholder"]
        if "conditions" in q and q["conditions"]:
            conds = q["conditions"]
            f["conditional"] = conds if len(conds) > 1 else conds[0]
        fields.append(f)
    return fields


def build_footer(footer_cfg):
    """Player info fields group at the bottom of the form."""
    fields = []
    for fld in footer_cfg.get("fields", []):
        f = {
            "id": fld["id"],
            "label": fld["label"],
            "type": fld.get("type", "text"),
            "sticky": True,
            "disabled": fld.get("disabled", True)
        }
        fields.append(f)

    return {
        "type": "fields_group",
        "bgcolor": footer_cfg.get("bgcolor", "#f5f5f5"),
        "fields": fields
    }


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_deal(config):
    fields = []

    # 1. Hidden context variables
    for f in build_context_vars(config.get("context_vars", [])):
        fields.append(f)

    # 2. Header info blocks
    for f in build_header_blocks(config.get("header_blocks", [])):
        fields.append(f)

    # 3. Attend question
    attend_cfg = config.get("attend")
    if attend_cfg:
        fields.append(build_attend_field(attend_cfg))

    # 4. Location question (only if multiple locations defined)
    locations = config.get("locations", [])
    if len(locations) > 1:
        fields.append(build_location_field(locations))

    # 5. Day question — two modes:
    #    a) Per-location day fields with capacity tracking (when locations have day_capacity)
    #    b) Single shared day field (standard case)
    days = config.get("days", [])
    per_loc_day_fields, loc_to_day_field = build_per_location_day_fields(config)

    if per_loc_day_fields:
        for f in per_loc_day_fields:
            fields.append(f)
    elif len(days) > 1:
        fields.append(build_day_field(days))

    # 6. Time slot fields (combinatorial)
    for f in build_time_slot_fields(config):
        fields.append(f)

    # 7. Hotel room question (optional)
    hotel_field = build_hotel_room_field(
        config.get("hotel_room"), locations, config, loc_to_day_field
    )
    if hotel_field:
        fields.append(hotel_field)

    # 8. Custom one-off questions
    for f in build_custom_questions(config.get("custom_questions", [])):
        fields.append(f)

    # 9. Divider before footer
    fields.append({"type": "info", "markdown": "---"})

    # 10. Footer fields group
    footer_cfg = config.get("footer")
    if footer_cfg:
        fields.append(build_footer(footer_cfg))

    # Assemble FORM section
    form = {"fields": fields}

    if "form_title" in config:
        form["title"] = config["form_title"]

    limits_cfg = config.get("limits")
    if limits_cfg:
        form["limits"] = {
            "most_recent_only": limits_cfg.get("most_recent_only", True),
            "most_recent_key": limits_cfg["most_recent_key"]
        }

    submit_cfg = config.get("submit")
    if submit_cfg:
        form["submit"] = {
            "label": submit_cfg.get("label", "Submit"),
            "color": submit_cfg.get("color", "#333333")
        }

    # Assemble full deal
    deal = {
        "biz_id": config["biz_id"],
        "check_in": config.get("check_in", True),
        "auth_required": config.get("auth_required", True)
    }

    if "error_auth" in config:
        deal["error_auth"] = config["error_auth"]

    if "active" in config:
        deal["active"] = config["active"]

    if "summary_info" in config:
        deal["summary_info"] = config["summary_info"]

    deal["FORM"] = form

    main_cfg = config.get("main", {})
    deal["MAIN"] = {"body_md": main_cfg.get("body_md", "# Thank you!")}

    return deal


# ---------------------------------------------------------------------------
# CSS generator
# ---------------------------------------------------------------------------

def build_css(config, deal_id):
    css_cfg = config.get("css")
    if not css_cfg:
        return None

    bg = css_cfg.get("background_color", "#ffffff")
    fonts = css_cfg.get("fonts", {})
    header_font = fonts.get("headers", {})
    body_font = fonts.get("body", {})

    lines = [f"/* CSS for deal: {deal_id} */", ""]

    if bg:
        lines.append(f"body, .deal-form {{")
        lines.append(f"    background-color: {bg};")
        lines.append(f"}}")
        lines.append("")

    if header_font.get("family"):
        weight = header_font.get("weight", "bold")
        style = header_font.get("style", "normal")
        lines.append(f"h1, h2, h3, .form-title {{")
        lines.append(f"    font-family: '{header_font['family']}', sans-serif;")
        lines.append(f"    font-weight: {weight};")
        lines.append(f"    font-style: {style};")
        lines.append(f"}}")
        lines.append("")

    if body_font.get("family"):
        weight = body_font.get("weight", "normal")
        lines.append(f"body, .form-label, input, select, textarea {{")
        lines.append(f"    font-family: '{body_font['family']}', sans-serif;")
        lines.append(f"    font-weight: {weight};")
        lines.append(f"}}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python deal_generator.py <config_file.json>")
        sys.exit(1)

    config_path = sys.argv[1]
    with open(config_path, "r") as f:
        config = json.load(f)

    deal_id = config.get("deal_id")
    if not deal_id:
        print("Error: config must include a 'deal_id' field.")
        sys.exit(1)

    # Output goes into ../deals/ relative to the tools/ folder
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    deals_dir = os.path.join(tools_dir, "..", "deals")
    os.makedirs(deals_dir, exist_ok=True)

    # Generate deal JSON
    deal = build_deal(config)
    out_json = os.path.join(deals_dir, f"{deal_id}.json")
    with open(out_json, "w") as f:
        json.dump(deal, f, indent="\t")
    print(f"✓ Deal JSON written to: {out_json}")

    # Generate CSS (if configured)
    css_content = build_css(config, deal_id)
    if css_content:
        out_css = os.path.join(deals_dir, f"{deal_id}.css")
        with open(out_css, "w") as f:
            f.write(css_content)
        print(f"✓ CSS written to:      {out_css}")

    print("\nDone.")


if __name__ == "__main__":
    main()
