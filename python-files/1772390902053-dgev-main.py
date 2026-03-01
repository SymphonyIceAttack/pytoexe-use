import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote

# Папка для загруженных файлов
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class FileUploadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Отображает HTML‑форму для загрузки файла"""
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = """
        <html>
        <head><title>Загрузка файлов</title></head>
        <body>
            <h1>Загрузите файл</h1>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file" required>
                <input type="submit" value="Загрузить">
            </form>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        """Обрабатывает загрузку файла"""
        if self.path == "/upload":
            content_type = self.headers.get('content-type')
            if not content_type or 'multipart/form-data' not in content_type:
                self.send_error(400, "Неверный тип контента")
                return

            # Извлекаем boundary из заголовка Content-Type
            boundary = content_type.split("boundary=")[1].encode()
            data = self.rfile.read()

            # Разделяем данные по boundary
            parts = data.split(b'--' + boundary)
            for part in parts:
                if b'filename=' in part:
                    # Находим имя файла
                    filename_start = part.find(b'filename="') + 10
                    filename_end = part.find(b'"', filename_start)
                    filename = part[filename_start:filename_end].decode()
                    filename = unquote(filename)

                    # Находим начало данных файла (после заголовка части)
                    file_data_start = part.find(b'\r\n\r\n') + 4
                    file_data_end = part.rfind(b'\r\n--')
                    file_data = part[file_data_start:file_data_end]

                    # Сохраняем файл
                    filepath = os.path.join(UPLOAD_DIR, filename)
                    with open(filepath, 'wb') as f:
                        f.write(file_data)

            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_error(404, "Страница не найдена")

def run_server():
    server_address = ('0.0.0.0', 10230)
    httpd = HTTPServer(server_address, FileUploadHandler)
    print(f"Сервер запущен на порту 10230. Откройте http://0.0.0.0:10230")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")

if __name__ == '__main__':
    run_server()
