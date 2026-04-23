import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests
import json
import os

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Resto Samuel - Sistema Blindado", layout="wide")

DB_FILE = "datos_restaurante.json"

# --- FUNCIONES DE PERSISTENCIA (GUARDADO AUTOMÁTICO) ---
def guardar_datos():
    datos = {
        "mesas": st.session_state.mesas,
        "historial": st.session_state.historial
    }
    with open(DB_FILE, "w") as f:
        json.dump(datos, f)

def cargar_datos_disco():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            datos = json.load(f)
            # Convertimos las llaves de las mesas de nuevo a números (JSON las guarda como texto)
            st.session_state.mesas = {int(k): v for k, v in datos["mesas"].items()}
            st.session_state.historial = datos["historial"]
    else:
        st.session_state.mesas = {i: [] for i in range(1, 51)}
        st.session_state.historial = []

# --- INICIALIZACIÓN ---
if 'mesas' not in st.session_state:
    cargar_datos_disco()

def gatillar_impresion():
    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# 2. CONEXIÓN AL EXCEL
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR683Ef1FFMFjMj0NqgygAm6d3siwKrKUtlmG_Xd3n_qv8zO56a2PnG6lBr66sMYxkJ2LOZfTZqoien/pub?output=csv"

@st.cache_data(ttl=5)
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

# 4. INTERFAZ
st.sidebar.title("🏨 Menú Principal")
modo = st.sidebar.radio("Ir a:", ["📍 Mozo", "💰 Caja", "📊 Cierre Z"])

# --- VISTA MOZO ---
if modo == "📍 Mozo":
    st.header("📍 Panel de Mesas")
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
        st.subheader(f"📝 Comanda Mesa {m}")
        if menu:
            c1, c2 = st.columns([2, 1])
            p_sel = c1.selectbox("Producto:", list(menu.keys()), key=f"s_{m}")
            cant = c2.number_input("Cant:", min_value=1, value=1, key=f"n_{m}")
            if st.button("➕ AGREGAR AL PEDIDO", use_container_width=True):
                st.session_state.mesas[m].append({
                    "Prod": p_sel, "Cant": cant, "Precio": menu[p_sel], "Sub": menu[p_sel]*cant
                })
                guardar_datos() # GUARDAMOS AL DISCO
                st.rerun()
            
            if st.session_state.mesas[m]:
                st.write("### 👁️ Vista Previa")
                st.table(pd.DataFrame(st.session_state.mesas[m])[['Cant', 'Prod']])
                if st.button("🖨️ IMPRIMIR COMANDA"):
                    gatillar_impresion()
                if st.button("🗑️ Vaciar Mesa"):
                    st.session_state.mesas[m] = []
                    guardar_datos() # GUARDAMOS AL DISCO
                    st.rerun()

# --- VISTA CAJA ---
elif modo == "💰 Caja":
    st.header("💰 Facturación")
    activas = sorted([i for i, v in st.session_state.mesas.items() if v])
    if activas:
        m_c = st.selectbox("Cobrar Mesa:", activas)
        df_c = pd.DataFrame(st.session_state.mesas[m_c])
        total = df_c["Sub"].sum()
        st.table(df_c)
        st.write(f"## TOTAL: ${total:,.2f}")
        metodo = st.radio("Pago:", ["Efectivo", "QR / Transferencia", "Tarjeta"], horizontal=True)
        if metodo == "Efectivo":
            pago = st.number_input("Paga con:", min_value=float(total), step=100.0)
            st.warning(f"### Vuelto: ${pago - total:,.2f}")
        
        if st.button(f"✅ FINALIZAR COBRO MESA {m_c}", use_container_width=True):
            st.session_state.historial.append({
                "Mesa": m_c, "Total": total, "Método": metodo, "Fecha": datetime.now().strftime("%H:%M")
            })
            st.session_state.mesas[m_c] = []
            guardar_datos() # GUARDAMOS AL DISCO
            st.success("Mesa cerrada.")
            st.rerun()
    else:
        st.info("No hay mesas abiertas.")

# --- CIERRE Z ---
elif modo == "📊 Cierre Z":
    st.header("📊 Cierre de Caja")
    if st.session_state.historial:
        df_z = pd.DataFrame(st.session_state.historial)
        st.metric("RECAUDACIÓN TOTAL", f"${df_z['Total'].sum():,.2f}")
        st.table(df_z.groupby("Método")["Total"].sum())
        
        if st.button("🖨️ IMPRIMIR REPORTE Z"):
            gatillar_impresion()
            
        st.divider()
        # SOLO AQUÍ SE BORRA TODO DE VERDAD
        if st.button("❌ REINICIAR DÍA (BORRAR TODO EL HISTORIAL)"):
            st.session_state.historial = []
            guardar_datos()
            st.success("Historial limpiado para el nuevo día.")
            st.rerun()
    else:
        st.warning("No hay ventas.")
        st.info("Sin ventas registradas.")
