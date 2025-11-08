
import tkinter as tk
from tkinter import ttk
import threading, queue, time
import traceback

# Optional deps:
# - speech_recognition
# - pyttsx3

try:
    import speech_recognition as sr
except Exception:
    sr = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

class VoiceEngine:
    def __init__(self):
        self.tts_engine = None
        if pyttsx3:
            try:
                self.tts_engine = pyttsx3.init()
            except Exception:
                self.tts_engine = None

    def say(self, text: str):
        if not text or not self.tts_engine:
            return
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

class SRWorker(threading.Thread):
    def __init__(self, out_q: queue.Queue, stop_event: threading.Event, energy_thresh: int = 300):
        super().__init__(daemon=True)
        self.out_q = out_q
        self.stop_event = stop_event
        self.energy_thresh = energy_thresh
        self.recognizer = sr.Recognizer() if sr else None

    def run(self):
        if not self.recognizer or not sr:
            self.out_q.put(("error", "speech_recognition chưa được cài đặt"))
            return
        self.recognizer.energy_threshold = self.energy_thresh
        self.recognizer.pause_threshold = 0.6
        with sr.Microphone() as mic:
            try:
                self.recognizer.adjust_for_ambient_noise(mic, duration=0.5)
            except Exception:
                pass
            while not self.stop_event.is_set():
                try:
                    audio = self.recognizer.listen(mic, timeout=5, phrase_time_limit=10)
                    try:
                        text = self.recognizer.recognize_google(audio, language="vi-VN")
                    except Exception as e:
                        text = ""
                    self.out_q.put(("transcript", text))
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    self.out_q.put(("error", f"Lỗi SR: {e}"))
                    time.sleep(0.3)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Voice Assistant (Stable)")
        self.geometry("700x480")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.txt = tk.Text(self, wrap="word", state="disabled")
        self.txt.pack(fill="both", expand=True, padx=8, pady=8)

        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack(fill="x", padx=8, pady=8)

        self.btn_listen = ttk.Button(self.btn_frame, text="Start Listening", command=self.toggle_listen)
        self.btn_listen.pack(side="left")

        self.status = tk.StringVar(value="Idle")
        ttk.Label(self.btn_frame, textvariable=self.status).pack(side="right")

        self.voice = VoiceEngine()
        self.out_q = queue.Queue()
        self.stop_event = threading.Event()
        self.worker = None

        self.after(50, self.poll_queue)

    def log(self, msg: str):
        self.txt.configure(state="normal")
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def toggle_listen(self):
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self.status.set("Stopping...")
            self.btn_listen.configure(text="Start Listening", state="disabled")
        else:
            self.stop_event.clear()
            self.worker = SRWorker(self.out_q, self.stop_event)
            self.worker.start()
            self.status.set("Listening...")
            self.btn_listen.configure(text="Stop Listening")

    def poll_queue(self):
        try:
            while True:
                topic, payload = self.out_q.get_nowait()
                if topic == "transcript":
                    text = payload or "(không nghe rõ)"
                    self.log(f"Bạn nói: {text}")
                    # Simple echo. Hook NLU/LLM here.
                    reply = f"Bạn vừa nói: {text}"
                    self.log(f"Trợ lý: {reply}")
                    self.voice.say(reply)
                elif topic == "error":
                    self.log(f"[Lỗi] {payload}")
                    self.status.set("Error")
        except queue.Empty:
            pass
        # Update button state after stopping
        if self.worker and not self.worker.is_alive():
            self.btn_listen.configure(text="Start Listening", state="normal")
            self.status.set("Idle")
        self.after(50, self.poll_queue)

    def on_close(self):
        try:
            self.stop_event.set()
        except Exception:
            pass
        self.after(200, self.destroy)

if __name__ == "__main__":
    App().mainloop()
