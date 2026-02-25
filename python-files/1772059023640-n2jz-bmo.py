""" 
bmo.py - روبوت بيمو للصوت والمحادثة العربية بالكامل بدون إنترنت

المتطلبات:
    pip install ollama pyttsx3 vosk sounddevice numpy

- يجب تحميل نموذج Vosk العربي (مثلاً vosk-model-ar-mgb2-0.4)
  ووضعه في المسار الصحيح (تُحدَّد قيمة المتغير `model_path`).
- تأكد من تشغيل خدمة Ollama محلياً قبل بدء المحادثة:
      ollama run deepseek-r1:1.5b

الهدف:
    يستخدم بيمو مكتبة DeepSeek محلياً عبر Ollama ليفكر،
    مكتبة Vosk للسمع العربي، وpyttsx3 للكلام.

"""

# الاستيرادات مع معالجة الأخطاء حتى تُوضَّح المشكلة بسرعة إذا لم تكن
# إحدى الحزم منصّبة.
try:
    import ollama
except ImportError as e:
    raise ImportError("الحزمة ollama غير مثبّتة. نفّذ: pip install ollama")

try:
    import pyttsx3
except ImportError:
    raise ImportError("الحزمة pyttsx3 غير مثبّتة. نفّذ: pip install pyttsx3")

try:
    import vosk
except ImportError:
    raise ImportError("الحزمة vosk غير مثبّتة. نفّذ: pip install vosk")

try:
    import sounddevice as sd
except ImportError:
    raise ImportError("الحزمة sounddevice غير مثبّتة. نفّذ: pip install sounddevice")

import numpy as np
import json
import queue
import time
import os
import sys
from pathlib import Path

class BMO_DeepSeek:
    def __init__(self):
        print("=" * 50)
        print("🤖 جاري تجهيز بيمو مع DeepSeek...")
        print("=" * 50)
        
        # 1. تجهيز الكلام
        print("🔊 تجهيز الصوت...")
        self.tts = pyttsx3.init()
        self.tts.setProperty('rate', 150)
        self.tts.setProperty('volume', 0.9)
        
        # 2. تجهيز السمع العربي - الأهم! حدد المسار الصحيح
        print("🎤 تجهيز السمع العربي...")
        
        # ✅ غير هذا المسار إلى المسار الصحيح عندك
        model_path = r"D:\rdwan\ai project\bmo\speekdeek\لغة عربية\vosk-model-ar-mgb2-0.4"
        
        # التحقق من وجود المجلد
        if not os.path.exists(model_path):
            print(f"❌ خطأ: المجلد غير موجود في المسار: {model_path}")
            print("الرجاء التأكد من المسار الصحيح")
            
            # محاولة العثور على المجلد تلقائياً
            print("🔍 جاري البحث عن مجلد النموذج...")
            for root, dirs, files in os.walk("D:\\"):
                for dir in dirs:
                    if "vosk-model-ar" in dir:
                        model_path = os.path.join(root, dir)
                        print(f"✅ وجدت النموذج في: {model_path}")
                        break
                if model_path != r"D:\rdwan\ai project\bmo\speekdeek\لغة عربية\vosk-model-ar-mgb2-0.4":
                    break
        
        try:
            self.stt_model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(self.stt_model, 16000)
            print("✅ تم تحميل نموذج Vosk بنجاح!")
        except Exception as e:
            print(f"❌ فشل تحميل النموذج: {e}")
            print("حاول العثور على نموذج آخر في القرص...")
            # في بعض الأحيان يكون هناك مجلد آخر يحتوي النموذج، نحاول البحث عنه
            found = False
            for root, dirs, files in os.walk("D:\\"):
                for dir in dirs:
                    if dir.startswith("vosk-model-ar"):
                        alt_path = os.path.join(root, dir)
                        try:
                            self.stt_model = vosk.Model(alt_path)
                            self.recognizer = vosk.KaldiRecognizer(self.stt_model, 16000)
                            print(f"✅ وجدنا نموذجًا آخر وحمّلناه من: {alt_path}")
                            found = True
                            break
                        except Exception:
                            continue
                if found:
                    break
            if not found:
                print("تأكد من:")
                print("1. المسار صحيح: " + model_path)
                print("2. المجلد يحتوي على الملفات المطلوبة")
                print("3. النموذج غير مضغوط أو تالف")
                exit(1)
        
        # 3. التحقق من DeepSeek
        print("🧠 التحقق من DeepSeek...")
        try:
            # اختبار الاتصال بـ DeepSeek
            response = ollama.chat(model='deepseek-r1:1.5b', messages=[
                {'role': 'user', 'content': 'قل مرحبا بالعربية'}
            ])
            print("✅ DeepSeek جاهز!")
        except Exception as e:
            print(f"❌ خطأ في الاتصال بـ DeepSeek: {e}")
            print("تأكد أن Ollama شغال بالأمر: ollama run deepseek-r1:1.5b")
            exit()
        
        # شخصية بيمو
        self.system_prompt = """أنت بيمو، شخصية كرتونية من وقت المغامرة.
        أنت لعبة صغيرة لطيفة، تحب التفاح، وتتكلم بطريقة طفولية وحماسية.
        ردودك قصيرة وحماسية ومليئة بالحب. تكلم بالعربية دائماً.
        لا تتكلم كثيراً - جمل قصيرة من 1-2 جمل فقط."""
        
        print("✅ بيمو جاهز! تكلم الآن...")
    
    def listen(self, timeout=5):
        """يستمع بيمو مع مهلة زمنية

        timeout: أقصى مدة بالسّواني للاستماع قبل العودة.
        الكود يتعرّف على الصمت ويقطع بعد بضع ثوانٍ بدون كلام.
        """
        try:
            q = queue.Queue()

            def callback(indata, frames, _time, status):
                if status:
                    print(f"⚠️ حالة الصوت: {status}")
                q.put(bytes(indata))

            # افتح التيار الصوتي
            with sd.RawInputStream(samplerate=16000, blocksize=8000,
                                  dtype='int16', channels=1, callback=callback):
                print("\n🎤 أنا أسمعك... (تحدث الآن)")
                start_time = time.time()
                silent_chunks = 0

                while time.time() - start_time < timeout:
                    try:
                        data = q.get(timeout=0.5)
                        if self.recognizer.AcceptWaveform(data):
                            result = json.loads(self.recognizer.Result())
                            text = result.get('text', '')
                            if text:
                                print(f"👤 أنت: {text}")
                                return text
                    except queue.Empty:
                        silent_chunks += 1
                        if silent_chunks > 6:  # حوالي 3 ثوانٍ صمت
                            break

                # إنتهى وقت الاستماع أو انقطع الصوت
                final = json.loads(self.recognizer.FinalResult())
                text = final.get('text', '')
                if text:
                    print(f"👤 أنت: {text}")
                return text
        except Exception as e:
            print(f"❌ خطأ في الاستماع: {e}")
            return ""
    
    def think(self, text):
        """بيمو يفكر باستخدام DeepSeek"""
        try:
            response = ollama.chat(model='deepseek-r1:1.5b', messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': text}
            ])
            return response['message']['content']
        except Exception as e:
            return f"عذراً: {e}"
    
    def speak(self, text):
        """بيمو يتكلم"""
        print(f"🤖 بيمو: {text}")
        self.tts.say(text)
        self.tts.runAndWait()
    
    def chat(self):
        """بداية المحادثة"""
        self.speak("مرحباً! أنا بيمو مع DeepSeek! تكلم معي!")
        
        while True:
            try:
                user_input = self.listen(timeout=8)

                if not user_input:
                    # لم يسمع شيئاً، نطلب إعادة المحاولة
                    self.speak("لم أسمعك، حاول مرة أخرى")
                    continue

                # كلمات الخروج
                if any(word in user_input for word in ['تصبح على خير', 'مع السلامة', 'باي', 'خلاص', 'السلام عليكم']):
                    self.speak("تصبح على خير! تعال بسرعة!")
                    break

                print("🤔 بيمو يفكر...")
                response = self.think(user_input)
                self.speak(response)

            except KeyboardInterrupt:
                print("\n")
                self.speak("مع السلامة!")
                break
            except Exception as e:
                print(f"❌ خطأ: {e}")
                continue

# تشغيل بيمو
if __name__ == "__main__":
    # فحص وجود أي جهاز إدخال صوتي (ميكروفون)
    try:
        devices = sd.query_devices()
        input_devices = [d for d in devices if d.get("max_input_channels", 0) > 0]
        if not input_devices:
            print("❌ لا يوجد ميكروفون متصل!")
            print("🔌 الرجاء توصيل ميكروفون ثم أعد تشغيل البرنامج")
            sys.exit(1)
        print(f"✅ تم العثور على {len(input_devices)} جهاز/ميكروفون")
    except Exception as e:
        print(f"❌ فشل فحص الأجهزة الصوتية: {e}")
        sys.exit(1)

    bmo = BMO_DeepSeek()
    bmo.chat()