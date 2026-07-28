import webview

url = "https://lucifer-dennica.github.io/wot-tactics/"

# Создаём окно с сайтом
webview.create_window(
    title="WoT Tactics",
    url=url,
    width=1280,
    height=800,
    resizable=True,
    fullscreen=False,
    min_size=(800, 600)
)

# Запускаем приложение
webview.start()