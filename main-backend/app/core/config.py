import os
import yaml
from pydantic import BaseModel
from typing import List, Optional

class RobotConfig(BaseModel):
    id: str
    ip: str

class AppConfig(BaseModel):
    robots: List[RobotConfig] = []

def load_config(config_path="robots.yaml") -> AppConfig:
    if not os.path.exists(config_path):
        return AppConfig()
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        if not data:
            return AppConfig()
        return AppConfig(**data)

settings = load_config()
