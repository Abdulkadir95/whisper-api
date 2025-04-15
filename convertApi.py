from flask import Flask, request, jsonify
import azure.cognitiveservices.speech as speechsdk
import os
import subprocess
import uuid

app = Flask(__name__)

# إعدادات Azure
speech_key = "6MKmoZxlcD6NsdzJZCBqpVbd56lqIquxAZYyA60Uude2VOONwDnwJQQJ99BDAC3pKaRXJ3w3AAAYACOGxyYb"
service_region = "eastasia"

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_recognition_language = "ar-SA"

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'file' not in request.files:
        return jsonify({"error": "يرجى رفع ملف صوتي"}), 400

    file = request.files['file']
    original_ext = os.path.splitext(file.filename)[1]
    unique_id = uuid.uuid4().hex

    original_filename = f"{unique_id}{original_ext}"
    converted_filename = f"{unique_id}_converted.wav"

    # حفظ الملف المرفوع
    file.save(original_filename)

    # تحويل الملف إلى WAV PCM 16kHz mono
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", original_filename,
            "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", converted_filename
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        os.remove(original_filename)
        return jsonify({"error": "فشل في تحويل الملف الصوتي. تأكد من أن الصيغة مدعومة."}), 500

    # تحويل الصوت إلى نص باستخدام Azure
    try:
        audio_config = speechsdk.audio.AudioConfig(filename=converted_filename)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        result = speech_recognizer.recognize_once()
    except Exception as e:
        os.remove(original_filename)
        os.remove(converted_filename)
        return jsonify({"error": str(e)}), 500

    # حذف الملفات المؤقتة
    os.remove(original_filename)
    os.remove(converted_filename)

    # التعامل مع النتائج
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return jsonify({"text": result.text})
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return jsonify({"error": "لم يتم التعرف على أي كلام"}), 204
    else:
        return jsonify({"error": str(result.reason)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050, debug=True)
