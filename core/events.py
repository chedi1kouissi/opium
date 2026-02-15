from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

@dataclass
class Event:
    """
    Standard envelope for all data flowing through the MemoraOS pipeline.
    This is what links the 'Listeners' to the 'Agents'.
    """
    event_type: str  # "SCREENSHOT", "AUDIO", "CALENDAR", "TEXT"
    content: Any     # The raw data (e.g., file path, text string, bytes)
    source: str      # "System", "Microphone", "Outlook"
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.event_type,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "source": self.source,
            "metadata": self.metadata
        }
