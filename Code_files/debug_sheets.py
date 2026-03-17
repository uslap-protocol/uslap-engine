#!/usr/bin/env python3
import openpyxl

wb = openpyxl.load_workbook("USLaP_Final_Data_Consolidated_Master_v2.xlsx", read_only=True, data_only=True)

def debug_sheet(sheet_name):
    print(f"\n=== {sheet_name} ===")
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    for i, row in enumerate(rows[:10]):
        print(f"Row {i}: {row}")

debug_sheet("DP_REGISTER")
debug_sheet("PHONETIC_REVERSAL")
debug_sheet("UMD_OPERATIONS")

wb.close()