import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

API = "http://localhost:8000"

st.set_page_config(
    page_title="Football Analytics",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
<style>
    .metric-card {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ── Helpers ──────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_ligas():
    r = requests.get(f"{API}/ligas")
    return r.json()

@st.cache_data(ttl=300)
def get_classificacao(code):
    r = requests.get(f"{API}/ligas/{code}/classificacao")
    return r.json()

@st.cache_data(ttl=300)
def get_partidas_recentes(liga=None, limit=30):
    params = {"limit": limit}
    if liga:
        params["liga"] = liga
    r = requests.get(f"{API}/partidas/recentes", params=params)
    return r.json()

@st.cache_data(ttl=300)
def get_times():
    r = requests.get(f"{API}/times")
    return r.json()

@st.cache_data(ttl=300)
def get_historico_time(team_id, limit=10):
    r = requests.get(f"{API}/times/{team_id}/historico", params={"limit": limit})
    return r.json()

# ── Sidebar ───────────────────────────────────────────────

with st.sidebar:
    st.title("⚽ Football Analytics")
    st.markdown("---")
    pagina = st.radio(
        "Navegação",
        ["🏠 Visão Geral", "🏆 Classificação", "📅 Partidas", "📊 Time"]
    )
    st.markdown("---")
    if st.button("🔄 Atualizar dados"):
        st.cache_data.clear()
        st.rerun()

ligas = get_ligas()
liga_map = {l["name"]: l["code"] for l in ligas}

# ══════════════════════════════════════════════════════════
# PÁGINA: VISÃO GERAL
# ══════════════════════════════════════════════════════════

if pagina == "🏠 Visão Geral":
    st.title("🏠 Visão Geral")

    partidas = get_partidas_recentes(limit=50)
    df = pd.DataFrame(partidas)

    if not df.empty:
        df["match_date"] = pd.to_datetime(df["match_date"])
        df_fin = df[df["status"] == "FINISHED"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de partidas", len(df))
        col2.metric("Finalizadas", len(df_fin))
        col3.metric("Ligas cobertas", len(ligas))
        col4.metric("Times cadastrados", len(get_times()))

        st.markdown("---")

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Partidas por liga")
            contagem = df["competition_code"].value_counts().reset_index()
            contagem.columns = ["Liga", "Partidas"]
            fig = px.bar(contagem, x="Liga", y="Partidas",
                         color="Liga", color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.subheader("Gols nas últimas partidas")
            df_fin["total_gols"] = df_fin["home_score"] + df_fin["away_score"]
            media = df_fin.groupby("competition_code")["total_gols"].mean().reset_index()
            media.columns = ["Liga", "Média de gols"]
            media["Média de gols"] = media["Média de gols"].round(2)
            fig2 = px.bar(media, x="Liga", y="Média de gols",
                          color="Liga", color_discrete_sequence=px.colors.qualitative.Set2)
            fig2.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.subheader("Últimas partidas finalizadas")
        df_show = df_fin[["match_date","competition_code","home_team","home_score","away_score","away_team"]].head(10).copy()
        df_show["match_date"] = df_show["match_date"].dt.strftime("%d/%m %H:%M")
        df_show.columns = ["Data","Liga","Mandante","Gols M","Gols V","Visitante"]
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════
# PÁGINA: CLASSIFICAÇÃO
# ══════════════════════════════════════════════════════════

elif pagina == "🏆 Classificação":
    st.title("🏆 Classificação")

    liga_nome = st.selectbox("Selecione a liga", list(liga_map.keys()))
    liga_code = liga_map[liga_nome]

    dados = get_classificacao(liga_code)
    df = pd.DataFrame(dados)

    if not df.empty:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"Tabela — {liga_nome}")
            df_show = df[["position","team","played","won","draw","lost",
                          "goals_for","goals_against","goal_diff","points"]].copy()
            df_show.columns = ["Pos","Time","J","V","E","D","GP","GC","SG","Pts"]

            def highlight_positions(row):
                if row["Pos"] <= 4:
                    return ["background-color: #d4edda; color: #155724"] * len(row)
                elif row["Pos"] <= 6:
                    return ["background-color: #cce5ff; color: #004085"] * len(row)
                elif row["Pos"] >= 18:
                    return ["background-color: #f8d7da; color: #721c24"] * len(row)
                return [""] * len(row)

            st.dataframe(
                df_show.style.apply(highlight_positions, axis=1),
                use_container_width=True,
                hide_index=True,
                height=600
            )

        with col2:
            st.subheader("Top 8 por pontos")
            fig = px.bar(
                df.head(8),
                x="points", y="team",
                orientation="h",
                color="points",
                color_continuous_scale="Blues"
            )
            fig.update_layout(height=400, showlegend=False,
                              yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Gols pró vs contra")
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name="Gols Pró", x=df.head(8)["team"],
                                  y=df.head(8)["goals_for"], marker_color="#2ecc71"))
            fig2.add_trace(go.Bar(name="Gols Contra", x=df.head(8)["team"],
                                  y=df.head(8)["goals_against"], marker_color="#e74c3c"))
            fig2.update_layout(barmode="group", height=350,
                               xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════
# PÁGINA: PARTIDAS
# ══════════════════════════════════════════════════════════

elif pagina == "📅 Partidas":
    st.title("📅 Partidas Recentes")

    col1, col2 = st.columns(2)
    with col1:
        liga_filtro = st.selectbox("Liga", ["Todas"] + list(liga_map.keys()))
    with col2:
        limit = st.slider("Quantidade", 10, 50, 20)

    liga_code = liga_map.get(liga_filtro) if liga_filtro != "Todas" else None
    partidas = get_partidas_recentes(liga=liga_code, limit=limit)
    df = pd.DataFrame(partidas)

    if not df.empty:
        df["match_date"] = pd.to_datetime(df["match_date"])
        df["data"] = df["match_date"].dt.strftime("%d/%m/%Y")
        df["hora"] = df["match_date"].dt.strftime("%H:%M")
        df["placar"] = df.apply(
            lambda r: f"{r['home_score']} x {r['away_score']}"
            if r["home_score"] is not None else "x", axis=1
        )

        st.markdown(f"**{len(df)} partidas encontradas**")

        for _, row in df.iterrows():
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([1.5, 3, 1.5, 3, 1.5])
                c1.markdown(f"**{row['data']}**  \n{row['hora']}")
                c2.markdown(f"<div style='text-align:right;font-size:1.1em'>{row['home_team']}</div>",
                            unsafe_allow_html=True)
                c3.markdown(f"<div style='text-align:center;font-size:1.3em;font-weight:bold'>{row['placar']}</div>",
                            unsafe_allow_html=True)
                c4.markdown(f"<div style='font-size:1.1em'>{row['away_team']}</div>",
                            unsafe_allow_html=True)
                c5.markdown(f"`{row['competition_code']}`  \n`{row['status']}`")
                st.divider()

# ══════════════════════════════════════════════════════════
# PÁGINA: TIME
# ══════════════════════════════════════════════════════════

elif pagina == "📊 Time":
    st.title("📊 Análise de Time")

    times = get_times()
    time_map = {t["name"]: t["id"] for t in times}

    time_nome = st.selectbox("Selecione o time", sorted(time_map.keys()))
    time_id = time_map[time_nome]

    historico = get_historico_time(team_id=time_id, limit=10)

    if isinstance(historico, list) and historico:
        df = pd.DataFrame(historico)
        df["match_date"] = pd.to_datetime(df["match_date"])
        df = df.sort_values("match_date")

        col1, col2, col3 = st.columns(3)
        vit = len(df[df["resultado"] == "V"])
        emp = len(df[df["resultado"] == "E"])
        der = len(df[df["resultado"] == "D"])
        col1.metric("Vitórias", vit)
        col2.metric("Empates", emp)
        col3.metric("Derrotas", der)

        st.markdown("---")
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Forma recente")
            cores = {"V": "#2ecc71", "E": "#f39c12", "D": "#e74c3c"}
            for _, row in df.iterrows():
                adversario = row["away_team"] if row["home_team"] == time_nome else row["home_team"]
                placar = f"{row['home_score']} x {row['away_score']}"
                cor = cores.get(row["resultado"], "#888")
                data = row["match_date"].strftime("%d/%m")
                st.markdown(
                    f"<div style='padding:6px;margin:4px 0;border-left:4px solid {cor};'>"
                    f"<b>{row['resultado']}</b> — {data} — vs {adversario} ({placar})</div>",
                    unsafe_allow_html=True
                )

        with col_b:
            st.subheader("Gols marcados vs sofridos")
            df["gols_marcados"] = df.apply(
                lambda r: r["home_score"] if r["home_team"] == time_nome else r["away_score"], axis=1
            )
            df["gols_sofridos"] = df.apply(
                lambda r: r["away_score"] if r["home_team"] == time_nome else r["home_score"], axis=1
            )
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["match_date"].dt.strftime("%d/%m"),
                y=df["gols_marcados"], name="Marcados",
                mode="lines+markers", line=dict(color="#2ecc71")
            ))
            fig.add_trace(go.Scatter(
                x=df["match_date"].dt.strftime("%d/%m"),
                y=df["gols_sofridos"], name="Sofridos",
                mode="lines+markers", line=dict(color="#e74c3c")
            ))
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nenhum histórico encontrado para este time.")
