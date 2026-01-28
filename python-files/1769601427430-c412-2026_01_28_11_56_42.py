import time

# Since 'win32print' and 'win32api' modules are not available, we provide a mock implementation for demonstration.
# In a real Windows environment, install 'pywin32' package and uncomment the import lines below.

# import win32print
# import win32api

class MockWin32Print:
    PRINTER_ENUM_LOCAL = 2

    @staticmethod
    def EnumPrinters(flags):
        # Return a list of tuples with printer info; third element is printer name
        return [(0, 0, 'Godex GE330', None), (0, 0, 'Microsoft Print to PDF', None)]

    @staticmethod
    def OpenPrinter(name):
        print(f"[Mock] OpenPrinter called with: {name}")
        return 1  # mock handle

    @staticmethod
    def StartDocPrinter(hprinter, level, docinfo):
        print(f"[Mock] StartDocPrinter called with handle {hprinter} and docinfo {docinfo}")

    @staticmethod
    def StartPagePrinter(hprinter):
        print(f"[Mock] StartPagePrinter called with handle {hprinter}")

    @staticmethod
    def WritePrinter(hprinter, data):
        print(f"[Mock] WritePrinter called with handle {hprinter} and data length {len(data)}")

    @staticmethod
    def EndPagePrinter(hprinter):
        print(f"[Mock] EndPagePrinter called with handle {hprinter}")

    @staticmethod
    def EndDocPrinter(hprinter):
        print(f"[Mock] EndDocPrinter called with handle {hprinter}")

    @staticmethod
    def ClosePrinter(hprinter):
        print(f"[Mock] ClosePrinter called with handle {hprinter}")

win32print = MockWin32Print


def print_to_godex(printer_name: str, ezpl_commands: str, encoding: str = 'cp437') -> bool:
    """
    Send EZPL commands to Godex printer via Windows driver.
    Args:
        printer_name: Exact printer name in the system
        ezpl_commands: EZPL command string
        encoding: Encoding (default 'cp437')
    Returns:
        True if sent successfully, else False
    """
    try:
        hprinter = win32print.OpenPrinter(printer_name)
        doc_info = ("Godex Label", None, None)
        win32print.StartDocPrinter(hprinter, 1, doc_info)
        win32print.StartPagePrinter(hprinter)
        raw_data = ezpl_commands.encode(encoding)
        win32print.WritePrinter(hprinter, raw_data)
        win32print.EndPagePrinter(hprinter)
        win32print.EndDocPrinter(hprinter)
        win32print.ClosePrinter(hprinter)
        print(f"✅ Label sent successfully to printer '{printer_name}'")
        return True
    except Exception as e:
        print(f"❌ Print error: {e}")
        return False


def create_sample_label(text: str = "Hello World") -> str:
    """
    Generate a simple EZPL label.
    """
    return f"""SIZE 60 mm, 30 mm
GAP 2 mm, 0 mm
CLS
TEXT 10,10,\"1\",0,1,1,\"{text}\"
TEXT 10,40,\"1\",0,1,1,\"Godex GE330\"
BARCODE 10,80,\"128\",50,0,0,2,4,\"1234567890\"
PRINT 1
"""


if __name__ == "__main__":
    PRINTER_NAME = "Godex GE330"  # Replace with your printer name
    printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
    if PRINTER_NAME not in printers:
        print(f"⚠️ Printer '{PRINTER_NAME}' not found. Available printers:")
        for p in printers:
            print(f"  - {p}")
        exit(1)
    label = create_sample_label("Test Print")
    success = print_to_godex(PRINTER_NAME, label)
    if success:
        print("🖨️ Printing started. Please wait 2-3 seconds...")
        time.sleep(3)