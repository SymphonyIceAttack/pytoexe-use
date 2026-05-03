from flask import Flask, request, jsonify
import win32print

app = Flask(__name__)

# Получаем принтер по умолчанию
printer_name = win32print.GetDefaultPrinter()

def print_raw(data):
    hPrinter = win32print.OpenPrinter(printer_name)
    
    hJob = win32print.StartDocPrinter(hPrinter, 1, ("Print Job", None, "RAW"))
    win32print.StartPagePrinter(hPrinter)
    
    win32print.WritePrinter(hPrinter, data.encode('utf-8'))
    
    win32print.EndPagePrinter(hPrinter)
    win32print.EndDocPrinter(hPrinter)
    win32print.ClosePrinter(hPrinter)

@app.route('/print', methods=['POST'])
def print_route():
    try:
        content = request.json.get("text", "")
        print_raw(content)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/')
def home():
    return "Print server is running"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)