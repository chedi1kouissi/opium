import json
import datetime
import queue
import time
import sys
import os

# Setup Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memora_os.core.events import Event
from memora_os.pipeline.perception.agent import PerceptionAgent
from memora_os.pipeline.normalizers.agent import NormalizerAgent
from memora_os.pipeline.linkers.agent import LinkerAgent

def run_realistic_scenario():
    """
    Run a realistic scenario from JSON file (text-based events).
    Tests the full pipeline with real-looking content.
    """
    print("="*70)
    print(">>> LOADING REALISTIC SCENARIO <<<")
    print("="*70)
    print()
    
    # Load scenario
    with open('scenario_realistic.json', 'r', encoding='utf-8') as f:
        scenario_data = json.load(f)
    
    print(f"📋 Scenario: {scenario_data['scenario_name']}")
    print(f"📝 Description: {scenario_data['description']}")
    print(f"📊 Total Events: {len(scenario_data['events'])}")
    print()
    print("="*70)
    print()
    
    # Setup pipeline
    ingest_queue = queue.Queue()
    perception_queue = queue.Queue()
    linker_queue = queue.Queue()
    
    cortex = PerceptionAgent(ingest_queue, perception_queue)
    cortex.start()
    
    normalizer = NormalizerAgent(perception_queue, linker_queue)
    normalizer.start()
    
    brain = LinkerAgent(linker_queue)
    brain.start()
    
    # Inject events
    base_time = datetime.datetime.now()
    
    for i, event_data in enumerate(scenario_data['events'], 1):
        timestamp = base_time + datetime.timedelta(hours=event_data.get('timestamp_offset_hours', 0))
        
        event = Event(
            event_type=event_data['event_type'],
            content=event_data['content'],  # Already text, no file paths
            source=event_data['source'],
            timestamp=timestamp
        )
        
        print(f"\n{'─'*70}")
        print(f"📌 Event {i}/{len(scenario_data['events'])}: {event.event_type}")
        print(f"⏰ Time offset: +{event_data.get('timestamp_offset_hours', 0)}h from start")
        print(f"📄 Preview: {event.content[:120].replace(chr(10), ' ')}...")
        print(f"{'─'*70}")
        
        ingest_queue.put(event)
        time.sleep(3)  # Wait for processing
    
    print("\n" + "="*70)
    print(">>> SCENARIO INJECTION COMPLETE <<<")
    print(">>> Waiting for agents to finish processing... <<<")
    print("="*70)
    time.sleep(120)  # Let agents finish (Local LLM can be slow)
    
    print("\n" + "="*70)
    print(">>> STOPPING AGENTS <<<")
    print("="*70)
    cortex.stop()
    normalizer.stop()
    brain.stop()
    
    time.sleep(2)
    
    print("\n" + "="*70)
    print("✅ SUCCESS!")
    print("="*70)
    print(f"📊 Knowledge Graph saved to: data/graph.json")
    print(f"📋 Trace logs saved to: data/trace.json")
    print()
    print("You can inspect:")
    print("  1. Graph structure (nodes and relationships)")
    print("  2. Entity extraction quality")
    print("  3. Semantic linking decisions")
    print("="*70)

if __name__ == "__main__":
    run_realistic_scenario()
