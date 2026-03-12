#!/usr/bin/env python3
"""
dashboard_generator.py

Reads a dashboard config JSON and generates a populateSettings.gs Apps Script
file for each location. The generated scripts are pasted into a Google Sheet's
Apps Script editor and run once to fully populate the Settings sheet.

Usage:
    python dashboard_generator.py configs/<dashboard-config>.json

Output:
    ../dashboards/<report_id>-<location-slug>-settings.gs  (one per location)
"""

import json
import sys
import os
from datetime import datetime


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def location_slug(location_id: str) -> str:
    return location_id.lower().replace(" ", "-")


def js_value(val) -> str:
    """Return a JS-safe literal for a Python value."""
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    return json.dumps(str(val))


# ─────────────────────────────────────────────
#  Core generator
# ─────────────────────────────────────────────

def generate_gs_for_location(config: dict, location: dict) -> str:
    loc_id          = location["location_id"]
    settings_name   = location.get("settings_sheet_name", "Settings")
    raw_sheet_name  = location["raw_sheet_name"]
    location_filter = location.get("location_filter", "")
    invite_num      = location.get("invite_num", 0)

    report_id = config["report_id"]
    api_url   = f"https://api.badjupiter.cloud/report/{report_id}"

    # ── #GLOBAL key/value pairs ──────────────────────────────────────────────
    global_rows = [
        ("testProd",            config.get("test_prod", "test")),
        ("EventName",           config["event_name"]),
        ("outputSheetName",     config.get("output_sheet_name", "RSVPs")),
        ("outputHeaderRow",     config.get("output_header_row", 9)),
        ("outputDataStartRow",  config.get("output_data_start_row", 10)),
        ("timezone",            config.get("timezone", "America/Los_Angeles")),
        ("lastUpdatedCell",     config.get("last_updated_cell", "N2")),
        ("lastUpdatedFormat",   config.get("last_updated_format", "MMM d, yyyy h:mm a")),
        ("lastUpdatedPrefix",   config.get("last_updated_prefix", "Last updated:")),
        ("outputSortField",     config.get("sort_field", "")),
        ("outputSortDirection", config.get("sort_direction", "ASC")),
    ]

    # ── #RAW_SOURCE key/value pairs ──────────────────────────────────────────
    raw_rows = [
        ("apiUrl",          api_url),
        ("RawSheetName",    raw_sheet_name),
        ("RawHeaderRow",    1),
        ("RawDataStartRow", 2),
        ("inviteNum",       invite_num),
        ("locationFilter",  location_filter),
    ]

    # ── #DISPLAY_MAP rows (resolve location-specific display columns) ─────────
    display_map_raw = config.get("display_map", [])
    resolved_map = []
    for field in display_map_raw:
        if field.get("_comment"):
            pass  # skip comment-only keys; rest of field still processed
        display = field.get("display", "not used")
        if isinstance(display, dict):
            display = display.get(loc_id, "not used")

        resolved_map.append([
            field.get("field", ""),
            field.get("csv_pos", ""),   # may be "" for calc fields
            field.get("data_type", "text"),
            display,
            field.get("header", ""),
            field.get("format", ""),
            field.get("user_editable", "No"),
            field.get("transform", ""),
            field.get("default", ""),
            field.get("calc_type", ""),
            field.get("calc_args", ""),
        ])

    # ── Compute row numbers dynamically ──────────────────────────────────────
    global_header_row     = 1
    global_data_start     = global_header_row + 1
    raw_header_row        = global_data_start + len(global_rows) + 1   # blank row gap
    raw_data_start        = raw_header_row + 1
    display_header_row    = raw_data_start + len(raw_rows) + 1         # blank row gap
    display_col_hdr_row   = display_header_row + 1
    display_data_start    = display_col_hdr_row + 1

    num_display_cols = 11  # Field Name … Calc Args
    last_display_col = chr(ord('A') + num_display_cols - 1)  # 'K'

    display_col_headers = [
        "Field Name", "CSV Position", "Data Type", "Display Column",
        "Header Value", "Format", "User Editable", "Value Transform",
        "Default value", "Calc Type", "Calc Args"
    ]

    # ── Assemble the script ───────────────────────────────────────────────────
    lines = []

    lines += [
        f"/**",
        f" * populateSettings — {config['event_name']} — {loc_id}",
        f" * Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f" * Report:    {report_id}",
        f" * API:       {api_url}",
        f" *",
        f" * Instructions:",
        f" *   1. Open the {loc_id} dashboard Google Sheet",
        f" *   2. Extensions > Apps Script",
        f" *   3. Paste this file, replacing any existing content",
        f" *   4. Run populateSettings() once",
        f" *   5. Verify the Settings sheet, then delete or keep this script (it is idempotent)",
        f" */",
        f"",
        f"function populateSettings() {{",
        f"  var ss = SpreadsheetApp.getActiveSpreadsheet();",
        f"",
        f"  // ── Get or create Settings sheet ──────────────────────────────────",
        f"  var sheetName = {js_value(settings_name)};",
        f"  var sheet = ss.getSheetByName(sheetName);",
        f"  if (!sheet) {{",
        f"    sheet = ss.insertSheet(sheetName);",
        f"  }}",
        f"  sheet.clearContents();",
        f"",
    ]

    # #GLOBAL
    lines += [
        f"  // ── #GLOBAL ────────────────────────────────────────────────────────",
        f"  sheet.getRange('A{global_header_row}').setValue('#GLOBAL');",
    ]
    for i, (key, val) in enumerate(global_rows):
        row = global_data_start + i
        lines.append(f"  sheet.getRange('A{row}:B{row}').setValues([['{key}', {js_value(val)}]]);")
    lines.append("")

    # #RAW_SOURCE
    lines += [
        f"  // ── #RAW_SOURCE ────────────────────────────────────────────────────",
        f"  sheet.getRange('A{raw_header_row}').setValue('#RAW_SOURCE');",
    ]
    for i, (key, val) in enumerate(raw_rows):
        row = raw_data_start + i
        lines.append(f"  sheet.getRange('A{row}:B{row}').setValues([['{key}', {js_value(val)}]]);")
    lines.append("")

    # #DISPLAY_MAP header
    lines += [
        f"  // ── #DISPLAY_MAP ───────────────────────────────────────────────────",
        f"  sheet.getRange('A{display_header_row}').setValue('#DISPLAY_MAP');",
        f"  sheet.getRange('A{display_col_hdr_row}:{last_display_col}{display_col_hdr_row}').setValues([{json.dumps(display_col_headers)}]);",
        f"",
    ]

    # #DISPLAY_MAP data
    lines.append(f"  var displayMap = [")
    for row_data in resolved_map:
        lines.append(f"    {json.dumps(row_data)},")
    lines += [
        f"  ];",
        f"",
        f"  if (displayMap.length > 0) {{",
        f"    sheet.getRange({display_data_start}, 1, displayMap.length, {num_display_cols}).setValues(displayMap);",
        f"  }}",
        f"",
        f"  SpreadsheetApp.flush();",
        f"",
        f"  var msg = 'Settings populated for {loc_id}\\nSheet: ' + sheetName;",
        f"  Logger.log(msg);",
        f"  Browser.msgBox(msg);",
        f"}}",
    ]

    return "\n".join(lines) + "\n"


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python dashboard_generator.py configs/<dashboard-config>.json")
        sys.exit(1)

    config_path = sys.argv[1]
    with open(config_path) as f:
        config = json.load(f)

    script_dir   = os.path.dirname(os.path.abspath(__file__))
    output_dir   = os.path.join(os.path.dirname(script_dir), "dashboards")
    os.makedirs(output_dir, exist_ok=True)

    report_id = config["report_id"]
    locations = config.get("locations", [])

    if not locations:
        print("Error: no locations defined in config.")
        sys.exit(1)

    for location in locations:
        loc_id   = location["location_id"]
        slug     = location_slug(loc_id)
        filename = f"{report_id}-{slug}-settings.gs"
        out_path = os.path.join(output_dir, filename)

        gs_content = generate_gs_for_location(config, location)

        with open(out_path, "w") as f:
            f.write(gs_content)

        print(f"✓  {filename}")

    print(f"\nOutput directory: {output_dir}")


if __name__ == "__main__":
    main()
