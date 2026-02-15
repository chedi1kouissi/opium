import requests
import json
from memora_os.config import settings

class LocalLLM:
    def __init__(self, base_url=None, model=None):
        # Use settings from YAML or provided values
        self.base_url = base_url or getattr(settings, 'LLM_BASE_URL', 'http://localhost:11434/api/generate')
        self.model = model or getattr(settings, 'LLM_MODEL', 'phi3:mini')

    def generate(self, prompt, system_prompt=None, json_mode=False):
        """
        Generic wrapper for a local LLM (e.g., Ollama).
        Returns empty JSON on error to prevent crashes.
        """
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\nUser: {prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
        }
        
        if json_mode:
            payload["format"] = "json"

        try:
            # Try connecting to local Ollama
            response = requests.post(self.base_url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json().get("response", "")
            return result
            
        except requests.RequestException as e:
            print(f"[LLM] ERROR: Could not connect to {self.base_url}. Is Ollama running?")
            print(f"[LLM] Details: {e}")
            return "{}" # Return empty JSON to prevent crash
