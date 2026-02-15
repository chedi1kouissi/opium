import argparse
import time
import queue
import threading
import sys
import os

# Allow importing from parent directory (opKG)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memora_os.core.events import Event
from memora_os.pipeline.perception.agent import PerceptionAgent
from memora_os.pipeline.normalizers.agent import NormalizerAgent
from memora_os.pipeline.linkers.agent import LinkerAgent

def main():
    parser = argparse.ArgumentParser(description="Manual Event Ingestion for MemoraOS")
    parser.add_argument("--type", required=True, choices=["AUDIO", "SCREENSHOT", "EMAIL", "CALENDAR"], help="Event Type")
    parser.add_argument("--content", required=True, help="Content (Text, Path, or Transcript)")
    parser.add_argument("--source", default="Manual_Injection", help="Source metadata")
    
    args = parser.parse_args()

    # Setup Pipelines
    ingest_queue = queue.Queue()
    perception_queue = queue.Queue()
    linker_queue = queue.Queue()

    # Start Agents
    print("[System] Initializing Pipeline...")
    
    cortex = PerceptionAgent(ingest_queue, perception_queue)
    cortex.start()

    normalizer = NormalizerAgent(perception_queue, linker_queue)
    normalizer.start()

    brain = LinkerAgent(linker_queue)
    brain.start()

    # Create & Inject Event
    print(f"[User] Injecting {args.type} Event...")
    event = Event(
        event_type=args.type,
        content=args.content,
        source=args.source
    )
    
    ingest_queue.put(event)

    # Allow time for processing
    try:
        while True:
            if ingest_queue.empty() and perception_queue.empty() and linker_queue.empty():
                print("[System] Processing Complete (Queues Empty). Waiting 5s for threads to finish...")
                time.sleep(5)
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cortex.stop()
        normalizer.stop()
        brain.stop()
        print("[System] Shutdown.")

if __name__ == "__main__":
    main()
