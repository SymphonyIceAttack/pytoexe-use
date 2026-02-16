import pandas as pd
import os
import re
from collections import Counter

folder = "/Users/iskandar/Documents/BillerValidation"
routing_file = "bank routing validation.xlsx"
routing_path = os.path.join(folder, routing_file)

# Load Biller List
biller_df = pd.read_excel(routing_path, sheet_name="Biller List")
biller_column = "Biller ID"
bank_column = "BANKS Name" 

# Mapping Biller -> Bank (standardize)
biller_to_bank = dict(zip(
    biller_df[biller_column].str.upper().str.strip(),
    biller_df[bank_column].str.strip()
))
  
all_mismatches = []
not_found_list = []
invalid_list = []

for file in os.listdir(folder):
    if file.endswith(".xlsx") and file != routing_file:
        print(f"\nChecking file: {file}")
        report_path = os.path.join(folder, file)
        report_df = pd.read_excel(report_path, header=None)
        
        # Simpan semua row: (row idx, biller_code, bank)
        row_info = []
        
        for idx, row in report_df.iterrows():
            # START FROM ROW 6 (A7) - index 6
            if idx < 6:
                continue
                
            first_col = str(row[0]).upper().strip()
            
            # CHECK: Has biller code format?
            match = re.search(r"([A-Z]+\d+)", first_col)
            
            if match:
                # HAS DIGIT - this is biller code
                biller_code = match.group(1)
                actual_bank = biller_to_bank.get(biller_code)
                
                if actual_bank:
                    row_info.append((idx, biller_code, actual_bank))
                else:
                    not_found_list.append({
                        "Report name": file,
                        "Row": idx,
                        "Biller code": biller_code,
                        "Status": "NOT FOUND IN BILLER LIST"
                    })
            else:
                # NO DIGIT - capture everything including empty
                if first_col != "NAN" and first_col not in ["NONE"]:
                    # Only capture short text or symbols or empty
                    if len(first_col) < 20 or '(' in first_col or ')' in first_col or '-' in first_col or first_col == "":
                        invalid_list.append({
                            "Report name": file,
                            "Row": idx,
                            "Content": first_col if first_col else "[EMPTY]",
                            "Status": "NOT A BILLER CODE FORMAT (MANUAL CHECK REQUIRED)"
                        })
                    
        if not row_info:
            continue
            
        # Calculate majority bank for report
        banks_only = [bank for _, _, bank in row_info]
        majority_bank, _ = Counter(banks_only).most_common(1)[0]
        
        # List rows that differ from report majority
        for idx, biller_code, bank in row_info:
            if bank != majority_bank:
                all_mismatches.append({
                    "Report name": file,
                    "Row": idx,
                    "Biller mismatch": biller_code,
                    "Bank": bank,
                    "Biller Bank": majority_bank
                })

# Print INVALID FORMAT - ONLY ROW 6 AND ABOVE
if invalid_list:
    print("\n" + "="*80)
    print("⚠️ NOT A BILLER CODE FORMAT (MANUAL CHECK REQUIRED):")
    print("="*80)
    invalid_df = pd.DataFrame(invalid_list)
    # Filter to ensure row >= 6
    invalid_df = invalid_df[invalid_df['Row'] >= 6]
    print(invalid_df.to_string(index=False))

# Print NOT FOUND
if not_found_list:
    print("\n" + "="*80)
    print("❌ BILLER CODE NOT FOUND IN BILLER LIST:")
    print("="*80)
    not_found_df = pd.DataFrame(not_found_list)
    print(not_found_df.to_string(index=False))
                  
# Print mismatch
if all_mismatches:
    print("\n" + "="*80)
    print("⚠️ ROWS WITH BANK DIFFERENT FROM REPORT MAJORITY:")
    print("="*80)
    mismatch_df = pd.DataFrame(all_mismatches)
    print(mismatch_df.to_string(index=False))

if not invalid_list and not not_found_list and not all_mismatches:
    print("\n✅ No issues found in all reports.")
