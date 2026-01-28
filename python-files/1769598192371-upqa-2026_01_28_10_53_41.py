import os  # For USB as a file printer

# Option 2: Via USB as a file printer (Windows)
def print_via_usb_windows(printer_name="Godex G330"):
    ezpl_commands = (
        "~D\n"
        "A50,50,0,3,2,2,\"PRODUCT\"\n"
        "B50,100,0,1,2,6,150,\"456789012345\"\n"
        "~E\n"
    )
    
    import tempfile
    import win32print
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.prn') as f:
        f.write(ezpl_commands)
        temp_file = f.name
    
    try:
        printer_handle = win32print.OpenPrinter(printer_name)
        win32print.StartDocPrinter(printer_handle, 1, ("Label", None, "RAW"))
        win32print.StartPagePrinter(printer_handle)
        win32print.WritePrinter(printer_handle, ezpl_commands.encode('ascii'))
        win32print.EndPagePrinter(printer_handle)
        win32print.EndDocPrinter(printer_handle)
        win32print.ClosePrinter(printer_handle)
        print("Печать через Windows API выполнена")
    except Exception as e:
        print(f"Ошибка печати: {e}")
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)