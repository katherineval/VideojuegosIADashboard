import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq
import os


GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Analítica de Videojuegos",
    layout="wide",
    page_icon="🎮"
)

# ============================================================
# MEJORA 2: ESTILOS VISUALES (CSS PERSONALIZADO)
# ============================================================

st.markdown("""
    <style>
        /* Fuente general más limpia */
        html, body, [class*="css"] {
            font-family: 'Segoe UI', sans-serif;
        }

        /* Hace los números de las métricas más grandes y visibles */
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 700 !important;
            color: #7B68EE !important;
        }

        /* Etiquetas de las métricas en gris suave */
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
            color: #888 !important;
        }

        /* Fondo de la barra lateral diferenciado */
        [data-testid="stSidebar"] {
            background-color: #1e1e2e !important;
        }

        /* Texto blanco en la barra lateral para contraste */
        [data-testid="stSidebar"] * {
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    df = pd.read_excel("Ventas Videojuegos.xlsx")
    return df

df = cargar_datos()

# ============================================================
# BARRA LATERAL CON FILTROS
# ============================================================
st.sidebar.header("🕹️ Panel de Filtros")
editoriales = st.sidebar.multiselect(
    "Selecciona Editorial:",
    options=df["Editorial"].unique(),
    default=df["Editorial"].unique()[:5]
)

# ============================================================
#  MANEJO DE FILTRO VACÍO
# ============================================================


if not editoriales:
    st.warning("⚠️ Selecciona al menos una editorial en el panel izquierdo.")
    st.stop()

df_filtrado = df[df["Editorial"].isin(editoriales)]

# ============================================================
# TÍTULO PRINCIPAL
# ============================================================
st.title("🎮 Dashboard de Videojuegos Inteligente")
st.markdown("---")

# ============================================================
# KPI ADICIONAL — EDITORIAL LÍDER
# ============================================================


col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.metric("Ventas Globales Totales", f"{df_filtrado['Ventas Global'].sum():.2f}M")

with col_kpi2:
    st.metric("Género más Frecuente", df_filtrado['Genero'].mode()[0])

with col_kpi3:
    st.metric("Juegos Filtrados", len(df_filtrado))

with col_kpi4:
    # ============================================================
    #  MÉTRICA — EDITORIAL LÍDER EN VENTAS
    # ============================================================
    
    editorial_lider = df_filtrado.groupby("Editorial")["Ventas Global"].sum().idxmax()
    st.metric("Editorial Líder", editorial_lider)

st.markdown("---")

# ============================================================
# DISEÑO EN DOS COLUMNAS: GRÁFICO + IA
# ============================================================
col_grafica, col_ia = st.columns([1.5, 1])

with col_grafica:
    st.subheader("📊 Visualización de Ventas")

    # ============================================================
    # ORDENAR ANTES DE GRAFICAR
    # ============================================================

    top15 = (
        df_filtrado
        .sort_values("Ventas Global", ascending=False)
        .head(15)
    )

    # ============================================================
    # PALETA DE COLOR MÁS LEGIBLE
    # ============================================================

    fig = px.bar(
        top15,
        x="Ventas Global",
        y="Nombre",
        color="Ventas Global",
        orientation='h',
        title="Top 15 Juegos por Ventas Globales",
        color_continuous_scale='Blues',
        hover_name="Nombre",          # Muestra el nombre al pasar el mouse
        hover_data={"Ventas Global": ":.2f"}  # Formato limpio en el tooltip
    )

    # ============================================================
    #  TIPOGRAFÍA DEL GRÁFICO 
    # ============================================================

    fig.update_layout(
        yaxis={
            'categoryorder': 'total ascending',
            'tickfont': {'size': 12}   # Nombres de juegos más grandes
        },
        xaxis={
            'tickfont': {'size': 11}
        },
        margin=dict(l=160),            # Espacio para nombres largos
        coloraxis_showscale=False,     # Oculta la barra de color (es redundante)
        title_font_size=15
    )

    st.plotly_chart(fig, use_container_width=True)

with col_ia:
    st.subheader("🤖 Pregúntale a la IA")

    with st.container(border=True):
        pregunta = st.text_input(
            "Haz una pregunta:",
            placeholder="Ej: ¿Qué género ha mostrado un crecimiento más constante?"
        )

        if pregunta:
            if not GROQ_API_KEY:
                st.error("⚠️ No se encontró la API Key de Groq. Configúrala en st.secrets o como variable de entorno.")
            else:
                with st.spinner("Analizando datos..."):

                    ventas_por_genero = (
                        df_filtrado
                        .groupby("Genero")["Ventas Global"]
                        .sum()
                        .sort_values(ascending=False)
                        .to_string()
                    )

                    ventas_por_anio = (
                        df_filtrado
                        .groupby("Año")["Ventas Global"]
                        .sum()
                        .sort_values()
                        .to_string()
                    )

                    top3_juegos = (
                        df_filtrado
                        .sort_values("Ventas Global", ascending=False)
                        .head(3)["Nombre"]
                        .tolist()
                    )

                    stats_globales = {
                        "total_ventas":      df_filtrado["Ventas Global"].sum(),
                        "ventas_na":         df_filtrado["Ventas NA"].sum(),
                        "ventas_eu":         df_filtrado["Ventas EU"].sum(),
                        "ventas_jp":         df_filtrado["Ventas JP"].sum(),
                        "promedio_ventas":   df_filtrado["Ventas Global"].mean(),
                        "juego_mas_vendido": df_filtrado.loc[df_filtrado["Ventas Global"].idxmax(), "Nombre"],
                        "top3_juegos":       ", ".join(top3_juegos),
                        "genero_lider":      df_filtrado["Genero"].mode()[0] if not df_filtrado["Genero"].mode().empty else "N/A",
                        "total_juegos":      len(df_filtrado)
                    }

                    client = Groq(api_key=GROQ_API_KEY)

                    prompt = f"""
Eres un Consultor Senior de Datos especializado en la industria del videojuego.
Analiza estos datos del dataset filtrado:

- Ventas Totales Globales: {stats_globales['total_ventas']:.2f}M
- Ventas en Norteamérica: {stats_globales['ventas_na']:.2f}M
- Ventas en Europa: {stats_globales['ventas_eu']:.2f}M
- Ventas en Japón: {stats_globales['ventas_jp']:.2f}M
- Promedio de ventas por juego: {stats_globales['promedio_ventas']:.2f}M
- Juego número 1: {stats_globales['juego_mas_vendido']}
- Top 3 juegos: {stats_globales['top3_juegos']}
- Género más frecuente: {stats_globales['genero_lider']}
- Total de juegos analizados: {stats_globales['total_juegos']}

### Ventas por género:
{ventas_por_genero}

### Evolución de ventas por año:
{ventas_por_anio}

Pregunta del usuario: {pregunta}

Responde de forma concisa y profesional. Usa emojis con moderación.
Si la pregunta no puede responderse con los datos disponibles, indícalo amablemente.
"""

                    try:
                        completion = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        respuesta = completion.choices[0].message.content
                        st.success(respuesta)

                    except Exception as e:
                        st.error(f"No se pudo conectar con la IA. Verifica tu conexión o API Key.\nDetalle: {e}")
                        