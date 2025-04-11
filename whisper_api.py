from fastapi import FastAPI, File, UploadFile
import whisper
import tempfile
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

app = FastAPI()
model = whisper.load_model("tiny")

@app.get("/")
def root():
    return {"message": "Whisper API is running."}

@app.post("/transcribe/")
async def transcribe(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(await file.read())
        path = tmp.name
    result = model.transcribe(path, language="arabic")
    return {"text": result["text"]}
