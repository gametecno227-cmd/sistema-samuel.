import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Resto Samuel", layout="wide")

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

# 3. MEMORIA DE SESIÓN
if 'mesas' not in st.session_state:
    st.session_state.mesas = {i: [] for i in range(1, 51)}
if 'historial' not in st.session_state:
    st.session_state.historial = []

# 4. INTERFAZ
st.sidebar.title("🏨 Menú Principal")
modo = st.sidebar.radio("Ir a:", ["📍 Mozo", "💰 Caja", "📊 Cierre Z"])

if modo == "📍 Mozo":
    st.header("📍 Panel de Mesas")
    
    # --- ARREGLO DE ORDEN DE MESAS ---
    # Convertimos las llaves a lista y las ordenamos numéricamente
    lista_mesas = sorted(st.session_state.mesas.keys())
    
    # En el celular usamos menos columnas para que no se amontonen
    columnas_grid = 5 if st.container() else 10 
    cols = st.columns(5) # 5 columnas es ideal para que en el celu entren bien
    
    for i in lista_mesas:
        with cols[(i-1)%5]:
            label = f"🔴 M{i}" if st.session_state.mesas[i] else f"🟢 M{i}"
            if st.button(label, key=f"m{i}", use_container_width=True):
                st.session_state.m_act = i
    
    if 'm_act' in st.session_state:
        m = st.session_state.m_act
        st.divider()
        st.subheader(f"📝 Pedido Mesa {m}")
        
        if menu:
            c1, c2 = st.columns([2, 1])
            p_sel = c1.selectbox("Producto:", list(menu.keys()), key=f"s_{m}")
            cant = c2.number_input("Cant:", min_value=1, value=1, key=f"n_{m}")
            
            if st.button("➕ AGREGAR", use_container_width=True):
                precio = menu[p_sel]
                st.session_state.mesas[m].append({"Prod": p_sel, "Cant": cant, "Precio": precio, "Sub": precio*cant})
                st.rerun()
            
            if st.session_state.mesas[m]:
                st.table(pd.DataFrame(st.session_state.mesas[m]))
                if st.button("🗑️ Vaciar Mesa"):
                    st.session_state.mesas[m] = []
                    st.rerun()

elif modo == "💰 Caja":
    st.header("💰 Cobros")
    # Ordenamos también las mesas activas para que salgan en orden en el selector
    activas = sorted([i for i, v in st.session_state.mesas.items() if v])
    
    if activas:
        m_c = st.selectbox("Seleccionar Mesa:", activas)
        df_c = pd.DataFrame(st.session_state.mesas[m_c])
        total = df_c["Sub"].sum()
        st.table(df_c)
        st.write(f"## TOTAL: ${total:,.2f}")
        
        metodo = st.radio("Pago:", ["Efectivo", "QR / Transferencia", "Tarjeta"], horizontal=True)
        if metodo == "Efectivo":
            pago = st.number_input("Paga con:", min_value=float(total))
            st.write(f"### Vuelto: ${pago - total:,.2f}")
        
        if st.button(f"✅ CERRAR MESA {m_c}", use_container_width=True):
            st.session_state.historial.append({"Mesa": m_c, "Total": total, "Método": metodo, "Fecha": datetime.now().strftime("%H:%M")})
            st.session_state.mesas[m_c] = []
            st.rerun()

elif modo == "📊 Cierre Z":
    st.header("📊 Cierre de Caja")
    if st.session_state.historial:
        df_z = pd.DataFrame(st.session_state.historial)
        st.metric("TOTAL RECAUDADO", f"${df_z['Total'].sum():,.2f}")
        st.table(df_z.groupby("Método")["Total"].sum())
        st.write("---")
        st.write("**Detalle de Ventas:**")
        st.dataframe(df_z)
    else:
        st.info("Sin ventas registradas.")
