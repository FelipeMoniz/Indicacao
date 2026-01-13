import json
import os
from datetime import datetime

DATA_DIR = "data"

# Garante que o diretório de dados existe
os.makedirs(DATA_DIR, exist_ok=True)

def load_data(filename, default=None):
    """Carrega dados de um arquivo JSON"""
    if default is None:
        default = []

    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_data(filename, data):
    """Salva dados em um arquivo JSON"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def init_default_data():
    """Inicializa dados padrão se não existirem"""
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

# Funções para gerenciar grupo do usuário
def save_user_preferred_group(username, group_id):
    """Salva o grupo preferido/último do usuário"""
    users = load_data("users.json", {})

    if username in users:
        users[username]["preferred_group"] = group_id
        users[username]["last_group"] = group_id
        save_data("users.json", users)
        return True
    return False

def get_user_preferred_group(username):
    """Obtém o grupo preferido/último do usuário"""
    users = load_data("users.json", {})

    if username in users:
        return users[username].get("preferred_group")
    return None

def get_user_last_group(username):
    """Obtém o último grupo acessado pelo usuário"""
    users = load_data("users.json", {})

    if username in users:
        return users[username].get("last_group")
    return None

# Função para atualizar usuários existentes (executar uma vez)
def update_existing_users():
    """Atualiza estrutura de usuários existentes"""
    users = load_data("users.json", {})

    for username in users:
        if "preferred_group" not in users[username]:
            users[username]["preferred_group"] = None
            users[username]["last_group"] = None

    save_data("users.json", users)
    print("✅ Usuários atualizados!")

# Execute uma vez se necessário
# update_existing_users()
