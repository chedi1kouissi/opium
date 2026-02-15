import json
import threading
import queue
from memora_os.core.events import Event
from memora_os.core.llm import LocalLLM
from memora_os.config import settings
import yaml
import os

class NormalizerAgent:
    def __init__(self, input_queue, output_queue):
        self.input_queue = input_queue
        self.output_queue = output_queue # Starts the Linker queue
        self.llm = LocalLLM()
        self.running = False
        
        # Load constraints
        self.prompts = self._load_prompts()

    def start(self):
        self.running = True
        print("[System] Normalizer Agent (The Lens) Active")
        threading.Thread(target=self._process_loop).start()

    def stop(self):
        self.running = False

    def _process_loop(self):
        while self.running:
            try:
                # Wait for processed event from Perception
                event = self.input_queue.get(timeout=1)
                
                # Check for "Skip" flag from Perception Router
                if event.metadata.get('skip_normalization'):
                    print(f"[Normalizer] Skipping LLM (Router Decision). Passing raw event to Linker.")
                    # Pass minimal structure or raw event to Linker
                    self.output_queue.put(event)
                    continue

                print(f"[Normalizer] Structuring {event.event_type}...")
                
                # 1. Prepare Prompt with EMPHASIS on preserving detail
                prompt_content = f"""
                Source: {event.source}
                Timestamp: {event.timestamp}
                FULL_CONTENT_DO_NOT_SUMMARIZE:
                {event.content}
                """
                
                # 2. Call LLM
                json_str = self.llm.generate(
                    prompt=prompt_content,
                    system_prompt=self.prompts.get('NORMALIZER_SYSTEM_PROMPT', ''),
                    json_mode=True
                )
                
                # 3. Parse & Enrich
                try:
                    normalized_data = json.loads(json_str)
                    
                    # Ensure deep_metadata exists
                    if 'deep_metadata' not in normalized_data:
                        normalized_data['deep_metadata'] = {}
                    
                    # CRITICAL: Force inject the source of truth if LLM hallucinated or missed it
                    normalized_data['deep_metadata']['raw_text'] = event.content
                    
                    # Inject filepath
                    if event.event_type in ["SCREENSHOT", "AUDIO"]:
                         # Prioritize metadata path, fall back to content if it looks like path
                         path = event.metadata.get('file_path', str(event.content))
                         normalized_data['deep_metadata']['file_path'] = path

                    event.metadata['normalized'] = normalized_data
                    self.output_queue.put(event)
                    
                    # Log Trace
                    from memora_os.core.trace import tracer
                    tracer.log("Normalizer", "Normalized", normalized_data)
                    
                    print(f"[Normalizer] Success -> Entity: {normalized_data.get('primary_entity')}")
                    
                except json.JSONDecodeError:
                    print(f"[Normalizer] Failed to parse LLM JSON. Using Fallback.")
                    # Fallback: Create basic structure so Linker has something to work with
                    fallback_data = {
                        "event_type": event.event_type,
                        "primary_entity": "Unprocessed Event",
                        "entities": {
                             "other": ["Fallback Entity"]
                        },
                        "content_summary": str(event.content)[:100],
                        "deep_metadata": {
                            "raw_text": str(event.content),
                            "confidence": "low"
                        }
                    }
                    event.metadata['normalized'] = fallback_data
                    self.output_queue.put(event)
                    
            except queue.Empty:
                pass
            except Exception as e:
                print(f"[Normalizer] Error: {e}")
                # Ensure we don't drop the event even on generic error
                try:
                   self.output_queue.put(event)
                except:
                   pass

    def _load_prompts(self):
        # Load from config/prompts.yaml
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "prompts.yaml")
        if os.path.exists(path):
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        return {}
