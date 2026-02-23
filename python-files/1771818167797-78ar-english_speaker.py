from tkinter import messagebox
try:
    import PySimpleGUI as sg
    import csv
    import win32com.client
    import threading
    import time
    import os
    
except Exception as e:
    messagebox.showerror("错误", "缺少必要的依赖程序，你可以尝试重新安装程序以解决此问题。\n如果需要联系支持人员，请提供此错误代码：[WinError 3] "+str(e))
sg.theme('Material1')

menu_def = [
['文件', ['退出']],
['播放', ['开始', '停止']],
['帮助', ['关于','帮助']]
]
tab1_layout = [[sg.VPush()],
    [sg.Column([[sg.Text('', font='微软雅黑 12')]], justification='center')],
    [sg.Column([[sg.Text('欢迎使用英语单词发音工具', font='微软雅黑 72', key="-A-")]], justification='center')],
    [sg.Column([[sg.Text('', font='微软雅黑 12')]], justification='center')],

    [sg.Column([[sg.Text('', font='微软雅黑 32', key="-D-")]], justification='center')],
    [sg.Column([[sg.Text('', font='微软雅黑 12')]], justification='center')],
    [sg.Column([[sg.Text('请先配置文件，然后点击【开始播放】', font='微软雅黑 52', key="-B-")]], justification='center')],
    [sg.Column([[sg.Text('', font='微软雅黑 12')]], justification='center')],
    [sg.Column([[sg.Text('', font='微软雅黑 12', key="-C-")]], justification='center')],
    [sg.Column([[sg.Text('', font='微软雅黑 12')]], justification='center')],
    [sg.Column([
        [sg.B('开始播放', font='微软雅黑 15', key="-START-"),
        sg.B('暂停', font='微软雅黑 15', key="-NEXT-", disabled=True,visible=False),
         sg.B('停止播放', font='微软雅黑 15', key="-PAUSE-", disabled=True),
         ]
    ], justification='center')],
[sg.VPush()],]

tab2_layout = [[sg.T("CSV文件格式：第一列【单词】，第二列【音标】，第三列【释义】，第四列【例句】，无须标题行。",font='微软雅黑 15')],
    [sg.T('选择CSV文件：',font='微软雅黑 15'),
     sg.In(key='-file_dir-',font='微软雅黑 15', size=(100,1)),
     sg.FileBrowse("选择",font='微软雅黑 15',file_types=(("CSV Files", "*.csv"),))],
     [sg.T("")],
    [sg.Column([[sg.B("关于我们",key="-ABOUT_US-",font='微软雅黑 15'),sg.B("获取帮助",key="-ABOUT_CS-",font='微软雅黑 15')]], justification='center')],
]

layout = [[sg.Menu(menu_def)],[sg.TabGroup([[sg.Tab('播放', tab1_layout, title_color='blue'), sg.Tab('配置', tab2_layout)]])],[sg.StatusBar('欢迎您使用英语单词发音工具！', key='-STATUS-')]]

window = sg.Window('英语单词发音工具', layout, size=(1470, 680))

window.set_icon('icon.ico')

is_playing = False
current_index = 0
csv_data = []

def speak_text(text):

    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Rate = 0
        speaker.Volume = 100
        speaker.Speak(text)
    except Exception as e:
        print(f"朗读出错: {e}")
        messagebox.showerror("错误", "朗读插件连接失败，你可以尝试重新安装程序或更换CSV文件以解决此问题。\n如果需要联系支持人员，请提供此错误代码：[WinError 5] "+str(e))

def parse_csv_to_list(file_path):

    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if row:  
                    data.append(row)
        return data
    except Exception as e:
        messagebox.showerror("错误", "缺少必要的依赖程序，你可以尝试重新安装程序以解决此问题。\n如果需要联系支持人员，请提供此错误代码：[WinError 4] 解析CSV文件错误。"+str(e))
        return None

def play_next_item():

    global current_index, is_playing
    
    if current_index >= len(csv_data):
        is_playing = False
        window['-START-'].update(disabled=False)
        window['-PAUSE-'].update(disabled=True)
        window['-NEXT-'].update(disabled=True)
        return
    
    row = csv_data[current_index]
    

    for tj, text in enumerate(row):
        if tj < 4:  # 只处理前4列
            LLL = ["-A-", "-D-", "-B-", "-C-"]
            window[LLL[tj]].update(value=text)
    for tj, text in enumerate(row):        
            if tj != 1 and tj != 3:  
                if tj==0:
                    for cccc in range(2):
                        threading.Thread(target=speak_text, args=(text,), daemon=True).start()
                        time.sleep(2)  
                else:
                    threading.Thread(target=speak_text, args=(text,), daemon=True).start()
                    time.sleep(2)  
    if is_playing == False:
        return
    current_index += 1    
    if is_playing and current_index < len(csv_data):
        time.sleep(2)
        play_next_item()  
def start_playback():
    global is_playing, current_index, csv_data
    file_path = values["-file_dir-"]
    if not file_path:
        print("请先在设置页面选择CSV文件再点击【开始播放】按钮")
        messagebox.showerror("错误", "请先在设置页面选择CSV文件再点击【开始播放】按钮\n如果需要联系支持人员，请提供此错误代码：\n[WinError 1] not file path of csv")
        return    
    # 解析CSV文件
    csv_data = parse_csv_to_list(file_path)
    if not csv_data:
        return    
    current_index = 0
    is_playing = True
    window['-START-'].update(disabled=True)
    window['-PAUSE-'].update(disabled=False)
    window['-NEXT-'].update(disabled=False)
    play_next_item()
def pause_playback():
    """暂停播放"""
    global is_playing
    is_playing = False
    window['-START-'].update(disabled=False)
    window['-PAUSE-'].update(disabled=True)
while True:
    event, values = window.read()
    if event == "-ABOUT_US-" or event == "-ABOUT_CS-" or event=="帮助" or event=="关于":
        try:
            os.startfile('about_us.txt')
        except Exception as e:
            messagebox.showerror("错误", "缺少必要的依赖程序，你可以尝试重新安装程序以解决此问题。\n如果需要联系支持人员，请提供此错误代码：\n"+str(e))
    if event == sg.WIN_CLOSED or event is None or event=="退出":
        break
    if event == "-START-" or event=="开始":
        threading.Thread(target=start_playback, daemon=True).start()
    elif event == "-PAUSE-" or event=='停止':
        pause_playback()
    elif event == "-NEXT-":
        if not is_playing:
            is_playing = True
            window['-START-'].update(disabled=True)
            window['-PAUSE-'].update(disabled=False)
        play_next_item()
window.close()