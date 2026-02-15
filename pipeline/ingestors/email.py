import time
import threading
import datetime
from memora_os.core.events import Event
from memora_os.config import settings

try:
    import win32com.client
    import pythoncom
    OUTLOOK_AVAILABLE = True
except ImportError:
    OUTLOOK_AVAILABLE = False

class EmailListener:
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.running = False
        self.check_interval = 30 # Check every 30 seconds
        self.last_checked = datetime.datetime.now()

    def start(self):
        self.running = True
        print("[System] Email Listener Active")
        threading.Thread(target=self._poll_inbox).start()

    def stop(self):
        self.running = False

    def _poll_inbox(self):
        if OUTLOOK_AVAILABLE:
            pythoncom.CoInitialize()
            
        while self.running:
            new_emails = self._get_new_emails()
            for email_data in new_emails:
                event = Event(
                    event_type="EMAIL",
                    content=email_data['body'],
                    source="outlook_inbox",
                    metadata={
                        "sender": email_data['sender'],
                        "subject": email_data['subject'],
                        "received_time": email_data['received_time']
                    }
                )
                self.event_queue.put(event)
                print(f"[Email] New Message from {email_data['sender']}: {email_data['subject']}")
            
            self.last_checked = datetime.datetime.now()
            time.sleep(self.check_interval)

    def _get_new_emails(self):
        """
        Connects to Outlook MAPI to find new emails since last check.
        NO KEYWORD FILTERS - uses timestamp comparison.
        """
        captured_emails = []
        if not OUTLOOK_AVAILABLE:
            return []

        try:
            outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
            inbox = outlook.GetDefaultFolder(6) # 6 = olFolderInbox
            messages = inbox.Items
            messages.Sort("[ReceivedTime]", True) # Descending

            for message in messages:
                try:
                    received_time = message.ReceivedTime
                    
                    # Only get emails AFTER last check (NO keyword filtering!)
                    if received_time > self.last_checked:
                        captured_emails.append({
                            "sender": str(message.SenderName),
                            "subject": message.Subject,
                            "body": message.Body, # Full body, not just preview
                            "received_time": str(received_time)
                        })
                    else:
                        # Since sorted descending, stop when we hit old emails
                        break
                        
                except:
                    continue
                    
        except Exception as e:
            # Silent fail if Outlook is locked/busy
            pass

        return captured_emails
