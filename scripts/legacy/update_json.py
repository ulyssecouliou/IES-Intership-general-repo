# -*- coding: utf-8 -*-
import openpyxl
import json
from datetime import datetime

# Load current JSON
with open(r'C:\Users\ulysse.couliou\Documents\SIA_Compliance_Scripts\refs\reference-data\test-1.ref.json', 'r', encoding='utf-8') as f:
    current_data = json.load(f)

wb_path = r"C:\Users\ulysse.couliou\Documents\SIA_Compliance_Scripts\SIA_4010_geteilter_Link\Test1\Resultaterfassung_Test1.xlsx"
wb = openpyxl.load_workbook(wb_path, data_only=True)
ws = wb["Zusammenfassung Testfälle"]

# ===== TABLE 30 EXTRACTION (Monthly Data) =====
def extract_table_30():
    table_30_data = {}

    # Cases 600FF and 900FF (monthly)
    cases_30 = [
        ("600FF", "AG", "AH", "AI", "AJ", "AK", "AL", "AM"),
        ("900FF", "AO", "AP", "AQ", "AR", "AS", "AT", "AU"),
    ]

    for case_id, col_month, col_testprog, col_iso, col_ida, col_excel, col_energyplus, col_tas in cases_30:
        case_data = {
            "_metadata": {
                "case_id": case_id,
                "table_number": 30,
                "table_name": "Operative temperature - monthly",
                "description": "Free-floating temperature (monthly data)",
                "columns": {
                    "month": col_month,
                    "testprogramm": col_testprog,
                    "iso_52016_1_2017": col_iso,
                    "ida_ice_5_0_beta_23": col_ida,
                    "excel_sia_380_2": col_excel,
                    "energyplus_openstudio": col_energyplus,
                    "tas_edsl": col_tas,
                }
            },
            "monthly": {}
        }

        # Rows 58-69 (months 1-12)
        for row in range(58, 70):
            month_num = ws[f'{col_month}{row}'].value
            testprog = ws[f'{col_testprog}{row}'].value
            iso = ws[f'{col_iso}{row}'].value
            ida = ws[f'{col_ida}{row}'].value
            excel = ws[f'{col_excel}{row}'].value
            energyplus = ws[f'{col_energyplus}{row}'].value
            tas = ws[f'{col_tas}{row}'].value

            if month_num and isinstance(month_num, int) and 1 <= month_num <= 12:
                month_key = f"month_{month_num:02d}"
                case_data["monthly"][month_key] = {
                    "testprogramm_candidate": {
                        "value": testprog if not isinstance(testprog, str) else None,
                        "unit": "C",
                        "cell": f"{col_testprog}{row}",
                        "note": "Excel error: #DIV/0!" if testprog == "#DIV/0!" else None
                    },
                    "iso_52016_1_2017_reference": {
                        "value": iso,
                        "unit": "C",
                        "cell": f"{col_iso}{row}",
                    },
                    "ida_ice_5_0_beta_23": {
                        "value": ida,
                        "unit": "C",
                        "cell": f"{col_ida}{row}",
                    },
                    "excel_sia_380_2": {
                        "value": excel,
                        "unit": "C",
                        "cell": f"{col_excel}{row}",
                    },
                    "energyplus_openstudio": {
                        "value": energyplus,
                        "unit": "C",
                        "cell": f"{col_energyplus}{row}",
                    },
                    "tas_edsl": {
                        "value": tas,
                        "unit": "C",
                        "cell": f"{col_tas}{row}",
                    }
                }

        # Row 70 (annual)
        row = 70
        month_num = ws[f'{col_month}{row}'].value
        testprog = ws[f'{col_testprog}{row}'].value
        iso = ws[f'{col_iso}{row}'].value
        ida = ws[f'{col_ida}{row}'].value
        excel = ws[f'{col_excel}{row}'].value
        energyplus = ws[f'{col_energyplus}{row}'].value
        tas = ws[f'{col_tas}{row}'].value

        if month_num == "Annual":
            case_data["monthly"]["annual"] = {
                "testprogramm_candidate": {
                    "value": testprog if not isinstance(testprog, str) else None,
                    "unit": "C",
                    "cell": f"{col_testprog}{row}",
                    "note": "Excel error: #DIV/0!" if testprog == "#DIV/0!" else None
                },
                "iso_52016_1_2017_reference": {
                    "value": iso,
                    "unit": "C",
                    "cell": f"{col_iso}{row}",
                },
                "ida_ice_5_0_beta_23": {
                    "value": ida,
                    "unit": "C",
                    "cell": f"{col_ida}{row}",
                },
                "excel_sia_380_2": {
                    "value": excel,
                    "unit": "C",
                    "cell": f"{col_excel}{row}",
                },
                "energyplus_openstudio": {
                    "value": energyplus,
                    "unit": "C",
                    "cell": f"{col_energyplus}{row}",
                },
                "tas_edsl": {
                    "value": tas,
                    "unit": "C",
                    "cell": f"{col_tas}{row}",
                }
            }

        table_30_data[case_id] = case_data

    return table_30_data

# ===== TABLE 32 EXTRACTION (Annual Extremes) =====
def extract_table_32():
    table_32_data = {}

    # Cases 600FF and 900FF (extremes: Max/Min/Average)
    cases_32 = [
        ("600FF", ("A", "B", "C", "D", "E", "F", "G")),
        ("900FF", ("I", "J", "K", "L", "M", "N", "O")),
    ]

    for case_id, cols in cases_32:
        col_label, col_testprog, col_iso, col_ida, col_excel, col_energyplus, col_tas = cols

        case_data = {
            "_metadata": {
                "case_id": case_id,
                "table_number": 32,
                "table_name": "Operative temperature - annual extremes",
                "description": "Annual extremes (Max/Min/Average temperature)",
                "columns": {
                    "label": col_label,
                    "testprogramm": col_testprog,
                    "iso_52016_1_2017": col_iso,
                    "ida_ice_5_0_beta_23": col_ida,
                    "excel_sia_380_2": col_excel,
                    "energyplus_openstudio": col_energyplus,
                    "tas_edsl": col_tas,
                }
            },
            "annual": {}
        }

        # Rows 105 (Max), 106 (Min), 107 (Average)
        for row, label_key in [(105, "max"), (106, "min"), (107, "average")]:
            label = ws[f'{col_label}{row}'].value
            testprog = ws[f'{col_testprog}{row}'].value
            iso = ws[f'{col_iso}{row}'].value
            ida = ws[f'{col_ida}{row}'].value
            excel = ws[f'{col_excel}{row}'].value
            energyplus = ws[f'{col_energyplus}{row}'].value
            tas = ws[f'{col_tas}{row}'].value

            case_data["annual"][label_key] = {
                "label": label,
                "testprogramm_candidate": {
                    "value": testprog if not isinstance(testprog, str) else None,
                    "unit": "C",
                    "cell": f"{col_testprog}{row}",
                    "note": "Excel error: #DIV/0!" if testprog == "#DIV/0!" else None
                },
                "iso_52016_1_2017_reference": {
                    "value": iso,
                    "unit": "C",
                    "cell": f"{col_iso}{row}",
                },
                "ida_ice_5_0_beta_23": {
                    "value": ida,
                    "unit": "C",
                    "cell": f"{col_ida}{row}",
                },
                "excel_sia_380_2": {
                    "value": excel,
                    "unit": "C",
                    "cell": f"{col_excel}{row}",
                },
                "energyplus_openstudio": {
                    "value": energyplus,
                    "unit": "C",
                    "cell": f"{col_energyplus}{row}",
                },
                "tas_edsl": {
                    "value": tas,
                    "unit": "C",
                    "cell": f"{col_tas}{row}",
                }
            }

        table_32_data[case_id] = case_data

    return table_32_data

# Extract corrected data
table_30_data = extract_table_30()
table_32_data = extract_table_32()

print("Table 30 (monthly) extracted:", list(table_30_data.keys()))
print("Table 32 (annual extremes) extracted:", list(table_32_data.keys()))

# Update JSON
current_data["reference_values"]["operative_temperature_monthly_celsius"]["600FF"] = table_30_data["600FF"]
current_data["reference_values"]["operative_temperature_monthly_celsius"]["900FF"] = table_30_data["900FF"]
current_data["reference_values"]["operative_temperature_annual_extremes_celsius"]["600FF"] = table_32_data["600FF"]
current_data["reference_values"]["operative_temperature_annual_extremes_celsius"]["900FF"] = table_32_data["900FF"]

# Update status and extraction date
current_data["status"] = "CORRECTED"
current_data["extraction_date"] = datetime.now().isoformat()
current_data["corrections"] = {
    "date": datetime.now().isoformat(),
    "reason": "Fixed column mapping error in Table 30 (600FF/900FF) and Table 32 (600FF/900FF extremes)",
    "details": {
        "table_30": "Corrected column mapping for 600FF (AG-AM) and 900FF (AP-AU); documented #DIV/0! errors in Testprogramm",
        "table_32": "Fixed zone identification for extremes; now using Zone 2 (A-G and I-O) instead of Zone 3 (BH-BM)"
    }
}

# Save corrected JSON
with open(r'C:\Users\ulysse.couliou\Documents\SIA_Compliance_Scripts\refs\reference-data\test-1.ref.json', 'w', encoding='utf-8') as f:
    json.dump(current_data, f, indent=2, ensure_ascii=False)

print("\nJSON updated and saved.")
print("Status:", current_data["status"])
