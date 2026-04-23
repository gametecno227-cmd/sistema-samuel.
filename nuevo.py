import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests

# 1. CONFIGURACIÓN DEL SISTEMA
st.set_page_config(page_title="Resto Samuel - Sistema Unificado", layout="wide")

# --- EL CEREBRO CENTRAL (Sincroniza Celulares y PC) ---
@st.cache_resource
def obtener_base_datos():
    # Esta función crea un diccionario que comparten todos los usuarios
    return {
        "mesas": {i: [] for i in range(1, 51)},
        "historial": []
    }

db = obtener_base_datos()

# Pasamos los datos al estado de la sesión actual
if 'mesas' not in st.session_state:
    st.session_state.mesas = db["mesas"]
if 'historial' not in st.session_state:
    st.session_state.historial = db["historial"]

# 2. CONEXIÓN AL EXCEL
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR683Ef1FFMFjMj0NqgygAm6d3siwKrKUtlmG_Xd3n_qv8zO56a2PnG6lBr66sMYxkJ2LOZfTZqoien/pub?output=csv"

@st.cache_data(ttl=1)
def cargar_menu():
    try:
        response = requests.get(SHEET_URL, timeout=10)
        response.encoding = 'utf-8'
        df = pd.read_csv(io.StringIO(response.text))
        df.columns = [str(c).strip().lower() for c in df.columns]
        def limpiar_p(v):
            if isinstance(v, str):
                v = v.replace('$', '').replace(',', '').strip()
            return float(v)
        return {str(row['producto']).strip(): limpiar_p(row['precio']) for _, row in df.iterrows()}
    except: return None

menu = cargar_menu()

# 3. INTERFAZ
st.sidebar.title("🏨 RESTO SAMUEL")
modo = st.sidebar.radio("Ir a:", ["📍 MOZOS (Pedidos)", "💰 CAJA (Cobros)", "📊 CIERRE Z"])

# --- VISTA MOZOS ---
if modo == "📍 MOZOS (Pedidos)":
    st.header("📍 Registro de Pedidos")
    cols = st.columns(5)
    for i in range(1, 51):
        with cols[(i-1)%5]:
            estado = "🔴" if st.session_state.mesas[i] else "🟢"
            if st.button(f"{estado} M{i}", key=f"m{i}", use_container_width=True):
                st.session_state.m_act = i
    
    if 'm_act' in st.session_state:
        m = st.session_state.m_act
        st.divider()
        st.subheader(f"Mesa {m}")
        if menu:
            p_sel = st.selectbox("Producto:", list(menu.keys()), key=f"p_{m}")
            cant = st.number_input("Cant:", min_value=1, value=1, key=f"c_{m}")
            if st.button("➕ AGREGAR PEDIDO", use_container_width=True):
                st.session_state.mesas[m].append({
                    "Prod": p_sel, "Cant": cant, "Precio": menu[p_sel], "Sub": menu[p_sel]*cant
                })
                st.rerun()

# --- VISTA CAJA ---
elif modo == "💰 CAJA (Cobros)":
    st.header("💰 Caja Central")
    activas = sorted([i for i, v in st.session_state.mesas.items() if v])
    if activas:
        m_c = st.selectbox("Cobrar Mesa:", activas)
        df_c = pd.DataFrame(st.session_state.mesas[m_c])
        st.table(df_c)
        total = df_c["Sub"].sum()
        st.write(f"## TOTAL: ${total:,.2f}")
        
        metodo = st.radio("Pago:", ["Efectivo", "QR / Transf", "Tarjeta"], horizontal=True)
        if st.button(f"✅ FINALIZAR COBRO MESA {m_c}", use_container_width=True):
            st.session_state.historial.append({
                "Mesa": m_c, "Total": total, "Método": metodo, "Fecha": datetime.now().strftime("%H:%M")
            })
            st.session_state.mesas[m_c] = []
            st.rerun()
    else:
        st.info("No hay mesas con pedidos cargados.")

# --- CIERRE Z ---
elif modo == "📊 CIERRE Z":
    st.header("📊 Cierre de Caja")
    if st.session_state.historial:
        df_z = pd.DataFrame(st.session_state.historial)
        st.metric("RECAUDACIÓN TOTAL", f"${df_z['Total'].sum():,.2f}")
        st.table(df_z.groupby("Método")["Total"].sum())
        if st.button("🖨️ IMPRIMIR"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
