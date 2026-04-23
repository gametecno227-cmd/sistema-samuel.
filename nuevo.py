import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Resto Samuel", layout="wide")

# 2. ENLACE AL EXCEL (CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3ePfVd6ZQquJqSmd_uB515tMaH20P5xeK9rKJUa0YD3bVj4XLpb4L5Hfos-e5YyRwrA3y7PUj-Fbs/pub?output=csv"

@st.cache_data(ttl=5)
def cargar_menu():
    try:
        # Método blindado: Descargamos el archivo primero
        response = requests.get(SHEET_URL, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            # Leemos el contenido descargado
            df = pd.read_csv(io.StringIO(response.text))
            
            # Limpiamos nombres de columnas (quita espacios y pone minúsculas)
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            # Función para limpiar precios ($8,500 -> 8500)
            def limpiar_p(v):
                if isinstance(v, str):
                    v = v.replace('$', '').replace(',', '').strip()
                return float(v)
            
            # Creamos el diccionario: producto -> precio
            return {str(row['producto']).strip(): limpiar_p(row['precio']) for _, row in df.iterrows()}
        else:
            return None
    except Exception as e:
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
    cols = st.columns(10)
    for i in range(1, 51):
        with cols[(i-1)%10]:
            etiqueta = "🔴" if st.session_state.mesas[i] else "🟢"
            if st.button(f"{etiqueta}\nM{i}", key=f"m{i}"):
                st.session_state.m_act = i
    
    if 'm_act' in st.session_state:
        m = st.session_state.m_act
        st.divider()
        st.subheader(f"Mesa {m}")
        
        if menu:
            c1, c2 = st.columns([3, 1])
            p_sel = c1.selectbox("Producto:", list(menu.keys()), key=f"sel_{m}")
            cant = c2.number_input("Cantidad:", min_value=1, value=1, key=f"cant_{m}")
            
            if st.button("➕ Agregar Pedido", use_container_width=True):
                precio = menu[p_sel]
                st.session_state.mesas[m].append({
                    "Producto": p_sel, 
                    "Cantidad": cant, 
                    "Precio": precio, 
                    "Subtotal": precio * cant
                })
                st.rerun()
            
            if st.session_state.mesas[m]:
                st.table(pd.DataFrame(st.session_state.mesas[m]))
        else:
            st.error("❌ No se pudo conectar con el Excel. Verifica que esté 'Publicado en la Web'.")

elif modo == "💰 Caja":
    st.header("💰 Cobros")
    activas = [i for i, v in st.session_state.mesas.items() if v]
    if activas:
        m_c = st.selectbox("Mesa a cobrar:", activas)
        df_c = pd.DataFrame(st.session_state.mesas[m_c])
        total = df_c["Subtotal"].sum()
        st.table(df_c)
        st.write(f"## TOTAL: ${total:,.2f}")
        
        # Lógica de Efectivo/Vuelto
        metodo = st.radio("Método:", ["Efectivo", "Otro"], horizontal=True)
        if metodo == "Efectivo":
            pago = st.number_input("Paga con:", min_value=float(total))
            st.write(f"### Vuelto: ${pago - total:,.2f}")

        if st.button(f"✅ Finalizar Mesa {m_c}", use_container_width=True):
            st.session_state.historial.append({"Mesa": m_c, "Total": total, "Fecha": datetime.now()})
            st.session_state.mesas[m_c] = []
            st.rerun()
    else:
        st.info("No hay mesas para cobrar.")

elif modo == "📊 Cierre Z":
    st.header("📊 Cierre de Caja")
    if st.session_state.historial:
        df_z = pd.DataFrame(st.session_state.historial)
        st.metric("Recaudación Total", f"${df_z['Total'].sum():,.2f}")
        st.dataframe(df_z, use_container_width=True)
    else:
        st.write("No hay ventas registradas.")
