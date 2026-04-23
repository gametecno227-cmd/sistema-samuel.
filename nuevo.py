import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests

# 1. CONFIGURACIÓN CENTRAL
st.set_page_config(page_title="Resto Samuel - Unificado", layout="wide")

# ESTO UNIFICA LOS DATOS PARA TODOS LOS QUE ENTREN AL LINK
if 'mesas' not in st.session_state:
    st.session_state.mesas = {i: [] for i in range(1, 51)}
if 'historial' not in st.session_state:
    st.session_state.historial = []

# 2. CONEXIÓN AL EXCEL
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR683Ef1FFMFjMj0NqgygAm6d3siwKrKUtlmG_Xd3n_qv8zO56a2PnG6lBr66sMYxkJ2LOZfTZqoien/pub?output=csv"

@st.cache_data(ttl=1) # Sincronización rápida con el Excel
def cargar_menu():
    try:
        response = requests.get(SHEET_URL, timeout=10)
        response.encoding = 'utf-8'
        df = pd.read_csv(io.StringIO(response.text))
        df.columns = [str(c).strip().lower() for c in df.columns]
        return {str(row['producto']).strip(): float(str(row['precio']).replace('$','').replace(',','')) for _, row in df.iterrows()}
    except: return None

menu = cargar_menu()

# 3. INTERFAZ UNIFICADA
st.sidebar.title("🏨 SISTEMA CENTRAL")
modo = st.sidebar.radio("Ir a:", ["📍 MOZOS", "💰 CAJA", "📊 CIERRE Z"])

if modo == "📍 MOZOS":
    st.header("📍 Registro de Pedidos")
    # Mesas en orden 1, 2, 3...
    cols = st.columns(5)
    for i in range(1, 51):
        with cols[(i-1)%5]:
            estado = "🔴" if st.session_state.mesas[i] else "🟢"
            if st.button(f"{estado} M{i}", key=f"m{i}", use_container_width=True):
                st.session_state.m_act = i
    
    if 'm_act' in st.session_state:
        m = st.session_state.m_act
        st.subheader(f"Mesa {m}")
        if menu:
            p_sel = st.selectbox("Producto:", list(menu.keys()), key=f"p_{m}")
            cant = st.number_input("Cant:", min_value=1, value=1, key=f"c_{m}")
            if st.button("➕ AGREGAR"):
                st.session_state.mesas[m].append({"Prod": p_sel, "Cant": cant, "Precio": menu[p_sel], "Sub": menu[p_sel]*cant})
                st.rerun() # Actualiza para que la cajera lo vea YA

elif modo == "💰 CAJA":
    st.header("💰 Cobros en Tiempo Real")
    activas = [i for i, v in st.session_state.mesas.items() if v]
    if activas:
        m_c = st.selectbox("Mesa a cobrar:", activas)
        df_c = pd.DataFrame(st.session_state.mesas[m_c])
        st.table(df_c)
        total = df_c["Sub"].sum()
        st.write(f"## TOTAL: ${total:,.2f}")
        if st.button(f"✅ FINALIZAR MESA {m_c}"):
            st.session_state.historial.append({"Mesa": m_c, "Total": total, "Fecha": datetime.now().strftime("%H:%M")})
            st.session_state.mesas[m_c] = []
            st.rerun()

elif modo == "📊 CIERRE Z":
    st.header("📊 Cierre Diario")
    if st.session_state.historial:
        df_z = pd.DataFrame(st.session_state.historial)
        st.metric("RECAUDACIÓN TOTAL", f"${df_z['Total'].sum():,.2f}")
        st.dataframe(df_z)
        if st.button("🖨️ IMPRIMIR"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
