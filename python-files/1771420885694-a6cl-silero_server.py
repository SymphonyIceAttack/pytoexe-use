from flask import Flask, request, jsonify
import torch
import sounddevice as sd
import os
import time
import base64
import numpy as np

app = Flask(__name__)

torch.set_num_threads(4)
model_path = './silero/silero_model.pt'

if not os.path.exists(model_path):
    torch.hub.download_url_to_file(
        'https://models.silero.ai/models/tts/ru/v5_ru.pt',
        model_path
    )

model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
model.to(torch.device('cpu'))

@app.route('/speak', methods=['POST'])
def speak():
    data = request.json
    text = data.get('text', '')
    
    audio = model.apply_tts(
        text=text,
        speaker='kseniya',
        sample_rate=48000,
        put_accent=True,
        put_yo=True
    )

    sd.play(audio.numpy(), 48000 * 1.05)
    time.sleep((len(audio) / 48000) + 0.5)
    sd.wait()
    
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='localhost', port=5000)
