import os
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext

HTML_FILENAME = "labels_output.html"

def generate_html_labels():
    raw_data = text_area.get("1.0", tk.END).strip()
    if not raw_data:
        messagebox.showerror("Ошибка", "Вставьте данные для этикеток!")
        return

    lines = raw_data.split('\n')
    labels_html = ""
    labels_count = 0

    for line in lines:
        if not line.strip():
            continue
        
        # Разделяем по табуляции (Excel) или точке с запятой
        columns = line.split('\t') if '\t' in line else line.split(';')
        while len(columns) < 4:
            columns.append("")

        col1, col2, col3, col4 = [col.strip() for col in columns[:4]]

        # Генерируем HTML-код для одной этикетки 100х50мм с отступами 5мм
        labels_html += f"""
        <div class="label">
            <div class="printable-area">
                <!-- Штрихкод и текст из 3-го столбца -->
                <div class="barcode-box">*{col3}*</div>
                <div class="col3-text">{col3}</div>
                
                <!-- Нижние колонки -->
                <div class="columns-container">
                    <div class="col-left">
                        <div class="title-text">Дата производства</div>
                        <div class="value-text-bold">{col4}</div>
                    </div>
                    <div class="col-right">
                        <div class="value-text">{col1}</div>
                        <div class="value-text-bold">{col2}</div>
                    </div>
                </div>
            </div>
        </div>
        """
        labels_count += 1

    # Полный шаблон HTML страницы с CSS-стилями для точной печати и шрифтом штрихкода
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Печать этикеток</title>
    <!-- Подключаем шрифт штрихкода Libre Barcode 39 напрямую из интернета -->
    <link rel="preconnect" href="https://googleapis.com">
    <link rel="preconnect" href="https://gstatic.com" crossorigin>
    <link href="https://googleapis.com/css2?family=Libre+Barcode+39&display=swap" rel="stylesheet">
    <style>
        @page {{
            size: 100mm 50mm;
            margin: 0;
        }}
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Arial', sans-serif;
            background-color: #f0f0f0;
            -webkit-print-color-adjust: exact;
        }}
        .label {{
            width: 100mm;
            height: 50mm;
            background: white;
            position: relative;
            box-sizing: border-box;
            page-break-after: always;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .printable-area {{
            width: 90mm;
            height: 40mm;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            box-sizing: border-box;
        }}
        .barcode-box {{
            font-family: 'Libre+Barcode+39', 'Libre Barcode 39', cursive;
            font-size: 38px;
            line-height: 1;
            height: 8mm;
            margin-top: 0px;
            overflow: hidden;
            width: 100%;
        }}
        .col3-text {{
            font-size: 11pt;
            font-weight: bold;
            margin-top: 4mm;
            width: 100%;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .columns-container {{
            display: flex;
            width: 100%;
            margin-top: auto; /* Прижимает колонки к низу печатной области */
            margin-bottom: 2mm;
        }}
        .col-left {{
            width: 26mm;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 14mm;
        }}
        .col-right {{
            width: 64mm;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 14mm;
        }}
        .title-text {{
            font-size: 9pt;
        }}
        .value-text {{
            font-size: 10pt;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .value-text-bold {{
            font-size: 11pt;
            font-weight: bold;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        /* Стили для экрана (чтобы видеть предпросмотр в браузере) */
        @media screen {{
            body {{ padding: 20px; display: flex; flex-direction: column; align-items: center; gap: 20px; }}
            .label {{ border: 1px dashed #999; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
        }}
    </style>
</head>
<body>
    {labels_html}
    <script>
        // Автоматически вызываем окно печати при открытии страницы
        window.onload = function() {{ window.print(); }}
    </script>
</body>
</html>
"""

    try:
        with open(HTML_FILENAME, "w", encoding="utf-8") as f:
            f.write(full_html)
        
        # Открываем созданный HTML файл в дефолтном браузере
        if sys.platform == 'win32':
            os.startfile(HTML_FILENAME)
        elif sys.platform == 'darwin':
            import subprocess
            subprocess.Popen(['open', HTML_FILENAME])
        else:
            import subprocess
            subprocess.Popen(['xdg-open', HTML_FILENAME])
            
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось создать файл: {str(e)}")

# --- ИНТЕРФЕЙС ПРОГРАММЫ ---
root = tk.Tk()
root.title("Генератор этикеток 100х50 мм")
root.geometry("550x420")

label_info = tk.Label(root, text="Вставьте строки из Excel (4 столбца):", font=("Arial", 10))
label_info.pack(pady=10)

text_area = scrolledtext.ScrolledText(root, width=60, height=15)
text_area.pack(pady=5)

btn_generate = tk.Button(
    root, 
    text="🖨️ Создать макет и открыть печать", 
    command=generate_html_labels, 
    bg="#4CAF50", 
    fg="white", 
    font=("Arial", 11, "bold")
)
btn_generate.pack(pady=15)

root.mainloop()
