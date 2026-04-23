import streamlit as st
import pandas as pd
from datetime import datetime

# CONFIGURACIÓN
st.set_page_config(page_title="Resto Samuel", layout="wide")

# TU LINK DE EXCEL
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3ePfVd6ZQquJqSmd_uB515tMaH20P5xeK9rKJUa0YD3bVj4XLpb4L5Hfos-e5YyRwrA3y7PUj-Fbs/pub?output=csv"

@st.cache_data(ttl=30) 
def cargar_menu():
    try:
        df = pd.read_csv(SHEET_URL)
        # ESTO ARREGLA EL PROBLEMA: Pasa todo a minúsculas automáticamente
        df.columns = [c.strip().lower() for c in df.columns]
        return dict(zip(df['producto'], df['precio']))
    except Exception as e:
        return {"Error de Conexión": 0, "Lomito (Local)": 8500}

menu_real = cargar_menu()

# --- EL RESTO DEL CÓDIGO SIGUE IGUAL ---
if 'mesas' not in st.session_state:
    st.session_state.mesas = {i: [] for i in range(1, 51)}
if 'historial_ventas' not in st.session_state:
    st.session_state.historial_ventas = []

st.sidebar.title("🏨 Menú Principal")
modo = st.sidebar.radio("Seleccione una pantalla:", ["📍 Vista Mozo", "💰 Vista Caja", "📊 Cierre Z"])

if modo == "📍 Vista Mozo":
    st.header("Panel de Mesas")
    cols = st.columns(5)
    for i in range(1, 51):
        with cols[(i-1) % 5]:
            estado = "🔴" if st.session_state.mesas[i] else "🟢"
            if st.button(f"{estado} Mesa {i}", key=f"m{i}"):
                st.session_state.m_sel = i

    if 'm_sel' in st.session_state:
        m = st.session_state.m_sel
        st.subheader(f"📝 Mesa {m}")
        p = st.selectbox("Producto", list(menu_real.keys()))
        c = st.number_input("Cantidad", min_value=1, value=1)
        if st.button("➕ Agregar"):
            st.session_state.mesas[m].append({"Producto": p, "Cantidad": c, "Precio": menu_real[p], "Subtotal": menu_real[p]*c})
            st.rerun()
        if st.session_state.mesas[m]:
            st.table(pd.DataFrame(st.session_state.mesas[m]))
            if st.button("🗑️ Vaciar"):
                st.session_state.mesas[m] = []
                st.rerun()

elif modo == "💰 Vista Caja":
    st.header("Caja")
    ocupadas = [i for i, items in st.session_state.mesas.items() if items]
    if not ocupadas: st.info("No hay mesas activas")
    else:
        m_c = st.selectbox("Mesa a cobrar", ocupadas)
        items = st.session_state.mesas[m_c]
        df_c = pd.DataFrame(items)
        total = df_c["Subtotal"].sum()
        st.table(df_c)
        st.metric("TOTAL", f"${total:,.2f}")
        if st.button("✅ COBRAR Y LIBERAR"):
            st.session_state.historial_ventas.append({"Hora": datetime.now().strftime("%H:%M"), "Total": total})
            st.session_state.mesas[m_c] = []
            st.success("Pagado")
            st.rerun()

elif modo == "📊 Cierre Z":
    st.header("Cierre")
    if st.session_state.historial_ventas:
        df_z = pd.DataFrame(st.session_state.historial_ventas)
        st.dataframe(df_z)
        st.metric("Recaudación Total", f"${df_z['Total'].sum():,.2f}")
    else: st.write("Sin ventas")
