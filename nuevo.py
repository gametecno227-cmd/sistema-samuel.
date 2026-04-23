import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests
import re

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Resto Samuel - Sistema Final", layout="wide")

@st.cache_resource
def obtener_base_datos():
    return {"mesas": {i: [] for i in range(1, 51)}, "historial": []}

db = obtener_base_datos()
if 'mesas' not in st.session_state: st.session_state.mesas = db["mesas"]
if 'historial' not in st.session_state: st.session_state.historial = db["historial"]

def imprimir():
    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# 2. CONEXIÓN AL EXCEL MEJORADA
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR683Ef1FFMFjMj0NqgygAm6d3siwKrKUtlmG_Xd3n_qv8zO56a2PnG6lBr66sMYxkJ2LOZfTZqoien/pub?output=csv"

@st.cache_data(ttl=1)
def cargar_menu():
    try:
        response = requests.get(SHEET_URL, timeout=10)
        response.encoding = 'utf-8'
        df = pd.read_csv(io.StringIO(response.text))
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # FUNCIÓN DE LIMPIEZA DE PRECIOS REFORZADA
        def limpiar_p(v):
            if pd.isna(v) or v == "": return 0.0
            # Quita todo lo que no sea número o coma/punto decimal
            s = re.sub(r'[^\d,.]', '', str(v)).replace(',', '.')
            try:
                return float(s)
            except:
                return 0.0

        return {str(row['producto']).strip(): limpiar_p(row['precio']) for _, row in df.iterrows()}
    except: return None

menu = cargar_menu()

# 3. INTERFAZ
st.sidebar.title("🏨 RESTO SAMUEL")
modo = st.sidebar.radio("Ir a:", ["📍 MOZOS", "💰 CAJA", "📊 CIERRE Z"])

if modo == "📍 MOZOS":
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
        st.subheader(f"📝 Pedido Mesa {m}")
        if menu:
            c1, c2 = st.columns([3, 1])
            p_sel = c1.selectbox("Producto:", list(menu.keys()), key=f"p_{m}")
            cant = c2.number_input("Cant:", min_value=1, value=1, key=f"c_{m}")
            if st.button("➕ AGREGAR AL PEDIDO", use_container_width=True):
                precio = menu[p_sel]
                st.session_state.mesas[m].append({"Prod": p_sel, "Cant": cant, "Precio": precio, "Sub": precio * cant})
                st.rerun()
            
            if st.session_state.mesas[m]:
                st.markdown("### 📋 VISTA PREVIA")
                df_m = pd.DataFrame(st.session_state.mesas[m])
                st.table(df_m[['Cant', 'Prod', 'Sub']])
                c3, c4 = st.columns(2)
                if c3.button("🖨️ IMPRIMIR COMANDA", use_container_width=True): imprimir()
                if c4.button("🗑️ VACIAR MESA", use_container_width=True):
                    st.session_state.mesas[m] = []
                    st.rerun()

elif modo == "💰 CAJA":
    st.header("💰 Cobros")
    activas = sorted([i for i, v in st.session_state.mesas.items() if v])
    if activas:
        m_c = st.selectbox("Mesa a cobrar:", activas)
        df_c = pd.DataFrame(st.session_state.mesas[m_c])
        st.table(df_c)
        total = df_c["Sub"].sum()
        st.write(f"## TOTAL: ${total:,.2f}")
        metodo = st.radio("Pago:", ["Efectivo", "QR / Transferencia", "Tarjeta"], horizontal=True)
        if metodo == "Efectivo":
            pago = st.number_input("Paga con:", min_value=float(total), step=100.0)
            st.warning(f"### Vuelto: ${pago - total:,.2f}")
        if st.button(f"✅ FINALIZAR COBRO MESA {m_c}", use_container_width=True):
            st.session_state.historial.append({"Mesa": m_c, "Total": total, "Método": metodo, "Fecha": datetime.now().strftime("%H:%M")})
            st.session_state.mesas[m_c] = []
            st.rerun()
    else: st.info("No hay mesas ocupadas.")

elif modo == "📊 CIERRE Z":
    st.header("📊 Cierre de Caja")
    if st.session_state.historial:
        df_z = pd.DataFrame(st.session_state.historial)
        total_s = df_z['Total'].sum()
        efect_s = df_z[df_z['Método'] == "Efectivo"]['Total'].sum()
        digi_s = df_z[df_z['Método'].isin(["QR / Transferencia", "Tarjeta"])]['Total'].sum()
        
        st.subheader("📝 Arqueo Manual")
        c1, c2 = st.columns(2)
        e_r = c1.number_input("Efectivo Real ($):", min_value=0.0)
        d_r = c2.number_input("Digital Real ($):", min_value=0.0)
        
        comparativa = pd.DataFrame({
            "Concepto": ["Efectivo", "Digital", "TOTAL"],
            "Sistema": [f"${efect_s:,.2f}", f"${digi_s:,.2f}", f"${total_s:,.2f}"],
            "Real": [f"${e_r:,.2f}", f"${d_r:,.2f}", f"${e_r+d_r:,.2f}"],
            "Dif": [f"${e_r-efect_s:,.2f}", f"${d_r-digi_s:,.2f}", f"${(e_r+d_r)-total_s:,.2f}"]
        })
        st.table(comparativa)
        if st.button("🖨️ IMPRIMIR REPORTE Z"): imprimir()
        if st.button("❌ REINICIAR DÍA"):
            st.session_state.historial = []
            st.rerun()
    else: st.warning("No hay ventas.")
