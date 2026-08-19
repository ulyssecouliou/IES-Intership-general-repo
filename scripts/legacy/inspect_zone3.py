import openpyxl

wb_path = r"C:\Users\ulysse.couliou\Documents\SIA_Compliance_Scripts\SIA_4010_geteilter_Link\Test1\Resultaterfassung_Test1.xlsx"
wb = openpyxl.load_workbook(wb_path, data_only=True)
ws = wb["Zusammenfassung Testfälle"]

print("=== Zone 3 : En-têtes et structure (colonnes BH onwards) ===\n")

# Header: find the header row
print("Cherche en-têtes (lignes 100-110, colonnes BH-BM) :")
for row in range(100, 112):
    bh_val = ws[f'BH{row}'].value
    bi_val = ws[f'BI{row}'].value
    bj_val = ws[f'BJ{row}'].value
    if bh_val or bi_val or bj_val:
        print(f"Row {row}: BH={repr(bh_val)}, BI={repr(bi_val)}, BJ={repr(bj_val)}")

# Check the headers for zone A-G (structure 1)
print("\n\n=== Zone 2 : En-têtes (lignes 100-110, colonnes A-G et I-O) ===")
for row in range(100, 112):
    a_val = ws[f'A{row}'].value
    b_val = ws[f'B{row}'].value
    c_val = ws[f'C{row}'].value
    i_val = ws[f'I{row}'].value
    j_val = ws[f'J{row}'].value
    k_val = ws[f'K{row}'].value
    if a_val or b_val or c_val or i_val or j_val or k_val:
        print(f"Row {row}: A={repr(a_val)}, B={repr(b_val)}, C={repr(c_val)}, I={repr(i_val)}, J={repr(j_val)}, K={repr(k_val)}")

# Check whether there is data below the headers (rows 113-130)
print("\n\n=== Zone 3 : Données possibles (lignes 113-130, colonnes BH-BM) ===")
for row in range(113, 131):
    bh_val = ws[f'BH{row}'].value
    bi_val = ws[f'BI{row}'].value
    bj_val = ws[f'BJ{row}'].value
    bk_val = ws[f'BK{row}'].value
    bl_val = ws[f'BL{row}'].value
    bm_val = ws[f'BM{row}'].value
    if bh_val or bi_val or bj_val or bk_val or bl_val or bm_val:
        print(f"Row {row}: BH={repr(bh_val)}, BI={repr(bi_val)}, BJ={repr(bj_val)}, BK={repr(bk_val)}, BL={repr(bl_val)}, BM={repr(bm_val)}")

