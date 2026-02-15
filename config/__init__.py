import yaml
import os

class Settings:
    def __init__(self, settings_path=None):
        # Default fallback
        self.MODE = "DEV"
        self.QUICK_LAYER_HOURS = 48
        self.SCREENSHOT = {"ENABLED": True, "INTERVAL_SECONDS": 10, "SAVE_PATH": "./data/screenshots"}
        self.AUDIO = {"ENABLED": True}
        
        # Determine absolute path to settings.yaml if not provided
        if settings_path is None:
            # Assuming this file is in memora_os/config/
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # memora_os/
            settings_path = os.path.join(base_dir, "config", "settings.yaml")

        # Load from file if exists
        if os.path.exists(settings_path):
            print(f"[Config] Loading settings from {settings_path}")
            with open(settings_path, 'r') as f:
                config = yaml.safe_load(f)
                if config:
                    for key, value in config.items():
                        setattr(self, key, value)
        else:
            print(f"[Config] Warning: Settings file not found at {settings_path}. Using defaults.")

settings = Settings()
