import time
import threading
import datetime
from memora_os.core.events import Event
from memora_os.config import settings

# Mocking win32com for environments without Outlook, but illustrating the logic
try:
    import win32com.client
    import pythoncom 
    OUTLOOK_AVAILABLE = True
except ImportError:
    OUTLOOK_AVAILABLE = False

class CalendarListener:
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.running = False
        self.check_interval = 60 # Check every minute

    def start(self):
        self.running = True
        print("[System] Calendar Listener Active")
        threading.Thread(target=self._poll_calendar).start()

    def stop(self):
        self.running = False

    def _poll_calendar(self):
        # COM must be initialized in the new thread
        if OUTLOOK_AVAILABLE:
            pythoncom.CoInitialize()
            
        while self.running:
            events = self._get_current_meetings()
            for evt_data in events:
                # Deduplicate logic would go here (don't send same event twice)
                event = Event(
                    event_type="CALENDAR",
                    content=evt_data['subject'],
                    source="outlook_mapi",
                    metadata={
                        "organizer": evt_data['organizer'],
                        "start": evt_data['start'],
                        "end": evt_data['end'],
                        "body_preview": evt_data['body'][:100]
                    }
                )
                self.event_queue.put(event)
                print(f"[Calendar] Found active meeting: {evt_data['subject']}")
            
            time.sleep(self.check_interval)

    def _get_current_meetings(self):
        """
        Connects to Outlook MAPI to find meetings happening RIGHT NOW.
        NO FILTERS - captures ALL active meetings.
        """
        active_events = []
        if not OUTLOOK_AVAILABLE:
            return []

        try:
            outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
            calendar = outlook.GetDefaultFolder(9) # 9 = olFolderCalendar
            appointments = calendar.Items
            appointments.Sort("[Start]")
            appointments.IncludeRecurrences = True

            now = datetime.datetime.now()
            
            # Find appointments happening RIGHT NOW (no keyword filtering!)
            for appt in appointments:
                try:
                    # Get start/end times
                    start = appt.Start
                    end = appt.End
                    
                    # Simple datetime comparison (handle timezone issues if needed)
                    # Check if current time is within meeting window
                    if start <= now <= end:
                        active_events.append({
                            "subject": appt.Subject,
                            "organizer": str(appt.Organizer),
                            "start": str(start),
                            "end": str(end),
                            "body": appt.Body
                        })
                except:
                    continue
                    
        except Exception as e:
            print(f"[Calendar] Error reading Outlook: {e}")

        return active_events
