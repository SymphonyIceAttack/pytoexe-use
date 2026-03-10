#from PIL import ImageGrab
from PIL import Image
from pynput import keyboard
from datetime import datetime
from pynput.keyboard import Key, Listener
import mss
#import os
import win32clipboard
import io
import tkinter as tk


DSP_MON_NO=1                                                    #  ディスプレイモニタ　No.
DSP_SIZE=1.00                                                   #  画面サイズ

def press(key):
    if key == keyboard.Key.insert:                              #　Insertキーが押された場合
        filenameX =f"Dx_{datetime.now():%Y%m%d_%H%M%S}.png"
        print(filenameX)
        blackcrt()                                              #  画面をフラッシュ(ブラック)表示
        
        with mss.mss() as screen:
            screen.shot(output=filenameX,mon=DSP_MON_NO)        # キャプチャーデータをファイルへ      

        resize(filenameX)                                       # ファイルをリサイズして保存
        clipcopy(filenameX)                                     # クリップボードにコピー

def blackcrt():                                                 # 画面をフラッシュ(ブラック)表示
    root = tk.Tk()
    root.configure(bg='black')
    root.overrideredirect(True)
    root.state('zoomed')
    root.after(100, root.destroy)                               # フラッシュ時間を 100 ミリ秒に設定
    root.mainloop()
    
def resize(filenameX):
    img = Image.open(filenameX)                                 # リサイズ前の画像を読み込み        
    (width, height) = (int(img.width *DSP_SIZE), int(img.height *DSP_SIZE))
    img_resized = img.resize((width, height))                   # 画像をリサイズする
    img_resized.save(filenameX, quality=95)                     # ファイルを保存
    

def clipcopy(filenameX):
    img = Image.open(filenameX)                                 # リサイズ後の画像を読み込み
    output = io.BytesIO()                                       # メモリストリームにBMP形式で保存してから読み出す    
    img.save(output, 'BMP')
    data = output.getvalue()[14:]

    win32clipboard.OpenClipboard()                              # クリップボードをクリアして、データをセットする
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

      
def release(key):
    if key == keyboard.Key.esc:                                 #　escが押された場合
        return False                                            #　listenerを止める


with Listener(                                                  #　Listener
        on_press=press,
        on_release=release) as listener:
    listener.join()
