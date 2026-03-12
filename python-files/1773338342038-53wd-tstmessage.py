import socket
import os
import threading
import random
import flet as ft
import pyperclip

def App(page: ft.Page):
    global File, SERVER_IP, PORT, OnServer, server_socket, client_threads
    File = None
    OnServer = False
    server_socket = None
    client_threads = []

    page.title = "Send"
    page.window.width = 400
    page.window.height = 600
    page.window.resizable = False
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)

    async def app_update():
        page.update()

    async def ChooseFile():
        global File
        File = await ft.FilePicker().pick_files(dialog_title="Выберите видео файл:")
        filename.value = "Файл: "
        filename.value += str(File[0].name) if len(str(File[0].name)) <= 37 else str(File[0].name)[:37]+"..."
        File = File[0].path

    def StopServer():
        global server_socket, client_threads, OnServer

        if server_socket:
            try:
                server_socket.close()
            except:
                pass
        for thread in client_threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        client_threads.clear()
        print("Сервер остановлен.")


    def StartSendFile():
        global OnServer
        if startbutton.content == "Старт:":
            OnServer = True
            startbutton.bgcolor=ft.Colors.RED_900
            startbutton.icon=ft.Icons.STOP_CIRCLE
            startbutton.content="Стоп:"
            threading.Thread(target=SendFile).start()
        else:
            OnServer = False
            startbutton.bgcolor=ft.Colors.GREEN_900
            startbutton.icon=ft.Icons.PLAY_ARROW
            startbutton.content="Старт:"
            StopServer()

    def SendFile():
        global OnServer, File
        if OnServer == True:
            try: 
                if not os.path.exists(File):
                    StartSendFile()
                    page.show_dialog(ft.AlertDialog(title=ft.Text("Ошибка"),content=ft.Text(f"Файл не был найден!"),open=True,actions=[ft.TextButton("Понятно", on_click=lambda e: page.pop_dialog())]))
                    page.run_task(app_update)
                    choosebutton.disabled = False
                else:
                    choosebutton.disabled = True
                    OnServer = True
                    file_size = os.path.getsize(File)
                    def handle_client(conn, addr):
                        global OnServer
                        with conn:
                            print(f"Подключён: {addr}")
                            conn.send(File.encode())
                            conn.recv(1024)
                            conn.send(str(file_size).encode())

                            sent_bytes = 0
                            with open(File, 'rb') as f:
                                chunk = f.read(4096)
                                while chunk and OnServer:
                                    conn.sendall(chunk)
                                    sent_bytes += len(chunk)
                                    percent = (sent_bytes / file_size) * 100
                                    print(f"[{addr}] Отправлено: {percent:.2f}% ({sent_bytes}/{file_size} байт)")
                                    chunk = f.read(4096)
                                    if not OnServer:
                                        break
                            print(f"[{addr}] Файл отправлен полностью.")
                            conn.send(b'END')

                    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    server_socket.bind((SERVER_IP, PORT))
                    server_socket.listen()
                    print(f"Сервер запущен {SERVER_IP}:{PORT}, ожидаем подключений...")
                    while OnServer:
                        server_socket.settimeout(1.0)
                        try:
                            conn, addr = server_socket.accept()
                            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                            client_thread.start()
                            client_threads.append(client_thread)
                            if OnServer == False:
                                print("Сервер остановлен.")
                                StartSendFile()
                                choosebutton.disabled = False
                            return 0
                        except socket.timeout:
                            continue
            except:
                StartSendFile()
                choosebutton.disabled = False
                page.show_dialog(ft.AlertDialog(title=ft.Text("Ошибка"),content=ft.Text(f"Файл не был найден!"),open=True,actions=[ft.TextButton("Понятно", on_click=lambda e: page.pop_dialog())]))
                page.run_task(app_update)
        else:
            StartSendFile()
            choosebutton.disabled = False

    def get_ip():
        global SERVER_IP
        hostname = socket.gethostname()
        SERVER_IP = socket.gethostbyname(hostname)
        return SERVER_IP
    
    def get_port():
        global PORT
        PORT = random.randint(1024,65535)
        return PORT
    
    def Copy_ip_port():
        pyperclip.copy(f"{SERVER_IP}:{PORT}")

    scrollconnect = ft.Column(height=210,width=542,scroll=ft.ScrollMode.ALWAYS)
    startbutton = ft.FloatingActionButton(width=90,height=130,content="Старт:",bgcolor=ft.Colors.GREEN_900,icon=ft.Icons.PLAY_ARROW,on_click=StartSendFile)
    choosebutton = ft.FloatingActionButton(width=115,height=130,content="Выбрать\nфайл:",icon=ft.Icons.ADD_TO_PHOTOS,on_click=ChooseFile)
    filename = ft.Text(value="Выберите файл:")

    toptabs = ft.Tabs(selected_index=0, length=2, animation_duration=250,expand=True, content=ft.Column(expand=True,controls=[ft.TabBar(tabs=[
        ft.Tab(label="Отправка:",icon=ft.icons.Icons.SEND), 
        ft.Tab(label="Получение:",icon=ft.icons.Icons.ARCHIVE)]),ft.TabBarView(expand=True,controls=[

        ft.Container(content=ft.Column(width=page.window.width,height=page.window.height,controls=[ft.Container(height=(int(page.window.height)/2.8),width=page.window.width,content=ft.Container(height=(int(page.window.height)/4),width=(int(page.window.width)/1.7),bgcolor=page.theme.color_scheme_seed, border_radius=10,content=ft.Row(height=(int(page.window.height)/4),width=(int(page.window.width)/1.7),controls=[startbutton,choosebutton],alignment=ft.MainAxisAlignment.CENTER)),alignment=ft.alignment.Alignment.CENTER), filename, ft.Container(height=(int(page.window.height)/3),border=ft.border.all(1,page.theme.color_scheme_seed),content=scrollconnect, border_radius=10)])),
        ft.Container(content=ft.Text(value="Привет"))
        ])]))
    
    iptext = ft.Text(value=f"IP: {get_ip()}:{get_port()}",size=20)
    ipcopy = ft.FloatingActionButton(width=35,height=35,icon=ft.Icons.COPY,on_click=Copy_ip_port)
    scrollconnect.controls.append(ft.Row(ft.Container(width=int(scrollconnect.width)/1.6,height=60,bgcolor=page.theme.color_scheme_seed,border_radius=10,padding=8,content=ft.Row(controls=[iptext,ipcopy])),alignment=ft.MainAxisAlignment.CENTER))

    page.add(toptabs)

ft.app(target=App)
