import sqlite3
import json
import os
from datetime import datetime

DB_FILE = "indica_app.db"

def init_database():
    """Inicializa o banco de dados SQLite"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL,
            preferred_group INTEGER,
            last_group INTEGER
        )
    ''')

    # Tabela de grupos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            categories TEXT,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            members TEXT,
            is_public BOOLEAN DEFAULT 1
        )
    ''')

    # Tabela de recomendações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            rating INTEGER,
            tags TEXT,
            author TEXT NOT NULL,
            group_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            dislikes INTEGER DEFAULT 0,
            liked_by TEXT,
            disliked_by TEXT
        )
    ''')

    conn.commit()
    conn.close()

def load_data(table_name, default=None):
    """Carrega dados de uma tabela - mantém compatibilidade"""
    if default is None:
        default = [] if table_name != "users" else {}

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        if table_name == "users":
            data = {}
            for row in rows:
                user_data = {
                    "password": row[1],
                    "created_at": row[2],
                    "preferred_group": row[3],
                    "last_group": row[4]
                }
                data[row[0]] = user_data
        else:
            data = []
            for row in rows:
                item = dict(zip(columns, row))

                # Converte campos JSON para lista
                json_fields = []
                if table_name == "groups":
                    json_fields = ['categories', 'members']
                elif table_name == "recommendations":
                    json_fields = ['tags', 'liked_by', 'disliked_by']

                for field in json_fields:
                    if field in item and item[field]:
                        try:
                            item[field] = json.loads(item[field])
                        except:
                            item[field] = []
                    elif field in item:
                        item[field] = []

                # Converte tipos
                if 'id' in item:
                    item['id'] = int(item['id'])
                if 'rating' in item:
                    item['rating'] = int(item['rating']) if item['rating'] else 0
                if 'likes' in item:
                    item['likes'] = int(item['likes']) if item['likes'] else 0
                if 'dislikes' in item:
                    item['dislikes'] = int(item['dislikes']) if item['dislikes'] else 0
                if 'group_id' in item:
                    item['group_id'] = int(item['group_id']) if item['group_id'] else 0
                if 'is_public' in item:
                    item['is_public'] = bool(item['is_public'])

                data.append(item)

        return data
    except Exception as e:
        print(f"⚠️  Carregando {table_name}: {e}")
        return default
    finally:
        conn.close()

def save_data(table_name, data):
    """Salva dados em uma tabela - mantém compatibilidade"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        if table_name == "users":
            for username, user_data in data.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO users
                    (username, password, created_at, preferred_group, last_group)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    username,
                    user_data.get('password', ''),
                    user_data.get('created_at', datetime.now().isoformat()),
                    user_data.get('preferred_group'),
                    user_data.get('last_group')
                ))

        elif table_name == "groups":
            cursor.execute("DELETE FROM groups")
            for item in data:
                cursor.execute('''
                    INSERT INTO groups
                    (id, name, description, categories, created_by, created_at, members, is_public)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.get('id'),
                    item.get('name', ''),
                    item.get('description', ''),
                    json.dumps(item.get('categories', [])),
                    item.get('created_by', ''),
                    item.get('created_at', datetime.now().isoformat()),
                    json.dumps(item.get('members', [])),
                    1 if item.get('is_public', True) else 0
                ))

        elif table_name == "recommendations":
            cursor.execute("DELETE FROM recommendations")
            for item in data:
                cursor.execute('''
                    INSERT INTO recommendations
                    (id, title, description, category, rating, tags, author, group_id, created_at, likes, dislikes, liked_by, disliked_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.get('id'),
                    item.get('title', ''),
                    item.get('description', ''),
                    item.get('category', ''),
                    item.get('rating', 0),
                    json.dumps(item.get('tags', [])),
                    item.get('author', ''),
                    item.get('group_id', 0),
                    item.get('created_at', datetime.now().isoformat()),
                    item.get('likes', 0),
                    item.get('dislikes', 0),
                    json.dumps(item.get('liked_by', [])),
                    json.dumps(item.get('disliked_by', []))
                ))

        conn.commit()
        return True

    except Exception as e:
        print(f"❌ Erro ao salvar {table_name}: {e}")
        return False

    finally:
        conn.close()

# Funções auxiliares para compatibilidade
def save_user_preferred_group(username, group_id):
    users = load_data("users", {})
    if username in users:
        users[username]["preferred_group"] = group_id
        users[username]["last_group"] = group_id
        save_data("users", users)
        return True
    return False

def get_user_preferred_group(username):
    users = load_data("users", {})
    if username in users:
        return users[username].get("preferred_group")
    return None

def get_user_last_group(username):
    users = load_data("users", {})
    if username in users:
        return users[username].get("last_group")
    return None

# Migra dados antigos se existirem
def migrate_old_data():
    """Migra dados dos arquivos JSON antigos para o SQLite"""
    old_files = {
        "users.json": "users",
        "groups.json": "groups",
        "recommendations.json": "recommendations"
    }

    for filename, table_name in old_files.items():
        if os.path.exists(f"data/{filename}"):
            try:
                with open(f"data/{filename}", 'r', encoding='utf-8') as f:
                    old_data = json.load(f)

                if old_data:
                    save_data(table_name, old_data)
                    print(f"✅ Migrados dados de {filename}")

                    # Renomeia arquivo antigo para backup
                    os.rename(f"data/{filename}", f"data/{filename}.backup")
            except Exception as e:
                print(f"⚠️  Não foi possível migrar {filename}: {e}")

# Inicializa o banco e migra dados
init_database()
migrate_old_data()
