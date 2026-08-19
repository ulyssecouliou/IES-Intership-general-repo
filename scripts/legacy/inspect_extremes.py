import openpyxl

wb_path = r"C:\Users\ulysse.couliou\Documents\SIA_Compliance_Scripts\SIA_4010_geteilter_Link\Test1\Resultaterfassung_Test1.xlsx"
wb = openpyxl.load_workbook(wb_path, data_only=True)
ws = wb["Zusammenfassung Testfälle"]

print("Inspection des extrêmes annuels (Table 32) :\n")

# Rows 104-107 (standard structure with AY labels)
print("=== Structure standard (lignes 104-107) ===")
print("\nLignes 105-107, blocs A-G et I-O :")
for row in range(105, 108):
    a_val = ws[f'A{row}'].value
    b_val = ws[f'B{row}'].value
    c_val = ws[f'C{row}'].value
    i_val = ws[f'I{row}'].value
    j_val = ws[f'J{row}'].value
    k_val = ws[f'K{row}'].value
    ay_val = ws[f'AY{row}'].value
    print(f"Row {row}: A={a_val}, B={b_val}, C={c_val} | I={i_val}, J={j_val}, K={k_val} | AY={ay_val}")

# Rows 108-112 (labels/descriptions)
print("\nLignes 108-112 (labels/codenames/countries) :")
for row in range(108, 113):
    ay_val = ws[f'AY{row}'].value
    if ay_val:
        print(f"Row {row}: AY={ay_val}")

# Check columns BH-BM
print("\n=== Alternative structure (colonnes BH-BM) ===")
print("\nLignes 105-107, colonnes BH-BM (si présentes) :")
for row in range(105, 108):
    bh_val = ws[f'BH{row}'].value
    bi_val = ws[f'BI{row}'].value
    bj_val = ws[f'BJ{row}'].value
    bk_val = ws[f'BK{row}'].value
    bl_val = ws[f'BL{row}'].value
    bm_val = ws[f'BM{row}'].value
    print(f"Row {row}: BH={bh_val}, BI={bi_val}, BJ={bj_val}, BK={bk_val}, BL={bl_val}, BM={bm_val}")

# Rows 108-112 for BH
print("\nLignes 108-112, colonne BH :")
for row in range(108, 113):
    bh_val = ws[f'BH{row}'].value
    if bh_val:
        print(f"Row {row}: BH={bh_val}")

print("\n=== Vérification de la zone 95-99 (programmes historiques) ===")
print("Lignes 95-99, colonnes AZ onwards :")
for row in range(95, 100):
    ay_val = ws[f'AY{row}'].value
    az_val = ws[f'AZ{row}'].value
    ba_val = ws[f'BA{row}'].value
    bb_val = ws[f'BB{row}'].value
    bc_val = ws[f'BC{row}'].value
    bd_val = ws[f'BD{row}'].value
    be_val = ws[f'BE{row}'].value
    bf_val = ws[f'BF{row}'].value
    bg_val = ws[f'BG{row}'].value
    bh_val = ws[f'BH{row}'].value
    print(f"Row {row}: AY={repr(ay_val)}, AZ={az_val}, BA={ba_val}, ..., BH={bh_val}")

