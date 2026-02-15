import time
import threading
import os
import mss
import mss.tools
from datetime import datetime
from memora_os.core.events import Event
from memora_os.config import settings

class ScreenshotListener:
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.running = False
        self.interval = settings.SCREENSHOT['INTERVAL_SECONDS']
        self.save_path = settings.SCREENSHOT['SAVE_PATH']
        
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

    def start(self):
        self.running = True
        print("[System] Screenshot Listener Active")
        while self.running:
            self.capture()
            time.sleep(self.interval)

    def stop(self):
        self.running = False

    def capture(self):
        try:
            with mss.mss() as sct:
                # Capture the primary monitor
                monitor = sct.monitors[1] 
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screen_{timestamp}.png"
                filepath = os.path.join(self.save_path, filename)
                
                # Save to file
                output = sct.grab(monitor)
                mss.tools.to_png(output.rgb, output.size, output=filepath)
                
                # Create Event -> Send to Agent pipeline
                event = Event(
                    event_type="SCREENSHOT",
                    content=str(filepath),
                    source="mss_screen_capture",
                    metadata={"width": output.width, "height": output.height}
                )
                self.event_queue.put(event)
                print(f"[Eye] Captured: {filename}")
                
        except Exception as e:
            print(f"[Eye] Error capturing screenshot: {e}")
