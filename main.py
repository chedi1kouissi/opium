import time
import threading
import sys
import os
import queue

# Add project root to path (one level up from current script)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from memora_os.config import settings
from pipeline.ingestors.screenshot import ScreenshotListener
from pipeline.ingestors.audio import AudioListener
from pipeline.ingestors.calendar import CalendarListener
from pipeline.ingestors.email import EmailListener
from pipeline.normalizers.agent import NormalizerAgent
from pipeline.perception.agent import PerceptionAgent
from pipeline.linkers.agent import LinkerAgent

def start_memora_os():
    """
    Main entry point for MemoraOS.
    Starts the Windows Native Listeners (Senses) and the Event Pipeline.
    """
    print(f"--- MemoraOS: Digital Nervous System ---")
    print(f"Status: Online")
    print(f"OS: Windows Native")
    print(f"Graph Layer: Quick (<{settings.QUICK_LAYER_HOURS}h)")
    
    # 1. The Pipelines
    # Raw Events -> Perception
    ingest_queue = queue.Queue()
    # Perceived Events (Text/Enriched) -> Normalizer
    perception_queue = queue.Queue()
    # Normalized Events -> Linker
    linker_queue = queue.Queue()
    
    # 2. Start The Senses (Listeners)
    listeners = []
    
    if settings.SCREENSHOT['ENABLED']:
        screen_eye = ScreenshotListener(ingest_queue)
        t = threading.Thread(target=screen_eye.start)
        t.daemon = True
        t.start()
        listeners.append(screen_eye)
    
    # ... (other listeners similarly use ingest_queue) ...
        
    if settings.AUDIO['ENABLED']:
        ear = AudioListener(ingest_queue)
        ear.start() 
        listeners.append(ear)
        
    if settings.CALENDAR.get('ENABLED', True):
        cal = CalendarListener(ingest_queue)
        cal.start()
        listeners.append(cal)

    if settings.CALENDAR.get('ENABLED', True):
        mail = EmailListener(ingest_queue)
        mail.start()
        listeners.append(mail)

    # 3. Start The Agents
    # Perception: Ingest -> Perception
    cortex = PerceptionAgent(ingest_queue, perception_queue)
    cortex.start()
    listeners.append(cortex)

    # Normalizer: Perception -> Linker
    normalizer = NormalizerAgent(perception_queue, linker_queue)
    normalizer.start()
    listeners.append(normalizer)
    
    # Linker: Consumes Linker Queue -> Graph
    brain = LinkerAgent(linker_queue)
    brain.start()
    listeners.append(brain)

    print("\n[System] All Senses Active. Constructing Reality...")
    print("Press Ctrl+C to stop.")
    
    # 4. Main Loop - Just wait for Ctrl+C (agents run in background)
    try:
        while True:
            time.sleep(1)  # Keep main thread alive
                
    except KeyboardInterrupt:
        print("\nShutting down MemoraOS...")
        for l in listeners:
            l.stop()

if __name__ == "__main__":
    start_memora_os()
