# -*- coding: utf-8 -*-
"""
Voice Server - HTTP API for UE5 Voice Integration
Runs faster-whisper as a local HTTP service.
UE5 sends audio via VaRest → server returns recognized text.

Usage: python voice_server.py [--port 9876]
"""
import argparse
import json
import os
import sys
import tempfile
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# ======================== Config ========================
MODEL = "small"
CACHE = os.path.join(os.path.dirname(__file__), "..", ".whisper_cache")

# ======================== Init ASR ========================
asr_model = None

def init_model():
    global asr_model
    print("[VoiceServer] Loading faster-whisper ({})...".format(MODEL))
    from faster_whisper import WhisperModel
    asr_model = WhisperModel(MODEL, device="cpu", compute_type="int8", download_root=CACHE)
    print("[VoiceServer] Model ready")

# ======================== Recognizer ========================
def recognize(wav_bytes):
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        with open(tmp_path, "wb") as f:
            f.write(wav_bytes)

        segments, _ = asr_model.transcribe(
            tmp_path, language="zh", beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        texts = [s.text.strip() for s in segments]
        return "".join(texts)
    except Exception as e:
        return "[ERROR: {}]".format(str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try: os.unlink(tmp_path)
            except: pass

# ======================== HTTP Server ========================
class VoiceHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/recognize":
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                self.respond(400, {"error": "No audio data"})
                return
            wav_bytes = self.rfile.read(length)
            result = recognize(wav_bytes)
            self.respond(200, {"text": result})
        elif self.path == "/status":
            self.respond(200, {"status": "ok", "model": MODEL})
        else:
            self.respond(404, {"error": "Not found"})

    def respond(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        if "/recognize" in str(args):
            print("[VoiceServer] Recognized: {}".format(args[0].split()[-1] if args else "?"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9876, help="Server port")
    parser.add_argument("--model", default="small", help="Whisper model size")
    args = parser.parse_args()

    global MODEL
    MODEL = args.model

    init_model()

    server = HTTPServer(("127.0.0.1", args.port), VoiceHandler)
    print("[VoiceServer] Listening on http://127.0.0.1:{}".format(args.port))
    print("[VoiceServer] POST /recognize  - send WAV bytes, get text back")
    print("[VoiceServer] GET  /status     - health check")
    print("[VoiceServer] Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print("[VoiceServer] Stopped")

if __name__ == "__main__":
    main()
