import json
import os
from datetime import datetime

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def load_data(filename, default=None):
    if default is None:
        default = []
    
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_data(filename, data):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def init_default_data():
    users_file = os.path.join(DATA_DIR, "users.json")
    if not os.path.exists(users_file):
        save_data("users.json", {})
    
    groups_file = os.path.join(DATA_DIR, "groups.json")
    if not os.path.exists(groups_file):
        save_data("groups.json", [])
    
    recs_file = os.path.join(DATA_DIR, "recommendations.json")
    if not os.path.exists(recs_file):
        save_data("recommendations.json", [])

init_default_data()
