import sys
import os
from PyPDF2 import PdfReader, PdfWriter

def remove_pdf_password(input_path, password):
    try:
        # Check file exists
        if not os.path.isfile(input_path):
            print("Error: File not found.")
            input("Press Enter to exit...")
            return

        # Get script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Create output folder
        output_dir = os.path.join(script_dir, "Pdf_password_rm")
        os.makedirs(output_dir, exist_ok=True)

        # Output file path (same name)
        file_name = os.path.basename(input_path)
        output_path = os.path.join(output_dir, file_name)

        # Read PDF
        reader = PdfReader(input_path)

        # Decrypt PDF
        if reader.is_encrypted:
            if reader.decrypt(password) == 0:
                print("Error: Incorrect password.")
                input("Press Enter to exit...")
                return
        else:
            print("PDF is not password protected.")

        # Write decrypted PDF
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"\n✅ Success!")
        print(f"Decrypted PDF saved at:\n{output_path}")

    except Exception as e:
        print(f"Error: {str(e)}")

    input("\nPress Enter to exit...")


if __name__ == "__main__":

    # Case 1: Command line usage
    if len(sys.argv) == 3:
        input_pdf = sys.argv[1]
        pdf_password = sys.argv[2]

    # Case 2: Drag & Drop (file path passed automatically)
    elif len(sys.argv) == 2:
        input_pdf = sys.argv[1]
        pdf_password = input("Enter PDF password: ")

    # Case 3: Manual input
    else:
        input_pdf = input("Drag & drop PDF here or enter path: ").strip('"')
        pdf_password = input("Enter PDF password: ")

    remove_pdf_password(input_pdf, pdf_password)