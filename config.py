import os
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, config_file='config.json'):
        """Initialize configuration from file and environment variables"""
        self.config = self.load_config(config_file)
    
    def load_config(self, config_file):
        """Load configuration from JSON file and environment variables"""
        default_config = {
            "channels": {
                "Timothy Ronald": {
                    "channel_id": "UCXMB8OiiSnq2B4xLgUtTYhw",
                    "rss_url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCXMB8OiiSnq2B4xLgUtTYhw"
                },
                "Akademi Crypto": {
                    "channel_id": "UCe9_rJjMmQS5C_LobUZ_pHg", 
                    "rss_url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCe9_rJjMmQS5C_LobUZ_pHg"
                }
            },
            "google": {
                "email": os.getenv("GOOGLE_EMAIL", "foralllllll13@gmail.com"),
                "password": os.getenv("GOOGLE_PASSWORD", "ForAllOfUs13.")
            },
            "openai_api_key": os.getenv("OPENAI_API_KEY", "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"),
            "download_path": os.getenv("DOWNLOAD_PATH", "./downloads"),
            "output_path": os.getenv("OUTPUT_PATH", "./output"),
            "clip_duration": int(os.getenv("CLIP_DURATION", "60")),
            "max_clips_per_video": int(os.getenv("MAX_CLIPS_PER_VIDEO", "5"))
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                # Merge with default config, prioritizing environment variables
                default_config.update(file_config)
        else:
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default config file: {config_file}")
        
        return default_config
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def __getitem__(self, key):
        """Allow dict-like access"""
        return self.config[key] 