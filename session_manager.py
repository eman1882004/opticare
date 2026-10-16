import json

class ConfigurationManager:
    def  __init__(self, config_path="config.json"):
        self.config_path = config_path
        with open(self.config_path, "r") as file:
            self.settings = json.load(file)

    def get_setting(self, key):
        return self.settings.get(key)

if __name__ == "__main__":
    config = ConfigurationManager()
    
    print("Configuration loaded successfully:")
    print("Camera Index:", config.get_setting("camera_index"))
    print("Dwell Time:", config.get_setting("dwell_time_seconds"))