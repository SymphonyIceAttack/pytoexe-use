import os
import win32com.client

def merge_excel_files():
    # Lấy folder chứa file .exe
    folder = os.path.dirname(os.path.abspath(__file__))

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    merged = excel.Workbooks.Add()
    sheet_out = merged.Worksheets(1)

    row = 1
    file_count = 0

    for file in os.listdir(folder):
        if file.endswith((".xlsx", ".xls")) and not file.startswith("~$"):
            file_path = os.path.join(folder, file)
            print(f"Processing: {file}")

            try:
                wb = excel.Workbooks.Open(file_path)
                
                try:
                    ws = wb.Worksheets("deliveryNote")

                    if row == 1:
                        ws.Range("A1").CurrentRegion.Copy(sheet_out.Cells(row, 1))
                    else:
                        ws.Range("A2").CurrentRegion.Copy(sheet_out.Cells(row, 1))

                    row = sheet_out.Cells(sheet_out.Rows.Count, 1).End(-4162).Row + 1

                    file_count += 1

                except:
                    print(f"❌ Sheet 'deliveryNote' not found in {file}")

                wb.Close(False)

            except:
                print(f"❌ Cannot open {file}")

    output_path = os.path.join(folder, "merged.xlsx")
    merged.SaveAs(output_path)

    excel.Quit()

    print(f"\n✅ Done! Merged {file_count} files")
    print(f"📁 Output: {output_path}")

if __name__ == "__main__":
    merge_excel_files()
    input("\nPress Enter to exit...")