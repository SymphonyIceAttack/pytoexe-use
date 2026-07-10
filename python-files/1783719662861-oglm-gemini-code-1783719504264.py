import io
import time
import sys
import socket
from flask import Flask, Response, request, jsonify
import pyautogui
from PIL import Image

app = Flask(__name__)
pyautogui.FAILSAFE = False 

# Adicionei uma tag <h3> para mostrar o IP na interface do aplicativo
PAGINA_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Acesso Remoto - 2011</title>
    <style>
        body { background: #222; color: #fff; text-align: center; font-family: Arial, sans-serif; margin-bottom: 20px; }
        h2 { margin-top: 20px; margin-bottom: 5px; }
        h3 { color: #4CAF50; margin-top: 0; margin-bottom: 15px; font-weight: normal; }
        #screen { border: 2px solid #555; cursor: crosshair; max-width: 100%; background: #000; }
        #gamepad-status { color: #aaa; font-size: 14px; margin-top: 15px; }
    </style>
</head>
<body>
    <h2>Servidor Remoto</h2>
    <h3>Conectado no IP: {{IP_SERVIDOR}}</h3>
    
    <img id="screen" src="/video" width="800" height="600" draggable="false" />
    <p id="gamepad-status">Procurando controle (Gamepad)...</p>

    <script>
        function sendCommand(query) {
            var xhr = window.XMLHttpRequest ? new XMLHttpRequest() : new ActiveXObject("Microsoft.XMLHTTP");
            xhr.open("GET", "/cmd?" + query, true);
            xhr.send();
        }

        var screenImg = document.getElementById('screen');
        var lastMove = 0;

        screenImg.onclick = function(e) {
            sendCommand("action=click");
        };

        screenImg.onmousemove = function(e) {
            var now = new Date().getTime();
            if (now - lastMove > 100) { 
                var rect = screenImg.getBoundingClientRect();
                var x = e.clientX - rect.left;
                var y = e.clientY - rect.top;
                sendCommand("action=move&x=" + x + "&y=" + y);
                lastMove = now;
            }
        };

        function updateGamepad() {
            var getGamepads = navigator.getGamepads || navigator.webkitGetGamepads || navigator.mozGetGamepads;
            
            if (getGamepads) {
                var pads = getGamepads.apply(navigator);
                var pad = pads ? pads[0] : null;
                
                if (pad) {
                    document.getElementById('gamepad-status').innerHTML = "Controle Conectado: " + (pad.id || "Genérico");
                    
                    var btnA = pad.buttons[0];
                    var btnB = pad.buttons[1];
                    
                    var aPressed = (typeof btnA == "object") ? btnA.pressed : (btnA == 1);
                    var bPressed = (typeof btnB == "object") ? btnB.pressed : (btnB == 1);

                    if (aPressed) sendCommand("action=btn_a");
                    if (bPressed) sendCommand("action=btn_b");
                } else {
                    document.getElementById('gamepad-status').innerHTML = "Nenhum controle detectado ou botão não pressionado.";
                }
            } else {
                document.getElementById('gamepad-status').innerHTML = "Gamepad API não suportada neste navegador.";
            }
            setTimeout(updateGamepad, 150);
        }
        
        setTimeout(updateGamepad, 500);
    </script>
</body>
</html>
"""

def obter_ip_local():
    """Descobre o IP local da máquina na rede conectando a um endereço fictício."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

@app.route('/')
def index():
    # Pega o IP real e substitui na string do HTML antes de enviar para o cliente
    ip_atual = obter_ip_local()
    html_pronto = PAGINA_HTML.replace("{{IP_SERVIDOR}}", ip_atual)
    return html_pronto

def generate_frames():
    while True:
        img = pyautogui.screenshot()
        img.thumbnail((800, 600))
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=40)
        frame = buffer.getvalue()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        time.sleep(0.05) 

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/cmd')
def cmd():
    action = request.args.get('action')
    
    if action == 'click':
        pyautogui.click()
        
    elif action == 'move':
        try:
            x = float(request.args.get('x', 0))
            y = float(request.args.get('y', 0))
            sw, sh = pyautogui.size()
            
            real_x = (x / 800.0) * sw
            real_y = (y / 600.0) * sh
            pyautogui.moveTo(real_x, real_y)
        except Exception:
            pass 
            
    elif action == 'btn_a':
        pyautogui.press('enter') 
        
    elif action == 'btn_b':
        pyautogui.press('esc')   
        
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    ip_atual = obter_ip_local()
    print("="*50)
    print(" SERVIDOR REMOTO INICIADO ")
    print("="*50)
    print(f"Abra o navegador no seu outro dispositivo e digite:")
    print(f" --->  http://{ip_atual}:5000  <---")
    print("="*50)
    
    app.run(host='0.0.0.0', port=5000, threaded=True)