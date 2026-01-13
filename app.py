import streamlit as st
import json
import time
from utils import load_data, save_data
from datetime import datetime

# Adicione esta função após os imports
def rerun():
    """Função compatível para rerun em todas versões do Streamlit"""
    try:
        # Tenta usar st.rerun() (versões mais novas)
        st.rerun()
    except AttributeError:
        # Fallback para versões mais antigas
        st.experimental_rerun()

# Configuração da página
st.set_page_config(
    page_title="Indica App",
    page_icon="🌟",
    layout="wide"
)

# Sistema de autenticação simples
def init_session_state():
    """Inicializa o estado da sessão"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'current_group' not in st.session_state:
        st.session_state.current_group = None

init_session_state()

# Funções de autenticação
def register_user(username, password):
    """Registra um novo usuário"""
    users = load_data("users.json", {})

    if username in users:
        return False, "Usuário já existe"

    # Em produção, use hashing para senhas!
    users[username] = {"password": password, "created_at": datetime.now().isoformat()}
    save_data("users.json", users)
    return True, "Usuário registrado com sucesso!"

def login_user(username, password):
    """Faz login do usuário"""
    users = load_data("users.json", {})

    if username not in users:
        return False, "Usuário não encontrado"

    # Em produção, use hashing para comparar senhas!
    if users[username]["password"] != password:
        return False, "Senha incorreta"

    st.session_state.authenticated = True
    st.session_state.username = username
    return True, "Login bem-sucedido!"

def logout():
    """Faz logout do usuário"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.current_group = None
    st.rerun()

# Funções para grupos
def create_group(group_name, description, categories):
    """Cria um novo grupo"""
    groups = load_data("groups.json", [])

    # Verifica se grupo já existe
    for group in groups:
        if group["name"].lower() == group_name.lower():
            return False, "Já existe um grupo com este nome"

    new_group = {
        "id": len(groups) + 1,
        "name": group_name,
        "description": description,
        "categories": categories,
        "created_by": st.session_state.username,
        "created_at": datetime.now().isoformat(),
        "members": [st.session_state.username],
        "is_public": True
    }

    groups.append(new_group)
    save_data("groups.json", groups)
    return True, "Grupo criado com sucesso!"

def join_group(group_id):
    """Entra em um grupo existente"""
    groups = load_data("groups.json", [])

    for group in groups:
        if group["id"] == group_id:
            if st.session_state.username not in group["members"]:
                group["members"].append(st.session_state.username)
                save_data("groups.json", groups)
                return True, f"Entrou no grupo '{group['name']}'!"
            return False, "Você já está neste grupo"

    return False, "Grupo não encontrado"

# Funções para recomendações
def add_recommendation(title, description, category, rating, tags=""):
    """Adiciona uma nova recomendação"""
    recommendations = load_data("recommendations.json", [])

    new_rec = {
        "id": len(recommendations) + 1,
        "title": title,
        "description": description,
        "category": category,
        "rating": rating,
        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
        "author": st.session_state.username,
        "group_id": st.session_state.current_group,
        "created_at": datetime.now().isoformat(),
        "likes": 0,
        "liked_by": []
    }

    recommendations.append(new_rec)
    save_data("recommendations.json", recommendations)
    return True, "Recomendação adicionada com sucesso!"

def get_group_recommendations(group_id):
    """Obtém recomendações de um grupo específico"""
    recommendations = load_data("recommendations.json", [])
    return [rec for rec in recommendations if rec["group_id"] == group_id]

def like_recommendation(rec_id):
    """Adiciona like a uma recomendação"""
    recommendations = load_data("recommendations.json", [])

    for rec in recommendations:
        if rec["id"] == rec_id:
            if st.session_state.username not in rec["liked_by"]:
                rec["likes"] += 1
                rec["liked_by"].append(st.session_state.username)
                save_data("recommendations.json", recommendations)
                return True
    return False

# Página de Login/Registro
def login_page():
    st.title("🌟 Indica App")
    st.markdown("### Faça login ou registre-se")

    tab1, tab2 = st.tabs(["Login", "Registro"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Nome de usuário")
            password = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar")

            if submit:
                if username and password:
                    success, message = login_user(username, password)
                    if success:
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)

    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Escolha um nome de usuário")
            new_password = st.text_input("Escolha uma senha", type="password")
            confirm_password = st.text_input("Confirme a senha", type="password")
            submit = st.form_submit_button("Registrar")

            if submit:
                if new_username and new_password:
                    if new_password == confirm_password:
                        success, message = register_user(new_username, new_password)
                        if success:
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("As senhas não coincidem")

# Página principal do aplicativo
def main_app():
    st.sidebar.title(f"👋 Olá, {st.session_state.username}!")

    # Menu lateral
    menu_options = ["🏠 Início", "👥 Grupos", "📝 Nova Indicação", "⭐ Minhas Indicações"]
    choice = st.sidebar.radio("Navegação", menu_options)

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair"):
        logout()

    # Página inicial
    if choice == "🏠 Início":
        st.title("Página Inicial")

        if st.session_state.current_group:
            groups = load_data("groups.json", [])
            current_group = next((g for g in groups if g["id"] == st.session_state.current_group), None)

            if current_group:
                st.header(f"📁 Grupo: {current_group['name']}")
                st.markdown(f"**Descrição:** {current_group['description']}")

                # Mostrar recomendações do grupo
                recommendations = get_group_recommendations(st.session_state.current_group)

                if recommendations:
                    st.subheader("📚 Recomendações Recentes")
                    for rec in recommendations[-10:]:  # Últimas 10 recomendações
                        with st.expander(f"{rec['title']} ⭐ {rec['rating']}/5"):
                            st.markdown(f"**Categoria:** {rec['category']}")
                            st.markdown(f"**Descrição:** {rec['description']}")
                            st.markdown(f"**Por:** {rec['author']}")
                            st.markdown(f"**Tags:** {', '.join(rec['tags']) if rec['tags'] else 'Nenhuma'}")

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button(f"👍 {rec['likes']}", key=f"like_{rec['id']}"):
                                    if like_recommendation(rec['id']):
                                        st.success("Obrigado pelo like!")
                                        time.sleep(0.5)
                                        st.rerun()
                else:
                    st.info("Nenhuma recomendação neste grupo ainda. Seja o primeiro a compartilhar!")
        else:
            st.info("Selecione um grupo para ver as recomendações")

    # Página de Grupos
    elif choice == "👥 Grupos":
        st.title("Grupos")

        tab1, tab2, tab3 = st.tabs(["Meus Grupos", "Explorar Grupos", "Criar Grupo"])

        with tab1:
            groups = load_data("groups.json", [])
            user_groups = [g for g in groups if st.session_state.username in g["members"]]

            if user_groups:
                st.subheader("Grupos que você participa")
                for group in user_groups:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {group['name']}")
                        st.markdown(f"{group['description']}")
                        st.markdown(f"**Categorias:** {', '.join(group['categories'])}")
                        st.markdown(f"**Membros:** {len(group['members'])}")

                    with col2:
                        if st.button("Entrar", key=f"enter_{group['id']}"):
                            st.session_state.current_group = group["id"]
                            st.success(f"Entrou no grupo {group['name']}!")
                            time.sleep(1)
                            st.rerun()
            else:
                st.info("Você ainda não está em nenhum grupo")

        with tab2:
            groups = load_data("groups.json", [])
            public_groups = [g for g in groups if g["is_public"] and st.session_state.username not in g["members"]]

            if public_groups:
                st.subheader("Grupos Públicos Disponíveis")
                for group in public_groups:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {group['name']}")
                        st.markdown(f"{group['description']}")
                        st.markdown(f"**Criado por:** {group['created_by']}")
                        st.markdown(f"**Membros:** {len(group['members'])}")

                    with col2:
                        if st.button("Participar", key=f"join_{group['id']}"):
                            success, message = join_group(group["id"])
                            if success:
                                st.success(message)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(message)
            else:
                st.info("Nenhum grupo público disponível")

        with tab3:
            st.subheader("Criar Novo Grupo")
            with st.form("create_group_form"):
                group_name = st.text_input("Nome do Grupo")
                description = st.text_area("Descrição do Grupo")

                # Categorias padrão
                default_categories = ["Filmes", "Séries", "Livros", "Produtos de Beleza", "Restaurantes", "Música", "Jogos", "Tecnologia"]
                categories = st.multiselect(
                    "Categorias disponíveis no grupo",
                    default_categories,
                    default=["Filmes", "Séries"]
                )

                if st.form_submit_button("Criar Grupo"):
                    if group_name and description and categories:
                        success, message = create_group(group_name, description, categories)
                        if success:
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Preencha todos os campos obrigatórios")

    # Página de Nova Indicação
    elif choice == "📝 Nova Indicação":
        st.title("Nova Indicação")

        if not st.session_state.current_group:
            st.warning("Você precisa entrar em um grupo primeiro para fazer indicações")
            return

        groups = load_data("groups.json", [])
        current_group = next((g for g in groups if g["id"] == st.session_state.current_group), None)

        if current_group:
            with st.form("recommendation_form"):
                st.markdown(f"**Grupo:** {current_group['name']}")

                title = st.text_input("Título da Indicação")
                description = st.text_area("Descrição detalhada")

                # Usar categorias do grupo
                category = st.selectbox("Categoria", current_group["categories"])

                rating = st.slider("Avaliação", 1, 5, 5)
                tags = st.text_input("Tags (separadas por vírgula)")

                if st.form_submit_button("Publicar Indicação"):
                    if title and description:
                        success, message = add_recommendation(title, description, category, rating, tags)
                        if success:
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Preencha título e descrição")

    # Página de Minhas Indicações
    elif choice == "⭐ Minhas Indicações":
        st.title("Minhas Indicações")

        recommendations = load_data("recommendations.json", [])
        my_recommendations = [rec for rec in recommendations if rec["author"] == st.session_state.username]

        if my_recommendations:
            for rec in my_recommendations:
                groups = load_data("groups.json", [])
                group_name = next((g["name"] for g in groups if g["id"] == rec["group_id"]), "Grupo Desconhecido")

                with st.expander(f"{rec['title']} - {group_name}"):
                    st.markdown(f"**Categoria:** {rec['category']}")
                    st.markdown(f"**Descrição:** {rec['description']}")
                    st.markdown(f"**Avaliação:** ⭐ {rec['rating']}/5")
                    st.markdown(f"**Likes:** {rec['likes']}")
                    st.markdown(f"**Tags:** {', '.join(rec['tags']) if rec['tags'] else 'Nenhuma'}")
                    st.markdown(f"**Data:** {rec['created_at'][:10]}")
        else:
            st.info("Você ainda não fez nenhuma indicação")

# Ponto de entrada da aplicação
def main():
    if st.session_state.authenticated:
        main_app()
    else:
        login_page()

if __name__ == "__main__":
    main()
