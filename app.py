import streamlit as st
import json
import os
import time
from datetime import datetime
from utils import load_data, save_data, save_user_preferred_group, get_user_preferred_group, get_user_last_group

# Configuração da página
st.set_page_config(
    page_title="Indica App",
    page_icon="🌟",
    layout="wide"
)

# Função compatível para rerun
def rerun():
    """Função compatível para rerun em todas versões do Streamlit"""
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# Sistema de autenticação simples
def init_session_state():
    """Inicializa o estado da sessão"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'current_group' not in st.session_state:
        st.session_state.current_group = None
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    if 'show_group_details' not in st.session_state:
        st.session_state.show_group_details = False

init_session_state()

# Funções de autenticação
def register_user(username, password):
    """Registra um novo usuário"""
    users = load_data("users.json", {})

    if username in users:
        return False, "Usuário já existe"

    # Em produção, use hashing para senhas!
    users[username] = {
        "password": password,
        "created_at": datetime.now().isoformat(),
        "preferred_group": None,
        "last_group": None
    }
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

    # Restaura o último grupo do usuário
    last_group = users[username].get("last_group")
    if last_group:
        # Verifica se o grupo ainda existe e o usuário ainda é membro
        groups = load_data("groups.json", [])
        group_exists = any(g["id"] == last_group for g in groups)

        if group_exists:
            # Verifica se usuário ainda é membro
            target_group = next((g for g in groups if g["id"] == last_group), None)
            if target_group and username in target_group.get("members", []):
                st.session_state.current_group = last_group
                save_user_preferred_group(username, last_group)

    return True, "Login bem-sucedido!"

def logout():
    """Faz logout do usuário"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.current_group = None
    st.session_state.page = "home"
    st.session_state.show_group_details = False
    rerun()

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

    # Atualiza grupo atual e salva preferência
    st.session_state.current_group = new_group["id"]
    save_user_preferred_group(st.session_state.username, new_group["id"])

    return True, "Grupo criado com sucesso! Você já está dentro dele."

def join_group(group_id):
    """Entra em um grupo existente"""
    groups = load_data("groups.json", [])

    for group in groups:
        if group["id"] == group_id:
            if st.session_state.username not in group["members"]:
                group["members"].append(st.session_state.username)
                save_data("groups.json", groups)

                # Atualiza grupo atual e salva preferência
                st.session_state.current_group = group_id
                save_user_preferred_group(st.session_state.username, group_id)

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

def get_user_recommendations(username):
    """Obtém recomendações de um usuário específico"""
    recommendations = load_data("recommendations.json", [])
    return [rec for rec in recommendations if rec["author"] == username]

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
                        rerun()
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
                            rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("As senhas não coincidem")

# Funções para renderizar páginas
def render_home_page():
    """Renderiza a página inicial"""
    st.title("Página Inicial")

    # Carrega grupos do usuário
    groups = load_data("groups.json", [])
    user_groups = [g for g in groups if st.session_state.username in g.get("members", [])]

    # Se não tem grupo selecionado
    if not st.session_state.current_group:
        if user_groups:
            # Sugere entrar em um grupo
            st.info("💡 Você está em grupos, mas nenhum está selecionado.")

            # Estatísticas rápidas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Grupos", len(user_groups))
            with col2:
                total_members = sum(len(g["members"]) for g in user_groups)
                st.metric("Total de Membros", total_members)
            with col3:
                if user_groups:
                    st.metric("Sugerido", user_groups[0]["name"])

            st.subheader("📋 Seus Grupos:")

            # Mostra grupos em cards
            cols = st.columns(2)
            for idx, group in enumerate(user_groups):
                with cols[idx % 2]:
                    with st.container():
                        st.markdown(f"### {group['name']}")
                        st.markdown(f"📝 {group['description'][:100]}..." if len(group['description']) > 100 else f"📝 {group['description']}")
                        st.markdown(f"👥 {len(group['members'])} membros")
                        st.markdown(f"🏷️ {', '.join(group['categories'][:3])}")

                        if st.button(f"Entrar em {group['name']}", key=f"enter_{group['id']}"):
                            st.session_state.current_group = group["id"]
                            save_user_preferred_group(st.session_state.username, group["id"])
                            st.success(f"Entrou no grupo!")
                            time.sleep(1)
                            rerun()

            st.markdown("---")
            st.markdown("### Ou")

        else:
            # Usuário não está em nenhum grupo
            st.info("🌟 Bem-vindo ao Indica App!")

            st.markdown("""
            ### Para começar:
            1. **Explore grupos públicos** ou **crie seu próprio grupo**
            2. **Convide amigos** para participar
            3. **Compartilhe recomendações** sobre filmes, séries, produtos, etc.
            4. **Descubra** novas indicações da comunidade
            """)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("👥 Explorar Grupos", use_container_width=True):
                    st.session_state.page = "groups"
                    rerun()
            with col2:
                if st.button("🚀 Criar Meu Grupo", use_container_width=True):
                    st.session_state.page = "create_group"
                    rerun()

    # Se tem grupo selecionado, mostra conteúdo
    else:
        groups = load_data("groups.json", [])
        current_group = next((g for g in groups if g["id"] == st.session_state.current_group), None)

        if current_group:
            # Cabeçalho com opções
            col1, col2 = st.columns([3, 1])
            with col1:
                st.header(f"📚 Recomendações em {current_group['name']}")
            with col2:
                if st.button("🔄 Trocar Grupo"):
                    st.session_state.current_group = None
                    rerun()

            # Mostra informações do grupo
            with st.expander(f"ℹ️ Sobre o grupo {current_group['name']}"):
                st.markdown(f"**Descrição:** {current_group['description']}")
                st.markdown(f"**Criado por:** {current_group['created_by']}")
                st.markdown(f"**Membros:** {', '.join(current_group['members'])}")
                st.markdown(f"**Categorias:** {', '.join(current_group['categories'])}")

            # Mostrar recomendações do grupo
            recommendations = get_group_recommendations(st.session_state.current_group)

            if recommendations:
                st.subheader(f"📝 {len(recommendations)} Recomendações")

                # Filtros
                col1, col2, col3 = st.columns(3)
                with col1:
                    categories = list(set([r["category"] for r in recommendations]))
                    selected_category = st.selectbox("Filtrar por categoria", ["Todas"] + categories)
                with col2:
                    sort_by = st.selectbox("Ordenar por", ["Mais recentes", "Mais likes", "Melhor avaliadas"])
                with col3:
                    search_term = st.text_input("Buscar por título ou tags")

                # Aplicar filtros
                filtered_recs = recommendations

                if selected_category != "Todas":
                    filtered_recs = [r for r in filtered_recs if r["category"] == selected_category]

                if search_term:
                    search_term = search_term.lower()
                    filtered_recs = [
                        r for r in filtered_recs
                        if search_term in r["title"].lower() or
                        any(search_term in tag.lower() for tag in r["tags"])
                    ]

                # Ordenar
                if sort_by == "Mais recentes":
                    filtered_recs.sort(key=lambda x: x["created_at"], reverse=True)
                elif sort_by == "Mais likes":
                    filtered_recs.sort(key=lambda x: x["likes"], reverse=True)
                elif sort_by == "Melhor avaliadas":
                    filtered_recs.sort(key=lambda x: x["rating"], reverse=True)

                # Mostrar recomendações filtradas
                for rec in filtered_recs:
                    with st.expander(f"⭐ {rec['rating']}/5 | {rec['title']} | 👍 {rec['likes']}"):
                        st.markdown(f"**Categoria:** {rec['category']}")
                        st.markdown(f"**Descrição:** {rec['description']}")
                        st.markdown(f"**Por:** {rec['author']}")
                        st.markdown(f"**Tags:** {', '.join(rec['tags']) if rec['tags'] else 'Nenhuma'}")
                        st.markdown(f"**Data:** {rec['created_at'][:10]}")

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"👍 Curtir ({rec['likes']})", key=f"like_{rec['id']}"):
                                if like_recommendation(rec['id']):
                                    st.success("Obrigado pelo like!")
                                    time.sleep(0.5)
                                    rerun()
                        with col2:
                            if st.button("📋 Ver detalhes", key=f"details_{rec['id']}"):
                                st.session_state.selected_recommendation = rec['id']
                                rerun()
            else:
                st.info("Nenhuma recomendação neste grupo ainda. Seja o primeiro a compartilhar!")
                if st.button("📝 Criar primeira recomendação"):
                    st.session_state.page = "new_recommendation"
                    rerun()

def render_groups_page():
    """Renderiza a página de grupos"""
    st.title("Grupos")

    tab1, tab2, tab3 = st.tabs(["Meus Grupos", "Explorar Grupos", "Criar Grupo"])

    with tab1:
        groups = load_data("groups.json", [])
        user_groups = [g for g in groups if st.session_state.username in g.get("members", [])]

        if user_groups:
            st.subheader(f"👥 {len(user_groups)} Grupos")

            for group in user_groups:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        st.markdown(f"### {group['name']}")
                        st.markdown(f"{group['description']}")
                        st.markdown(f"**Categorias:** {', '.join(group['categories'][:3])}")

                    with col2:
                        st.markdown(f"**Criado por:** {group['created_by']}")
                        st.markdown(f"**Membros:** {len(group['members'])}")
                        st.markdown(f"**Recomendações:** {len(get_group_recommendations(group['id']))}")

                    with col3:
                        # Se já é o grupo atual
                        if st.session_state.current_group == group["id"]:
                            st.success("✅ Atual")
                        else:
                            if st.button("Entrar", key=f"enter_{group['id']}"):
                                st.session_state.current_group = group["id"]
                                save_user_preferred_group(st.session_state.username, group["id"])
                                st.success(f"Entrou no grupo {group['name']}!")
                                time.sleep(1)
                                rerun()

                    st.markdown("---")
        else:
            st.info("Você ainda não está em nenhum grupo")
            if st.button("🔍 Explorar Grupos Públicos"):
                st.session_state.page = "explore"
                rerun()

    with tab2:
        groups = load_data("groups.json", [])
        public_groups = [g for g in groups if g["is_public"] and st.session_state.username not in g.get("members", [])]

        if public_groups:
            st.subheader(f"🔍 {len(public_groups)} Grupos Públicos")

            for group in public_groups:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        st.markdown(f"### {group['name']}")
                        st.markdown(f"{group['description']}")
                        st.markdown(f"**Categorias:** {', '.join(group['categories'][:3])}")

                    with col2:
                        st.markdown(f"**Criado por:** {group['created_by']}")
                        st.markdown(f"**Membros:** {len(group['members'])}")

                    with col3:
                        if st.button("Participar", key=f"join_{group['id']}"):
                            success, message = join_group(group["id"])
                            if success:
                                st.success(message)
                                time.sleep(1)
                                rerun()
                            else:
                                st.error(message)

                    st.markdown("---")
        else:
            st.info("Nenhum grupo público disponível no momento")

    with tab3:
        st.subheader("Criar Novo Grupo")
        with st.form("create_group_form"):
            group_name = st.text_input("Nome do Grupo*")
            description = st.text_area("Descrição do Grupo*")

            # Categorias padrão
            default_categories = ["Filmes", "Séries", "Livros", "Produtos de Beleza",
                                "Restaurantes", "Música", "Jogos", "Tecnologia",
                                "Viagens", "Esportes", "Moda", "Comida"]
            categories = st.multiselect(
                "Categorias disponíveis no grupo*",
                default_categories,
                default=["Filmes", "Séries"]
            )

            is_public = st.checkbox("Grupo público (qualquer um pode ver e pedir para participar)", value=True)

            if st.form_submit_button("Criar Grupo"):
                if group_name and description and categories:
                    success, message = create_group(group_name, description, categories)
                    if success:
                        st.success(message)
                        time.sleep(1)
                        rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Preencha todos os campos obrigatórios (*)")

def render_new_recommendation_page():
    """Renderiza a página de nova recomendação"""
    st.title("Nova Indicação")

    if not st.session_state.current_group:
        st.warning("⚠️ Você precisa entrar em um grupo primeiro para fazer indicações")

        groups = load_data("groups.json", [])
        user_groups = [g for g in groups if st.session_state.username in g.get("members", [])]

        if user_groups:
            st.info("Selecione um grupo:")
            for group in user_groups:
                if st.button(f"📁 {group['name']}", key=f"select_for_rec_{group['id']}"):
                    st.session_state.current_group = group["id"]
                    save_user_preferred_group(st.session_state.username, group["id"])
                    rerun()
        else:
            st.info("Você não está em nenhum grupo ainda")
            if st.button("👥 Ir para Grupos"):
                st.session_state.page = "groups"
                rerun()

        return

    # Se tem grupo selecionado
    groups = load_data("groups.json", [])
    current_group = next((g for g in groups if g["id"] == st.session_state.current_group), None)

    if current_group:
        with st.form("recommendation_form"):
            st.markdown(f"**Grupo atual:** {current_group['name']}")

            title = st.text_input("Título da Indicação*")
            description = st.text_area("Descrição detalhada*", height=150)

            # Usar categorias do grupo
            category = st.selectbox("Categoria*", current_group["categories"])

            col1, col2 = st.columns(2)
            with col1:
                rating = st.slider("Avaliação*", 1, 5, 5)
            with col2:
                tags = st.text_input("Tags (separadas por vírgula)")

            # Dicas
            with st.expander("💡 Dicas para uma boa recomendação"):
                st.markdown("""
                - Seja específico na descrição
                - Explique por que recomenda
                - Inclua detalhes relevantes
                - Use tags para facilitar a busca
                """)

            submitted = st.form_submit_button("📤 Publicar Indicação")

            if submitted:
                if title and description:
                    success, message = add_recommendation(title, description, category, rating, tags)
                    if success:
                        st.success(message)
                        time.sleep(1)
                        st.session_state.page = "home"
                        rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Preencha os campos obrigatórios (*)")
    else:
        st.error("Grupo não encontrado")

def render_my_recommendations_page():
    """Renderiza a página das minhas recomendações"""
    st.title("Minhas Indicações")

    recommendations = get_user_recommendations(st.session_state.username)

    if recommendations:
        st.subheader(f"📊 {len(recommendations)} Recomendações Criadas")

        # Estatísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_likes = sum(r["likes"] for r in recommendations)
            st.metric("Total de Likes", total_likes)
        with col2:
            avg_rating = sum(r["rating"] for r in recommendations) / len(recommendations)
            st.metric("Média de Avaliação", f"{avg_rating:.1f}/5")
        with col3:
            categories = len(set(r["category"] for r in recommendations))
            st.metric("Categorias", categories)
        with col4:
            groups = len(set(r["group_id"] for r in recommendations))
            st.metric("Grupos", groups)

        st.markdown("---")

        # Lista de recomendações
        for rec in sorted(recommendations, key=lambda x: x["created_at"], reverse=True):
            groups = load_data("groups.json", [])
            group_name = next((g["name"] for g in groups if g["id"] == rec["group_id"]), "Grupo Desconhecido")

            with st.expander(f"{rec['title']} | ⭐ {rec['rating']}/5 | 👍 {rec['likes']} | 📁 {group_name}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Categoria:** {rec['category']}")
                    st.markdown(f"**Descrição:** {rec['description']}")
                    st.markdown(f"**Tags:** {', '.join(rec['tags']) if rec['tags'] else 'Nenhuma'}")
                with col2:
                    st.markdown(f"**Grupo:** {group_name}")
                    st.markdown(f"**Data:** {rec['created_at'][:10]}")
                    st.markdown(f"**Likes:** {rec['likes']}")

                    # Botão para ir para o grupo
                    if st.button("Ir para grupo", key=f"goto_{rec['id']}"):
                        st.session_state.current_group = rec["group_id"]
                        save_user_preferred_group(st.session_state.username, rec["group_id"])
                        st.session_state.page = "home"
                        rerun()
    else:
        st.info("Você ainda não fez nenhuma indicação")
        st.markdown("""
        ### Comece a compartilhar suas indicações!

        **Ideias do que compartilhar:**
        - Filmes que você amou
        - Séries que maratonou
        - Produtos que realmente funcionam
        - Restaurantes imperdíveis
        - Livros que mudaram sua perspectiva
        """)

        if st.button("📝 Fazer minha primeira indicação"):
            st.session_state.page = "new_recommendation"
            rerun()

# Página principal do aplicativo
def main_app():
    st.sidebar.title(f"👋 Olá, {st.session_state.username}!")

    # ===== Seletor de grupos no sidebar =====
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 Grupo Atual")

    groups = load_data("groups.json", [])
    user_groups = [g for g in groups if st.session_state.username in g.get("members", [])]

    if user_groups:
        # Encontra o grupo atual
        current_group_info = None
        if st.session_state.current_group:
            current_group_info = next(
                (g for g in user_groups if g["id"] == st.session_state.current_group),
                None
            )

        # Lista de grupos para seleção
        group_names = [g["name"] for g in user_groups]

        # Índice do grupo atual na lista
        current_index = 0
        if current_group_info:
            try:
                current_index = group_names.index(current_group_info["name"])
            except ValueError:
                current_index = 0

        # Dropdown para selecionar grupo
        selected_group_name = st.sidebar.selectbox(
            "Selecione seu grupo:",
            options=group_names,
            index=current_index,
            key="group_selector"
        )

        # Atualiza quando selecionar diferente
        if selected_group_name:
            selected_group = next(g for g in user_groups if g["name"] == selected_group_name)
            if selected_group["id"] != st.session_state.current_group:
                st.session_state.current_group = selected_group["id"]
                save_user_preferred_group(st.session_state.username, selected_group["id"])
                st.sidebar.success(f"Grupo '{selected_group_name}' selecionado!")
                time.sleep(0.5)
                rerun()

        # Mostra informações do grupo atual
        if current_group_info:
            st.sidebar.markdown(f"**Grupo:** {current_group_info['name']}")
            st.sidebar.markdown(f"**Membros:** {len(current_group_info['members'])}")
            st.sidebar.markdown(f"**Categorias:** {', '.join(current_group_info['categories'][:2])}")

            # Botão para ver detalhes
            if st.sidebar.button("📊 Ver detalhes do grupo"):
                st.session_state.show_group_details = not st.session_state.show_group_details
                rerun()
    else:
        st.sidebar.warning("Você não está em nenhum grupo")
        if st.sidebar.button("👥 Explorar grupos"):
            st.session_state.page = "groups"
            rerun()

    # Menu principal
    st.sidebar.markdown("---")
    menu_options = ["🏠 Início", "👥 Grupos", "📝 Nova Indicação", "⭐ Minhas Indicações"]

    # Atualiza página baseada na escolha
    choice = st.sidebar.radio("Navegação", menu_options)

    if choice == "🏠 Início":
        st.session_state.page = "home"
    elif choice == "👥 Grupos":
        st.session_state.page = "groups"
    elif choice == "📝 Nova Indicação":
        st.session_state.page = "new_recommendation"
    elif choice == "⭐ Minhas Indicações":
        st.session_state.page = "my_recommendations"

    st.sidebar.markdown("---")

    # Informações do usuário
    st.sidebar.markdown("### 👤 Meu Perfil")
    st.sidebar.write(f"Usuário: {st.session_state.username}")

    # Botão de logout
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        logout()

    # Renderiza a página atual
    if st.session_state.page == "home":
        render_home_page()
    elif st.session_state.page == "groups":
        render_groups_page()
    elif st.session_state.page == "new_recommendation":
        render_new_recommendation_page()
    elif st.session_state.page == "my_recommendations":
        render_my_recommendations_page()

# Ponto de entrada da aplicação
def main():
    if st.session_state.authenticated:
        main_app()
    else:
        login_page()

if __name__ == "__main__":
    main()
