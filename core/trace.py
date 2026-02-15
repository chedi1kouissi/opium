import json
import threading
import os
from datetime import datetime

class TraceLogger:
    """
    Centralized logging for agent reasoning.
    Saves to data/trace.json on every log to ensure data persistence even if crash.
    """
    _instance = None
    _lock = threading.Lock()
    _log_file = "./data/trace.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TraceLogger, cls).__new__(cls)
            # Ensure directory exists
            os.makedirs(os.path.dirname(cls._log_file), exist_ok=True)
            # Initialize empty list if file doesn't exist
            if not os.path.exists(cls._log_file):
                with open(cls._log_file, 'w') as f:
                    json.dump([], f)
        return cls._instance

    @classmethod
    def log(cls, agent, action, details):
        """
        Logs a structured event.
        """
        # Ensure details are serializable (recursive check or simple str conversion for safe fallback)
        def json_serial(obj):
            if isinstance(obj, (datetime, datetime.date)):
                return obj.isoformat()
            return str(obj)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "details": details
        }
        
        with cls._lock:
            try:
                # Read existing
                data = []
                if os.path.exists(cls._log_file):
                    with open(cls._log_file, 'r') as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError:
                            data = []
                
                # Append
                data.append(entry)
                
                # Write back with default=str to handle non-serializable objects in 'details'
                with open(cls._log_file, 'w') as f:
                    json.dump(data, f, indent=2, default=json_serial)
            except Exception as e:
                print(f"[Trace] Error logging: {e}")

# Global instance
tracer = TraceLogger()
