import time
import threading
import wave
import os
import pyaudio
import struct
import math
from datetime import datetime
from memora_os.core.events import Event
from memora_os.config import settings

class AudioListener:
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.running = False
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.threshold = 1000 # Energy threshold for "Voice Activity"
        self.silence_limit = 2 # Seconds of silence to stop recording
        self.save_path = "./data/audio"
        
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

    def start(self):
        self.running = True
        print("[System] Audio Listener (Ear) Active")
        threading.Thread(target=self._listen_loop).start()

    def stop(self):
        self.running = False

    def _rms(self, data):
        count = len(data) / 2
        format = "%dh" % (count)
        shorts = struct.unpack(format, data)
        sum_squares = 0.0
        for sample in shorts:
            n = sample * (1.0 / 32768)
            sum_squares += n * n
        return math.sqrt(sum_squares / count) * 32768

    def _listen_loop(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk)

        print("[Ear] Listening for speech...")
        
        frames = []
        listening_to_speech = False
        silence_start = None

        while self.running:
            data = stream.read(self.chunk)
            rms = self._rms(data)

            if rms > self.threshold:
                if not listening_to_speech:
                    print("[Ear] Speech detected! Recording...")
                    listening_to_speech = True
                frames.append(data)
                silence_start = None
            elif listening_to_speech:
                frames.append(data)
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > self.silence_limit:
                    print("[Ear] End of speech.")
                    self._save_audio(frames)
                    frames = []
                    listening_to_speech = False
                    silence_start = None
        
        stream.stop_stream()
        stream.close()
        p.terminate()

    def _save_audio(self, frames):
        if not frames:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio_{timestamp}.wav"
        filepath = os.path.join(self.save_path, filename)
        
        wf = wave.open(filepath, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        # Emit Event
        event = Event(
            event_type="AUDIO",
            content=str(filepath),
            source="microphone",
            metadata={"duration_frames": len(frames)}
        )
        self.event_queue.put(event)
        print(f"[Ear] Saved clip: {filename} -> Sent to Ingestor Agent")
