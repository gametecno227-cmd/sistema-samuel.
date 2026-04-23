import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Resto Samuel", layout="wide")

# 2. ENLACE AL EXCEL (Publicado como CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3ePfVd6ZQquJqSmd_uB515tMaH20P5xeK9rKJUa0YD3bVj4XLpb4L5Hfos-e5YyRwrA3y7PUj-Fbs/pub?output=csv"

@st.cache_data(ttl=5)
def cargar_menu():
    try:
        # Usamos requests para forzar la descarga limpia del CSV
        response = requests.get(SHEET_URL)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            # Limpiamos nombres de columnas
            df.columns = [str(c).strip().lower() for c in df.columns]
            # Limpiamos los precios de símbolos como '$' o ','
            def limpiar_p(v):
                if isinstance(v, str):
                    v = v.replace('$', '').replace(',', '').strip()
                return float(v)
            return {str(row['producto']).strip(): limpiar_p(row['precio']) for _, row in df.iterrows()}
        else:
            return {}
    except:
        return {}

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
    cols = st.columns(10)
    for i in range(1, 51):
        with cols[(i-1)%10]:
            etiqueta = "🔴" if st.session_state.mesas[i] else "🟢"
            if st.button(f"{etiqueta}\nM{i}", key=f"m{i}"):
                st.session_state.m_act = i
    
    if 'm_act' in st.session_state:
        m = st.session_state.m_act
        st.subheader(f"Mesa {m}")
        if menu:
            p_sel = st.selectbox("Producto:", list(menu.keys()))
            cant = st.number_input("Cantidad:", min_value=1, value=1)
            if st.button("Agregar"):
                precio = menu[p_sel]
                st.session_state.mesas[m].append({"Prod": p_sel, "Cant": cant, "Precio": precio, "Sub": precio*cant})
                st.rerun()
            if st.session_state.mesas[m]:
                st.table(pd.DataFrame(st.session_state.mesas[m]))
        else:
            st.error("No se pudo cargar el menú del Excel.")

elif modo == "💰 Caja":
    st.header("💰 Cobros")
    activas = [i for i, v in st.session_state.mesas.items() if v]
    if activas:
        m_c = st.selectbox("Mesa:", activas)
        df_c = pd.DataFrame(st.session_state.mesas[m_c])
        total = df_c["Sub"].sum()
        st.table(df_c)
        st.write(f"### TOTAL: ${total:,.2f}")
        if st.button("Finalizar Pago"):
            st.session_state.historial.append({"Total": total, "Fecha": datetime.now()})
            st.session_state.mesas[m_c] = []
            st.rerun()
    else:
        st.info("No hay mesas ocupadas.")

elif modo == "📊 Cierre Z":
    st.header("📊 Cierre")
    if st.session_state.historial:
        df_z = pd.DataFrame(st.session_state.historial)
        st.metric("Total Diario", f"${df_z['Total'].sum():,.2f}")
        st.table(df_z)
    else:
        st.write("Sin ventas.")
