import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Resto Samuel - Sistema en Red", layout="wide")

# 2. BASE DE DATOS GLOBAL (Esto hace que todos vean lo mismo)
if 'mesas' not in st.session_state:
    st.session_state.mesas = {i: [] for i in range(1, 51)}
if 'historial' not in st.session_state:
    st.session_state.historial = []

# 3. CONEXIÓN AL EXCEL
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR683Ef1FFMFjMj0NqgygAm6d3siwKrKUtlmG_Xd3n_qv8zO56a2PnG6lBr66sMYxkJ2LOZfTZqoien/pub?output=csv"

@st.cache_data(ttl=1) # Actualiza el menú casi instantáneamente
def cargar_menu():
    try:
        response = requests.get(SHEET_URL, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            df.columns = [str(c).strip().lower() for c in df.columns]
            def limpiar_p(v):
                if isinstance(v, str):
                    v = v.replace('$', '').replace(',', '').strip()
                return float(v)
            return {str(row['producto']).strip(): limpiar_p(row['precio']) for _, row in df.iterrows()}
        return None
    except:
        return None

menu = cargar_menu()

# --- INTERFAZ ---
st.sidebar.title("🏨 Panel de Control")
modo = st.sidebar.radio("Ir a:", ["📍 Mozo", "💰 Caja", "📊 Cierre Z"])

if modo == "📍 Mozo":
    st.header("📍 Panel de Mesas (Sincronizado)")
    lista_mesas = sorted(st.session_state.mesas.keys())
    cols = st.columns(5)
    for i in lista_mesas:
        with cols[(i-1)%5]:
            estado = "🔴" if st.session_state.mesas[i] else "🟢"
            if st.button(f"{estado} M{i}", key=f"m{i}", use_container_width=True):
                st.session_state.m_act = i
    
    if 'm_act' in st.session_state:
        m = st.session_state.m_act
        st.divider()
        st.subheader(f"Mesa {m}")
        if menu:
            p_sel = st.selectbox("Producto:", list(menu.keys()), key=f"sel_{m}")
            cant = st.number_input("Cant:", min_value=1, value=1, key=f"c_{m}")
            if st.button("➕ AGREGAR PEDIDO", use_container_width=True):
                st.session_state.mesas[m].append({
                    "Prod": p_sel, "Cant": cant, "Precio": menu[p_sel], "Sub": menu[p_sel]*cant
                })
                st.rerun() # Esto avisa a los demás dispositivos del cambio
            
            if st.session_state.mesas[m]:
                st.table(pd.DataFrame(st.session_state.mesas[m])[['Cant', 'Prod']])

elif modo == "💰 Caja":
    st.header("💰 Caja Central")
    activas = sorted([i for i, v in st.session_state.mesas.items() if v])
    if activas:
        m_c = st.selectbox("Cobrar Mesa:", activas)
        df_c = pd.DataFrame(st.session_state.mesas[m_c])
        st.table(df_c)
        total = df_c["Sub"].sum()
        st.write(f"## TOTAL: ${total:,.2f}")
        
        if st.button(f"✅ FINALIZAR COBRO MESA {m_c}", use_container_width=True):
            st.session_state.historial.append({"Mesa": m_c, "Total": total, "Fecha": datetime.now().strftime("%H:%M")})
            st.session_state.mesas[m_c] = []
            st.rerun()
    else:
        st.info("Esperando pedidos de las mozas...")

elif modo == "📊 Cierre Z":
    st.header("📊 Resumen del Día")
    if st.session_state.historial:
        df_z = pd.DataFrame(st.session_state.historial)
        st.metric("TOTAL", f"${df_z['Total'].sum():,.2f}")
        st.dataframe(df_z)
