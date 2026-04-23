import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Resto Samuel - Sistema Profesional", layout="wide")

# Función para impresión
def script_impresion():
    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# 2. CONEXIÓN AL EXCEL (URL Verificada)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3ePfVd6ZQquJqSmd_uB515tMaH20P5xeK9rKJUa0YD3bVj4XLpb4L5Hfos-e5YyRwrA3y7PUj-Fbs/pub?output=csv"

@st.cache_data(ttl=5)
def cargar_menu():
    try:
        response = requests.get(SHEET_URL, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            # Limpiamos columnas: 'producto' y 'precio'
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            def limpiar_p(v):
                if isinstance(v, str):
                    v = v.replace('$', '').replace(',', '').strip()
                return float(v)
            
            return {str(row['producto']).strip(): limpiar_p(row['precio']) for _, row in df.iterrows()}
        else:
            return None
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

menu = cargar_menu()

# 3. MEMORIA (Estado de sesión)
if 'mesas' not in st.session_state:
    st.session_state.mesas = {i: [] for i in range(1, 51)}
if 'historial' not in st.session_state:
    st.session_state.historial = []

# 4. INTERFAZ Y NAVEGACIÓN
st.sidebar.title("🏨 Menú Principal")
modo = st.sidebar.radio("Ir a:", ["📍 Vista Mozo", "💰 Vista Caja", "📊 Cierre Z"])

# --- VISTA MOZO ---
if modo == "📍 Vista Mozo":
    st.header("📍 Panel de Mesas")
    cols = st.columns(10)
    for i in range(1, 51):
        with cols[(i-1)%10]:
            estado = "🔴" if st.session_state.mesas[i] else "🟢"
            if st.button(f"{estado}\nM{i}", key=f"m{i}"):
                st.session_state.m_act = i

    if 'm_act' in st.session_state:
        m = st.session_state.m_act
        st.divider()
        st.subheader(f"📝 Mesa {m}")
        
        if menu:
            c1, c2 = st.columns([3, 1])
            p_sel = c1.selectbox("Seleccionar Producto (Desde Excel):", list(menu.keys()), key=f"sel_{m}")
            cant = c2.number_input("Cantidad:", min_value=1, value=1, key=f"cant_{m}")
            
            if st.button("➕ AGREGAR PEDIDO", use_container_width=True):
                p_u = menu[p_sel]
                st.session_state.mesas[m].append({
                    "Producto": p_sel, "Cantidad": cant, "Precio": p_u, "Subtotal": p_u * cant
                })
                st.rerun()
            
            if st.session_state.mesas[m]:
                st.table(pd.DataFrame(st.session_state.mesas[m]))
                if st.button("🖨️ Imprimir Comanda"): script_impresion()
        else:
            st.error("⚠️ No se pudo cargar el menú. Revisá que el Excel esté publicado como CSV.")

# --- VISTA CAJA ---
elif modo == "💰 Vista Caja":
    st.header("💰 Facturación")
    activas = [i for i, items in st.session_state.mesas.items() if items]
    
    if not activas:
        st.info("No hay mesas ocupadas.")
    else:
        m_c = st.selectbox("Cobrar Mesa:", activas)
        df_c = pd.DataFrame(st.session_state.mesas[m_c])
        total = df_c["Subtotal"].sum()
        
        st.table(df_c)
        st.metric("TOTAL A COBRAR", f"${total:,.2f}")
        
        metodo = st.radio("Forma de pago:", ["Efectivo", "Tarjeta", "Transferencia"], horizontal=True)
        vuelto = 0.0
        pago_con = total
        
        if metodo == "Efectivo":
            pago_con = st.number_input("Paga con:", min_value=float(total), step=100.0)
            vuelto = pago_con - total
            st.write(f"### 💵 Vuelto: ${vuelto:,.2f}")

        if st.button(f"✅ REGISTRAR PAGO Y LIBERAR MESA {m_c}", use_container_width=True):
            st.session_state.historial.append({
                "Fecha": datetime.now().strftime("%H:%M"), "Mesa": m_c, 
                "Total": total, "Metodo": metodo, "Recibido": pago_con, "Vuelto": vuelto
            })
            st.session_state.mesas[m_c] = []
            st.success("Cobro realizado.")
            st.rerun()

# --- CIERRE Z ---
elif modo == "📊 Cierre Z":
    st.header("📊 Cierre de Caja")
    if not st.session_state.historial:
        st.write("No hay ventas registradas.")
    else:
        df_z = pd.DataFrame(st.session_state.historial)
        st.dataframe(df_z, use_container_width=True)
        st.metric("RECAUDACIÓN TOTAL", f"${df_z['Total'].sum():,.2f}")
        st.write("### Desglose por Medio de Pago")
        st.table(df_z.groupby("Metodo")["Total"].sum())
        if st.button("🖨️ Imprimir Reporte"): script_impresion()
