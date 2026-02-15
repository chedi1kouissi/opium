import json
import threading
import queue
import os
from memora_os.core.events import Event
from memora_os.core.llm import LocalLLM

class PerceptionAgent:
    """
    Agent A.2: Perception
    - Receives Single Mode Event.
    - Performs OCR or STT.
    - Decides if content is matched enough to send to Normalizer.
    """
    def __init__(self, input_queue, output_queue):
        self.input_queue = input_queue
        self.output_queue = output_queue # Starts the Normalizer queue
        self.llm = LocalLLM() # Used for STT mock or small routing decisions
        self.running = False

    def start(self):
        self.running = True
        print("[System] Perception Agent (The Cortex) Active")
        threading.Thread(target=self._process_loop).start()

    def stop(self):
        self.running = False

    def _process_loop(self):
        while self.running:
            try:
                raw_event = self.input_queue.get(timeout=1)
                print(f"[Perception] Analyzing: {raw_event.event_type}")

                enhanced_event = self._reason_on_input(raw_event)
                
                if enhanced_event:
                    self.output_queue.put(enhanced_event)
                    print(f"[Perception] Forwarded to Normalizer.")
                else:
                    print(f"[Perception] Skipped (Low confidence/Empty).")

            except queue.Empty:
                pass
            except Exception as e:
                print(f"[Perception] Error: {e}")

    def _reason_on_input(self, event: Event):
        """
        SLM-based Routing Logic.
        Decides: Normalizer (Deep) vs Linker (Metadata only).
        """
        # 1. Extract Raw Signal (OCR or STT)
        text_content = ""
        context_type = ""
        
        if event.event_type == "AUDIO":
            # If content looks like a path, perform real STT
            # If content is already text (Simulation), use it.
            if str(event.content).endswith(".wav"):
                 event.metadata['file_path'] = str(event.content) 
                 text_content = self._perform_stt(event.content)
            else:
                 text_content = str(event.content)
            
            context_type = "Audio Transcript"
            event.metadata['transcript'] = text_content
            
        elif event.event_type == "SCREENSHOT":
            if str(event.content).endswith(".png"):
                 event.metadata['file_path'] = str(event.content)
                 text_content = self._perform_ocr(event.content)
            else:
                 text_content = str(event.content)
                 
            context_type = "Screen OCR"
            event.metadata['ocr_text'] = text_content
            
        elif event.event_type in ["EMAIL", "CALENDAR", "WEB"]:
            text_content = event.content
            context_type = "Text Item"
            
        if not text_content:
            return None

        # 2. SLM Router Decision
        # Ask the Local Model: "Is this meaningful?"
        decision = self._query_slm_router(text_content, context_type)
        
        if decision == "NORMALIZE":
            event.content = text_content # Pass full text to Normalizer
            return event
        else:
            # Bypass Normalizer, send straight to Linker (Logic to be handled by main/linker)
            # For now, we return None to skip Normalizer, 
            # BUT we should actually flag it as 'metadata_only' and still pass it if Linker expects it.
            # Plan says: "Send directly to Linker". 
            # Current pipeline in main.py is Linear: Perception -> Normalizer -> Linker.
            # To skip Normalizer, we flag it.
            event.metadata['skip_normalization'] = True
            event.content = text_content
            return event

    def _query_slm_router(self, text, context_type):
        """
        Uses Local LLM to classify importance.
        """
        prompt = f"""
        Act as a Data Router.
        Input Type: {context_type}
        Content: "{text[:500]}"
        
        Task: Does this content contain valuable information (names, dates, projects, financials) 
        that should be universally indexed? 
        Or is it noise/menu text?
        
        Response VALID JSON ONLY: {{"action": "NORMALIZE" | "SKIP"}}
        """
        
        # Real SLM Call
        try:
            response = self.llm.generate(prompt, json_mode=True)
            data = json.loads(response)
            return data.get("action", "NORMALIZE") # Default to NORMALIZE to be safe
        except:
            # Fallback only if json parse fails, but rely on LLM
            print("[Perception] Router LLM failed/malformed. Defaulting to NORMALIZE.")
            return "NORMALIZE"

    def _handle_audio(self, event):
        # Deprecated by _reason_on_input
        pass

    def _handle_screenshot(self, event):
        # Deprecated by _reason_on_input
        pass

    def _perform_stt(self, wav_path):
        """
        Real STT using faster-whisper (optimized Whisper).
        Model: tiny (39M params) - fast and runs on CPU.
        """
        try:
            from faster_whisper import WhisperModel
            
            # Initialize model once (lazy loading)
            if not hasattr(self, '_whisper_model'):
                print("[Perception] Loading Whisper model (first time only)...")
                # "tiny" = 39M params, "base" = 74M params
                self._whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            
            segments, info = self._whisper_model.transcribe(wav_path, language="en")
            text = ' '.join([segment.text for segment in segments])
            return text.strip()
        except ImportError:
            print(f"[Perception] faster-whisper not installed. Install: pip install faster-whisper")
            return ""
        except Exception as e:
            print(f"[Perception] STT Error on {wav_path}: {e}")
            return ""

    def _perform_ocr(self, image_path):
        """
        Real OCR using pytesseract.
        Falls back to empty string on error.
        """
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
        except ImportError:
            print(f"[Perception] pytesseract not installed. Install: pip install pytesseract Pillow")
            print(f"[Perception] Also install Tesseract binary: https://github.com/tesseract-ocr/tesseract")
            return ""
        except Exception as e:
            print(f"[Perception] OCR Error on {image_path}: {e}")
            return ""
