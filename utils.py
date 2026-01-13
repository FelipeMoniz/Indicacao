import json
import os
from datetime import datetime

DATA_DIR = "data"

# Garante que o diretório de dados existe
os.makedirs(DATA_DIR, exist_ok=True)

def load_data(filename, default=None):
    """Carrega dados de um arquivo JSON com tratamento de erros"""
    if default is None:
        default = [] if filename.endswith(".json") and "users" not in filename else {}

    filepath = os.path.join(DATA_DIR, filename)

    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Aplica migrações se necessário
            if filename == "recommendations.json":
                data = migrate_recommendations(data)
            elif filename == "users.json":
                data = migrate_users(data)
            elif filename == "groups.json":
                data = migrate_groups(data)

            return data
        except json.JSONDecodeError:
            print(f"⚠️  Erro ao ler {filename}, retornando valor padrão")
            return default
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

# ==================== SISTEMA DE MIGRAÇÃO ====================

def migrate_recommendations(recommendations):
    """Migra recomendações antigas para nova estrutura"""
    if not isinstance(recommendations, list):
        return recommendations

    migrated = False

    for rec in recommendations:
        # Versão 1.0 → 1.1: Adiciona campos de dislike
        if "dislikes" not in rec:
            rec["dislikes"] = 0
            migrated = True

        if "disliked_by" not in rec:
            rec["disliked_by"] = []
            migrated = True

        # Versão 1.1 → 1.2: Garante campos obrigatórios
        required_fields = ["id", "title", "description", "category", "rating",
                          "tags", "author", "group_id", "created_at", "likes", "liked_by"]

        for field in required_fields:
            if field not in rec:
                if field == "tags":
                    rec[field] = []
                elif field == "likes":
                    rec[field] = 0
                elif field == "liked_by":
                    rec[field] = []
                elif field == "created_at":
                    rec[field] = datetime.now().isoformat()
                else:
                    rec[field] = ""
                migrated = True

    if migrated:
        print("🔄 Recomendações migradas para nova versão")
        save_data("recommendations.json", recommendations)

    return recommendations

def migrate_users(users):
    """Migra usuários antigos para nova estrutura"""
    if not isinstance(users, dict):
        return users

    migrated = False

    for username, user_data in users.items():
        # Se user_data não é dicionário (estrutura muito antiga)
        if not isinstance(user_data, dict):
            users[username] = {
                "password": user_data,
                "created_at": datetime.now().isoformat(),
                "preferred_group": None,
                "last_group": None
            }
            migrated = True
        else:
            # Versão 1.0 → 1.1: Adiciona campos de grupo preferido
            if "preferred_group" not in user_data:
                user_data["preferred_group"] = None
                migrated = True

            if "last_group" not in user_data:
                user_data["last_group"] = None
                migrated = True

            # Versão 1.1 → 1.2: Adiciona campo created_at se não existir
            if "created_at" not in user_data:
                user_data["created_at"] = datetime.now().isoformat()
                migrated = True

    if migrated:
        print("🔄 Usuários migrados para nova versão")
        save_data("users.json", users)

    return users

def migrate_groups(groups):
    """Migra grupos antigos para nova estrutura"""
    if not isinstance(groups, list):
        return groups

    migrated = False

    for group in groups:
        # Versão 1.0 → 1.1: Adiciona campo is_public
        if "is_public" not in group:
            group["is_public"] = True
            migrated = True

        # Garante campos obrigatórios
        required_fields = ["id", "name", "description", "categories",
                          "created_by", "created_at", "members"]

        for field in required_fields:
            if field not in group:
                if field == "categories":
                    group[field] = []
                elif field == "members":
                    group[field] = []
                elif field == "created_at":
                    group[field] = datetime.now().isoformat()
                else:
                    group[field] = ""
                migrated = True

    if migrated:
        print("🔄 Grupos migrados para nova versão")
        save_data("groups.json", groups)

    return groups

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

# Inicializa dados e aplica migrações
init_default_data()

# Carrega e migra todos os dados na inicialização
print("🔍 Verificando migrações necessárias...")
load_data("users.json")
load_data("groups.json")
load_data("recommendations.json")
print("✅ Sistema de migração pronto!")
