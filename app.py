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
    if 'show_registration_success' not in st.session_state:
        st.session_state.show_registration_success = False
    if 'login_tab' not in st.session_state:
        st.session_state.login_tab = "Login"

init_session_state()

# ==================== FUNÇÕES COM FALLBACKS ====================

def register_user(username, password):
    """Registra um novo usuário com estrutura atualizada"""
    users = load_data("users.json", {})

    if username in users:
        return False, "Usuário já existe"

    # Estrutura completa do usuário
    users[username] = {
        "password": password,
        "created_at": datetime.now().isoformat(),
        "preferred_group": None,
        "last_group": None
    }
    save_data("users.json", users)
    return True, "Usuário registrado com sucesso!"

def login_user(username, password):
    """Faz login do usuário com compatibilidade retroativa"""
    users = load_data("users.json", {})

    if username not in users:
        return False, "Usuário não encontrado"

    # Suporte para estrutura antiga (senha direta) e nova (dicionário)
    user_data = users[username]

    # Se user_data é string (estrutura antiga), é a senha diretamente
    if isinstance(user_data, str):
        stored_password = user_data
        # Atualiza para nova estrutura
        users[username] = {
            "password": stored_password,
            "created_at": datetime.now().isoformat(),
            "preferred_group": None,
            "last_group": None
        }
        save_data("users.json", users)
        user_data = users[username]

    # Verifica senha
    if user_data.get("password") != password:
        return False, "Senha incorreta"

    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.show_registration_success = False

    # Restaura o último grupo do usuário
    last_group = user_data.get("last_group")
    if last_group:
        groups = load_data("groups.json", [])
        group_exists = any(g.get("id") == last_group for g in groups)

        if group_exists:
            # Verifica se usuário ainda é membro
            target_group = next((g for g in groups if g.get("id") == last_group), None)
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
    st.session_state.show_registration_success = False
    rerun()

# ==================== FUNÇÕES PARA GRUPOS ====================

def create_group(group_name, description, categories):
    """Cria um novo grupo com estrutura consistente"""
    groups = load_data("groups.json", [])

    # Verifica se grupo já existe
    for group in groups:
        if group.get("name", "").lower() == group_name.lower():
            return False, "Já existe um grupo com este nome"

    # Cria ID único
    existing_ids = [g.get("id", 0) for g in groups if "id" in g]
    new_id = max(existing_ids) + 1 if existing_ids else 1

    new_group = {
        "id": new_id,
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
    st.session_state.current_group = new_id
    save_user_preferred_group(st.session_state.username, new_id)

    return True, "Grupo criado com sucesso! Você já está dentro dele."

def join_group(group_id):
    """Entra em um grupo existente com tratamento seguro"""
    groups = load_data("groups.json", [])

    for group in groups:
        if group.get("id") == group_id:
            # Garante que existe campo members
            if "members" not in group:
                group["members"] = []

            if st.session_state.username not in group["members"]:
                group["members"].append(st.session_state.username)
                save_data("groups.json", groups)

                # Atualiza grupo atual e salva preferência
                st.session_state.current_group = group_id
                save_user_preferred_group(st.session_state.username, group_id)

                return True, f"Entrou no grupo '{group.get('name', 'Sem nome')}'!"
            return False, "Você já está neste grupo"

    return False, "Grupo não encontrado"

# ==================== FUNÇÕES PARA RECOMENDAÇÕES ====================

def add_recommendation(title, description, category, rating, tags=""):
    """Adiciona uma nova recomendação com estrutura completa"""
    recommendations = load_data("recommendations.json", [])

    # Cria ID único
    existing_ids = [r.get("id", 0) for r in recommendations if "id" in r]
    new_id = max(existing_ids) + 1 if existing_ids else 1

    # Processa tags
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    new_rec = {
        "id": new_id,
        "title": title,
        "description": description,
        "category": category,
        "rating": rating,
        "tags": tag_list,
        "author": st.session_state.username,
        "group_id": st.session_state.current_group,
        "created_at": datetime.now().isoformat(),
        "likes": 0,
        "dislikes": 0,
        "liked_by": [],
        "disliked_by": []
    }

    recommendations.append(new_rec)
    save_data("recommendations.json", recommendations)
    return True, "Recomendação adicionada com sucesso!"

def get_group_recommendations(group_id):
    """Obtém recomendações de um grupo específico com fallback"""
    recommendations = load_data("recommendations.json", [])

    # Filtra por grupo_id e garante estrutura
    filtered = []
    for rec in recommendations:
        # Se não tem group_id, pula (recomendação inválida)
        if "group_id" not in rec:
            continue

        if rec["group_id"] == group_id:
            # Garante campos obrigatórios
            if "dislikes" not in rec:
                rec["dislikes"] = 0
            if "disliked_by" not in rec:
                rec["disliked_by"] = []
            if "likes" not in rec:
                rec["likes"] = 0
            if "liked_by" not in rec:
                rec["liked_by"] = []

            filtered.append(rec)

    return filtered

def get_user_recommendations(username):
    """Obtém recomendações de um usuário específico"""
    recommendations = load_data("recommendations.json", [])
    return [rec for rec in recommendations if rec.get("author") == username]

def like_recommendation(rec_id):
    """Adiciona like a uma recomendação com sistema toggle"""
    recommendations = load_data("recommendations.json", [])

    for rec in recommendations:
        if rec.get("id") == rec_id:
            username = st.session_state.username

            # Garante campos existem
            if "likes" not in rec:
                rec["likes"] = 0
            if "liked_by" not in rec:
                rec["liked_by"] = []
            if "dislikes" not in rec:
                rec["dislikes"] = 0
            if "disliked_by" not in rec:
                rec["disliked_by"] = []

            # Sistema toggle: like/dislike são mutuamente exclusivos
            if username in rec["liked_by"]:
                # Remove like
                rec["likes"] -= 1
                rec["liked_by"].remove(username)
            else:
                # Adiciona like, remove dislike se existir
                if username in rec["disliked_by"]:
                    rec["dislikes"] -= 1
                    rec["disliked_by"].remove(username)

                rec["likes"] += 1
                rec["liked_by"].append(username)

            save_data("recommendations.json", recommendations)
            return True
    return False

def dislike_recommendation(rec_id):
    """Adiciona dislike a uma recomendação com sistema toggle"""
    recommendations = load_data("recommendations.json", [])

    for rec in recommendations:
        if rec.get("id") == rec_id:
            username = st.session_state.username

            # Garante campos existem
            if "dislikes" not in rec:
                rec["dislikes"] = 0
            if "disliked_by" not in rec:
                rec["disliked_by"] = []
            if "likes" not in rec:
                rec["likes"] = 0
            if "liked_by" not in rec:
                rec["liked_by"] = []

            # Sistema toggle: like/dislike são mutuamente exclusivos
            if username in rec["disliked_by"]:
                # Remove dislike
                rec["dislikes"] -= 1
                rec["disliked_by"].remove(username)
            else:
                # Adiciona dislike, remove like se existir
                if username in rec["liked_by"]:
                    rec["likes"] -= 1
                    rec["liked_by"].remove(username)

                rec["dislikes"] += 1
                rec["disliked_by"].append(username)

            save_data("recommendations.json", recommendations)
            return True
    return False

# ==================== PÁGINA DE LOGIN/REGISTRO ====================

def login_page():
    st.title("🌟 Indica App")

    # Mostra mensagem de registro bem-sucedido se existir
    if st.session_state.get('show_registration_success'):
        st.success("✅ Registro realizado com sucesso! Faça login para continuar.")
        st.session_state.show_registration_success = False

    st.markdown("### Faça login ou registre-se")

    # Controla qual tab mostrar
    if st.session_state.get('force_login_tab'):
        tab = st.tabs(["Login", "Registro"])
        active_tab = 0
        st.session_state.force_login_tab = False
    else:
        tab = st.tabs(["Login", "Registro"])
        active_tab = 0 if st.session_state.login_tab == "Login" else 1

    with tab[0]:  # Login
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
                else:
                    st.error("Preencha todos os campos")

    with tab[1]:  # Registro
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
                            st.session_state.show_registration_success = True
                            st.session_state.force_login_tab = True
                            time.sleep(1)
                            rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("As senhas não coincidem")
                else:
                    st.error("Preencha todos os campos")

        st.markdown("---")
        if st.button("← Voltar para Login"):
            st.session_state.force_login_tab = True
            rerun()

# ==================== FUNÇÕES DE RENDERIZAÇÃO ====================

def render_home_page():
    """Renderiza a página inicial"""
    st.title("Página Inicial")

    groups = load_data("groups.json", [])
    user_groups = [g for g in groups if st.session_state.username in g.get("members", [])]

    if not st.session_state.current_group:
        if user_groups:
            st.info("💡 Você está em grupos, mas nenhum está selecionado.")

            cols = st.columns(3)
            with cols[0]:
                st.metric("Grupos", len(user_groups))
            with cols[1]:
                total_members = sum(len(g.get("members", [])) for g in user_groups)
                st.metric("Membros", total_members)
            with cols[2]:
                if user_groups:
                    st.metric("Sugerido", user_groups[0].get("name", "Sem nome"))

            st.subheader("📋 Seus Grupos:")

            # Mostra grupos em cards
            col_count = 2
            columns = st.columns(col_count)
            for idx, group in enumerate(user_groups):
                with columns[idx % col_count]:
                    with st.container():
                        st.markdown(f"### {group.get('name', 'Sem nome')}")
                        desc = group.get('description', 'Sem descrição')
                        st.markdown(f"📝 {desc[:100]}..." if len(desc) > 100 else f"📝 {desc}")
                        st.markdown(f"👥 {len(group.get('members', []))} membros")
                        categories = group.get('categories', [])
                        st.markdown(f"🏷️ {', '.join(categories[:3])}")

                        if st.button(f"Entrar", key=f"enter_{group.get('id', idx)}"):
                            st.session_state.current_group = group.get("id")
                            save_user_preferred_group(st.session_state.username, group.get("id"))
                            st.success("Entrou no grupo!")
                            time.sleep(1)
                            rerun()

            st.markdown("---")
        else:
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

    else:
        # Tem grupo selecionado
        current_group = next((g for g in groups if g.get("id") == st.session_state.current_group), None)

        if current_group:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.header(f"📚 Recomendações em {current_group.get('name', 'Sem nome')}")
            with col2:
                if st.button("🔄 Trocar Grupo"):
                    st.session_state.current_group = None
                    rerun()

            with st.expander(f"ℹ️ Sobre o grupo {current_group.get('name', 'Sem nome')}"):
                st.markdown(f"**Descrição:** {current_group.get('description', 'Sem descrição')}")
                st.markdown(f"**Criado por:** {current_group.get('created_by', 'Desconhecido')}")
                st.markdown(f"**Membros:** {', '.join(current_group.get('members', []))}")
                st.markdown(f"**Categorias:** {', '.join(current_group.get('categories', []))}")

            recommendations = get_group_recommendations(st.session_state.current_group)

            if recommendations:
                st.subheader(f"📝 {len(recommendations)} Recomendações")

                # Filtros
                col1, col2, col3 = st.columns(3)
                with col1:
                    categories = list(set([r.get("category", "") for r in recommendations]))
                    categories = [c for c in categories if c]
                    selected_category = st.selectbox("Filtrar por categoria", ["Todas"] + categories)
                with col2:
                    sort_options = ["Mais recentes", "Mais likes", "Melhor avaliadas", "Mais polêmicas"]
                    sort_by = st.selectbox("Ordenar por", sort_options)
                with col3:
                    search_term = st.text_input("Buscar por título ou tags")

                # Aplica filtros
                filtered_recs = recommendations

                if selected_category != "Todas":
                    filtered_recs = [r for r in filtered_recs if r.get("category") == selected_category]

                if search_term:
                    search_term = search_term.lower()
                    filtered_recs = [
                        r for r in filtered_recs
                        if search_term in r.get("title", "").lower() or
                        any(search_term in tag.lower() for tag in r.get("tags", []))
                    ]

                # Ordena
                if sort_by == "Mais recentes":
                    filtered_recs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                elif sort_by == "Mais likes":
                    filtered_recs.sort(key=lambda x: x.get("likes", 0), reverse=True)
                elif sort_by == "Melhor avaliadas":
                    filtered_recs.sort(key=lambda x: x.get("rating", 0), reverse=True)
                elif sort_by == "Mais polêmicas":
                    filtered_recs.sort(key=lambda x: abs(x.get("likes", 0) - x.get("dislikes", 0)))

                # Mostra recomendações
                for rec in filtered_recs:
                    likes = rec.get("likes", 0)
                    dislikes = rec.get("dislikes", 0)
                    saldo = likes - dislikes

                    with st.expander(f"⭐ {rec.get('rating', 0)}/5 | {rec.get('title', 'Sem título')} | 👍 {likes} | 👎 {dislikes} | 📊 {saldo}"):
                        st.markdown(f"**Categoria:** {rec.get('category', 'Sem categoria')}")
                        st.markdown(f"**Descrição:** {rec.get('description', 'Sem descrição')}")
                        st.markdown(f"**Por:** {rec.get('author', 'Anônimo')}")
                        tags = rec.get("tags", [])
                        st.markdown(f"**Tags:** {', '.join(tags) if tags else 'Nenhuma'}")
                        created = rec.get("created_at", "")
                        st.markdown(f"**Data:** {created[:10] if created else 'Data desconhecida'}")

                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            if st.button(f"👍 Like", key=f"like_{rec.get('id')}"):
                                if like_recommendation(rec.get('id')):
                                    st.success("Interação registrada!")
                                    time.sleep(0.5)
                                    rerun()
                        with col2:
                            if st.button(f"👎 Dislike", key=f"dislike_{rec.get('id')}"):
                                if dislike_recommendation(rec.get('id')):
                                    st.success("Interação registrada!")
                                    time.sleep(0.5)
                                    rerun()
                        with col3:
                            if st.button("📋 Ver detalhes", key=f"details_{rec.get('id')}"):
                                st.session_state.selected_recommendation = rec.get('id')
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
                        st.markdown(f"### {group.get('name', 'Sem nome')}")
                        st.markdown(f"{group.get('description', 'Sem descrição')}")
                        categories = group.get('categories', [])
                        st.markdown(f"**Categorias:** {', '.join(categories[:3])}")

                    with col2:
                        st.markdown(f"**Criado por:** {group.get('created_by', 'Desconhecido')}")
                        st.markdown(f"**Membros:** {len(group.get('members', []))}")
                        st.markdown(f"**Recomendações:** {len(get_group_recommendations(group.get('id')))}")

                    with col3:
                        if st.session_state.current_group == group.get("id"):
                            st.success("✅ Atual")
                        else:
                            if st.button("Entrar", key=f"enter_{group.get('id')}"):
                                st.session_state.current_group = group.get("id")
                                save_user_preferred_group(st.session_state.username, group.get("id"))
                                st.success(f"Entrou no grupo!")
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
        public_groups = [g for g in groups if g.get("is_public", True) and
                        st.session_state.username not in g.get("members", [])]

        if public_groups:
            st.subheader(f"🔍 {len(public_groups)} Grupos Públicos")

            for group in public_groups:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        st.markdown(f"### {group.get('name', 'Sem nome')}")
                        st.markdown(f"{group.get('description', 'Sem descrição')}")
                        categories = group.get('categories', [])
                        st.markdown(f"**Categorias:** {', '.join(categories[:3])}")

                    with col2:
                        st.markdown(f"**Criado por:** {group.get('created_by', 'Desconhecido')}")
                        st.markdown(f"**Membros:** {len(group.get('members', []))}")

                    with col3:
                        if st.button("Participar", key=f"join_{group.get('id')}"):
                            success, message = join_group(group.get("id"))
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

            default_categories = ["Filmes", "Séries", "Livros", "Produtos de Beleza",
                                "Restaurantes", "Música", "Jogos", "Tecnologia"]
            categories = st.multiselect(
                "Categorias disponíveis no grupo*",
                default_categories,
                default=["Filmes", "Séries"]
            )

            is_public = st.checkbox("Grupo público", value=True)

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
                if st.button(f"📁 {group.get('name', 'Sem nome')}", key=f"select_for_rec_{group.get('id')}"):
                    st.session_state.current_group = group.get("id")
                    save_user_preferred_group(st.session_state.username, group.get("id"))
                    rerun()
        else:
            st.info("Você não está em nenhum grupo ainda")
            if st.button("👥 Ir para Grupos"):
                st.session_state.page = "groups"
                rerun()

        return

    # Se tem grupo selecionado
    groups = load_data("groups.json", [])
    current_group = next((g for g in groups if g.get("id") == st.session_state.current_group), None)

    if current_group:
        with st.form("recommendation_form"):
            st.markdown(f"**Grupo atual:** {current_group.get('name', 'Sem nome')}")

            title = st.text_input("Título da Indicação*")
            description = st.text_area("Descrição detalhada*", height=150)

            # Usar categorias do grupo
            categories = current_group.get("categories", [])
            if not categories:
                categories = ["Geral"]
            category = st.selectbox("Categoria*", categories)

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
            total_likes = sum(r.get("likes", 0) for r in recommendations)
            total_dislikes = sum(r.get("dislikes", 0) for r in recommendations)
            st.metric("Saldo Likes", f"{total_likes - total_dislikes}")
        with col2:
            avg_rating = sum(r.get("rating", 0) for r in recommendations) / len(recommendations)
            st.metric("Média Avaliação", f"{avg_rating:.1f}/5")
        with col3:
            categories = len(set(r.get("category", "") for r in recommendations if r.get("category")))
            st.metric("Categorias", categories)
        with col4:
            groups = len(set(r.get("group_id") for r in recommendations if r.get("group_id")))
            st.metric("Grupos", groups)

        st.markdown("---")

        # Lista de recomendações
        for rec in sorted(recommendations, key=lambda x: x.get("created_at", ""), reverse=True):
            groups = load_data("groups.json", [])
            group_name = next((g.get("name", "Grupo Desconhecido") for g in groups if g.get("id") == rec.get("group_id")), "Grupo Desconhecido")

            likes = rec.get("likes", 0)
            dislikes = rec.get("dislikes", 0)

            with st.expander(f"{rec.get('title', 'Sem título')} | ⭐ {rec.get('rating', 0)}/5 | 👍 {likes} | 👎 {dislikes} | 📁 {group_name}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Categoria:** {rec.get('category', 'Sem categoria')}")
                    st.markdown(f"**Descrição:** {rec.get('description', 'Sem descrição')}")
                    tags = rec.get("tags", [])
                    st.markdown(f"**Tags:** {', '.join(tags) if tags else 'Nenhuma'}")
                with col2:
                    st.markdown(f"**Grupo:** {group_name}")
                    created = rec.get("created_at", "")
                    st.markdown(f"**Data:** {created[:10] if created else 'Data desconhecida'}")
                    st.markdown(f"**Likes:** {likes}")
                    st.markdown(f"**Dislikes:** {dislikes}")

                    # Botão para ir para o grupo
                    if st.button("Ir para grupo", key=f"goto_{rec.get('id')}"):
                        st.session_state.current_group = rec.get("group_id")
                        save_user_preferred_group(st.session_state.username, rec.get("group_id"))
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

# ==================== PÁGINA PRINCIPAL DO APLICATIVO ====================

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
                (g for g in user_groups if g.get("id") == st.session_state.current_group),
                None
            )

        # Lista de grupos para seleção
        group_names = [g.get("name", "Sem nome") for g in user_groups]

        # Índice do grupo atual na lista
        current_index = 0
        if current_group_info:
            try:
                current_index = group_names.index(current_group_info.get("name", "Sem nome"))
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
            selected_group = next(g for g in user_groups if g.get("name") == selected_group_name)
            if selected_group.get("id") != st.session_state.current_group:
                st.session_state.current_group = selected_group.get("id")
                save_user_preferred_group(st.session_state.username, selected_group.get("id"))
                st.sidebar.success(f"Grupo '{selected_group_name}' selecionado!")
                time.sleep(0.5)
                rerun()

        # Mostra informações do grupo atual
        if current_group_info:
            st.sidebar.markdown(f"**Grupo:** {current_group_info.get('name', 'Sem nome')}")
            st.sidebar.markdown(f"**Membros:** {len(current_group_info.get('members', []))}")
            categories = current_group_info.get('categories', [])
            st.sidebar.markdown(f"**Categorias:** {', '.join(categories[:2])}")

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

# ========== NOVO: BOTÃO DE ATUALIZAR ==========
    st.sidebar.markdown("---")

    # Botão principal de atualização
    if st.sidebar.button("🔄 Atualizar Página",
                        use_container_width=True,
                        type="secondary",  # Ou "primary" para destacar mais
                        help="Recarrega a página mantendo seu login"):
        rerun()

    # Informação útil
    st.sidebar.caption("Pressione F5 no navegador para atualizar")

# ==================== PONTO DE ENTRADA DA APLICAÇÃO ====================

def main():
    if st.session_state.authenticated:
        main_app()
    else:
        login_page()

if __name__ == "__main__":
    # Verifica se há dados antigos para migrar
    import os
    if os.path.exists("data/users.json") or os.path.exists("data/groups.json"):
        print("🔄 Migrando dados antigos para SQLite...")

    main()
