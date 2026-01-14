import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats
import requests
from io import StringIO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Oráculo Master Pro",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO ---
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: 800; color: #0f172a; text-align: center; margin-bottom: 1rem;}
    .sub-header {font-size: 1.2rem; color: #64748b; text-align: center; margin-bottom: 2rem;}
    .card {background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;}
    .metric-value {font-size: 1.8rem; font-weight: 700; color: #0f172a;}
    .metric-label {font-size: 0.9rem; color: #64748b; text-transform: uppercase;}
    .ball {
        display: inline-block; width: 40px; height: 40px; line-height: 40px; 
        text-align: center; border-radius: 50%; color: white; font-weight: bold;
        margin: 3px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE CARREGAMENTO ---
@st.cache_data(ttl=3600) # Cache de 1 hora para não ficar baixando toda hora
def load_data_from_github(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        # Lê o CSV ignorando linhas problemáticas se houver
        df = pd.read_csv(StringIO(response.text))
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

def detect_config(df):
    """Detecta automaticamente qual é a loteria baseada nas colunas"""
    cols = df.columns
    # Filtra colunas que parecem ser dezenas (D1, Bola1, etc)
    ball_cols = [c for c in cols if any(x in c.lower() for x in ['d', 'bola', 'dezen']) and not any(x in c.lower() for x in ['data', 'concurso', 'ganhador'])]
    
    # Se não achar pelo nome, tenta pegar colunas numéricas
    if not ball_cols:
        ball_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Remove colunas óbvias que não são bolas
        ball_cols = [c for c in ball_cols if 'concurso' not in c.lower()]

    if not ball_cols:
        return None, None, None

    max_val = df[ball_cols].max().max()
    n_cols = len(ball_cols)
    
    name = "Desconhecida"
    max_num = int(max_val)
    draw_size = n_cols

    # Regras de Negócio
    if n_cols >= 15: name, max_num = "Lotofácil", 25
    elif n_cols == 5: name, max_num = "Quina", 80
    elif n_cols == 6:
        if max_val > 50: name, max_num = "Mega Sena", 60
        else: name, max_num = "Dupla Sena", 50
    elif n_cols == 7:
        if max_val > 31: name, max_num = "Timemania", 80
        else: name, max_num = "Dia de Sorte", 31
    elif n_cols >= 20: name, max_num = "Lotomania", 100
    
    # Ajuste para Dupla Sena (se o CSV tiver 12 colunas, usamos 6 para gerar jogos)
    gen_size = 6 if n_cols == 12 else (50 if n_cols >= 20 else n_cols) # Lotomania gera 50

    return df[ball_cols], name, {"max": max_num, "size": gen_size}

# --- FUNÇÕES MATEMÁTICAS ---
def analyze_stats(df_balls, config):
    # Frequência
    all_numbers = df_balls.values.flatten()
    all_numbers = all_numbers[~np.isnan(all_numbers)] # Remove vazios
    counts = pd.Series(all_numbers).value_counts().sort_index()
    
    # Reindexa para garantir que todos os números (1 ao max) apareçam, mesmo com contagem 0
    full_index = range(1, config['max'] + 1)
    counts = counts.reindex(full_index, fill_value=0)
    
    # Hot & Cold
    sorted_nums = counts.sort_values(ascending=False)
    hot = sorted_nums.index[:config['max']//3].tolist()
    cold = sorted_nums.index[-config['max']//3:].tolist()
    
    # Par/Ímpar
    even = counts[counts.index % 2 == 0].sum()
    odd = counts[counts.index % 2 != 0].sum()
    
    return {"counts": counts, "hot": hot, "cold": cold, "even_pct": even/(even+odd)}

def generate_games(stats_data, config, n_games=1):
    games = []
    
    # Estratégia 1: Equilíbrio (Mistura Frios com Neutros)
    pool_eq = stats_data['cold'] + list(set(range(1, config['max']+1)) - set(stats_data['hot']) - set(stats_data['cold']))
    
    # Estratégia 2: Tendência (Quentes)
    pool_tr = stats_data['hot']
    
    for _ in range(n_games):
        # Gerar Equilíbrio
        g_eq = np.random.choice(pool_eq, config['size'], replace=False)
        g_eq.sort()
        
        # Gerar Tendência (com fallback se não tiver números quentes suficientes)
        use_pool_tr = pool_tr if len(pool_tr) >= config['size'] else list(range(1, config['max']+1))
        g_tr = np.random.choice(use_pool_tr, config['size'], replace=False)
        g_tr.sort()
        
        # Gerar Mestre (Híbrido)
        # Pega metade dos quentes e metade aleatório/frio
        n_hot = config['size'] // 2
        n_rest = config['size'] - n_hot
        
        # Garante que pools são válidos
        valid_hot = [x for x in stats_data['hot'] if x <= config['max']]
        valid_cold = [x for x in stats_data['cold'] if x <= config['max']]
        
        if len(valid_hot) < n_hot: valid_hot = range(1, config['max']+1)
        if len(valid_cold) < n_rest: valid_cold = range(1, config['max']+1)

        p1 = np.random.choice(valid_hot, n_hot, replace=False)
        # Remove do pool frio o que já saiu no quente para não duplicar
        pool_cold_clean = list(set(valid_cold) - set(p1))
        if len(pool_cold_clean) < n_rest: pool_cold_clean = list(set(range(1, config['max']+1)) - set(p1))
            
        p2 = np.random.choice(pool_cold_clean, n_rest, replace=False)
        g_ma = np.concatenate((p1, p2))
        g_ma.sort()
        
        games.append({"Equilíbrio": g_eq, "Tendência": g_tr, "Mestre": g_ma})
        
    return games

# --- INTERFACE PRINCIPAL ---

st.markdown('<div class="main-header">🔮 ORÁCULO MASTER</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Inteligência Artificial para Loterias</div>', unsafe_allow_html=True)

# 1. SIDEBAR - SELEÇÃO DE ARQUIVOS
st.sidebar.header("📁 Base de Dados")
st.sidebar.info("Os dados são carregados diretamente do seu repositório GitHub.")

# Mapeamento dos seus arquivos (VOCÊ VAI SUBSTITUIR PELS SEUS LINKS RAW DO GITHUB AQUI)
# Exemplo: https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/Oraculo_DB_Master%20-%20Mega_Sena.csv
files = {
    "Mega Sena": "LINK_RAW_DA_MEGA_SENA_AQUI", 
    "Lotofácil": "LINK_RAW_DA_LOTOFACIL_AQUI",
    "Quina": "LINK_RAW_DA_QUINA_AQUI",
    "Lotomania": "LINK_RAW_DA_LOTOMANIA_AQUI",
    "Timemania": "LINK_RAW_DA_TIMEMANIA_AQUI",
    "Dia de Sorte": "LINK_RAW_DO_DIA_DE_SORTE_AQUI",
    "Dupla Sena": "LINK_RAW_DA_DUPLA_SENA_AQUI"
}

# Opção de Upload manual caso o GitHub falhe ou para teste local
source_option = st.sidebar.radio("Fonte dos Dados:", ["GitHub (Automático)", "Upload Manual (CSV)"])

df = None
selected_lottery = None

if source_option == "GitHub (Automático)":
    selected_lottery = st.sidebar.selectbox("Selecione a Loteria:", list(files.keys()))
    url = files[selected_lottery]
    if url != "LINK_RAW_DA_MEGA_SENA_AQUI": # Só carrega se o link for real
        with st.spinner('Baixando base atualizada...'):
            df = load_data_from_github(url)
    else:
        st.sidebar.warning("⚠️ Configure os links no código!")

else:
    uploaded_file = st.sidebar.file_uploader("Arraste seu arquivo CSV aqui", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)

# 2. PROCESSAMENTO E EXIBIÇÃO
if df is not None:
    # Detecta configuração
    df_balls, detected_name, config = detect_config(df)
    
    if df_balls is not None:
        if source_option == "Upload Manual (CSV)": 
            selected_lottery = detected_name
            
        st.success(f"✅ Base carregada: **{selected_lottery}** | {len(df)} Concursos | {config['size']} Dezenas")
        
        # Análises
        stats_data = analyze_stats(df_balls, config)
        
        # --- DASHBOARD ---
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="card">
                <div class="metric-label">Paridade (Ímpar / Par)</div>
                <div class="metric-value">{1-stats_data['even_pct']:.0%} / {stats_data['even_pct']:.0%}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            top_hot = stats_data['hot'][:3]
            st.markdown(f"""
            <div class="card">
                <div class="metric-label">Top 3 Quentes 🔥</div>
                <div class="metric-value">{', '.join(map(str, top_hot))}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            top_cold = stats_data['cold'][:3]
            st.markdown(f"""
            <div class="card">
                <div class="metric-label">Top 3 Atrasados ❄️</div>
                <div class="metric-value">{', '.join(map(str, top_cold))}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # --- ORÁCULO GERADOR ---
        st.subheader("🎲 Gerador de Palpites Otimizados")
        
        if st.button("GERAR COMBINAÇÕES", type="primary"):
            predictions = generate_games(stats_data, config)
            pred = predictions[0] # Pega o primeiro set
            
            c1, c2, c3 = st.columns(3)
            
            def render_balls_html(numbers, color):
                html = ""
                for n in numbers:
                    html += f'<span class="ball" style="background-color: {color}">{n}</span>'
                return html

            with c1:
                st.markdown("### ⚖️ Equilíbrio")
                st.caption("Mistura inteligente de frios e neutros.")
                st.markdown(render_balls_html(pred['Equilíbrio'], "#0ea5e9"), unsafe_allow_html=True)
                
            with c2:
                st.markdown("### 🔥 Tendência")
                st.caption("Segue os números mais frequentes.")
                st.markdown(render_balls_html(pred['Tendência'], "#f59e0b"), unsafe_allow_html=True)
                
            with c3:
                st.markdown("### 🔮 Mestre")
                st.caption("A melhor aposta híbrida.")
                st.markdown(render_balls_html(pred['Mestre'], "#10b981"), unsafe_allow_html=True)

        # --- GRÁFICOS ---
        st.markdown("---")
        st.subheader("📊 Raio-X Estatístico")
        
        tab1, tab2 = st.tabs(["Frequência das Dezenas", "Tabela de Dados"])
        
        with tab1:
            chart_data = pd.DataFrame({
                'Dezena': stats_data['counts'].index,
                'Frequência': stats_data['counts'].values
            })
            st.bar_chart(chart_data, x='Dezena', y='Frequência')
            
        with tab2:
            st.dataframe(df, use_container_width=True)

    else:
        st.error("Não foi possível identificar colunas de dezenas (D1, D2...) neste arquivo.")
else:
    st.info("👈 Selecione uma loteria no menu lateral ou faça upload de um arquivo para começar.")
