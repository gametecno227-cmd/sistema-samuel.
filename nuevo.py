import streamlit as st
import pandas as pd

# CONFIGURACIÓN RÁPIDA
st.set_page_config(page_title="Resto Samuel", layout="wide")

# TU ENLACE DIRECTO
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3ePfVd6ZQquJqSmd_uB515tMaH20P5xeK9rKJUa0YD3bVj4XLpb4L5Hfos-e5YyRwrA3y7PUj-Fbs/pub?output=csv"

def cargar_menu():
    try:
        # Forzamos la lectura ignorando errores de formato
        df = pd.read_csv(SHEET_URL)
        # Limpieza total: quitamos espacios y pasamos a minúsculas
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Buscamos las columnas correctas sin importar el orden
        col_prod = 'producto' if 'producto' in df.columns else df.columns[0]
        col_prec = 'precio' if 'precio' in df.columns else df.columns[1]
        
        return dict(zip(df[col_prod], df[col_prec]))
    except:
        # Menú de emergencia real para que NO pierdas la venta
        return {"Lomo completo": 8500, "Papas grandes": 7500, "Gaseosa 1L": 1500}

menu = cargar_menu()

# MEMORIA
if 'mesas' not in st.session_state:
    st.session_state.mesas = {i: [] for i in range(1, 51)}

# VISTA SIMPLIFICADA PARA MOZO
st.title("🚀 Sistema de Pedidos - Resto Samuel")

m_sel = st.selectbox("Seleccione Mesa:", list(range(1, 51)))

col1, col2 = st.columns([2, 1])
with col1:
    prod = st.selectbox("Producto:", list(menu.keys()))
with col2:
    cant = st.number_input("Cantidad:", min_value=1, value=1)

if st.button("➕ AGREGAR PEDIDO", use_container_width=True):
    precio = menu[prod]
    st.session_state.mesas[m_sel].append({
        "producto": prod, 
        "cantidad": cant, 
        "precio": precio, 
        "subtotal": precio * cant
    })
    st.success(f"Agregado a Mesa {m_sel}")

# MOSTRAR COMANDA
if st.session_state.mesas[m_sel]:
    st.subheader(f"Detalle Mesa {m_sel}")
    df_mesa = pd.DataFrame(st.session_state.mesas[m_sel])
    st.table(df_mesa)
    st.write(f"### TOTAL: ${df_mesa['subtotal'].sum():,.2f}")
    
    if st.button("🗑️ VACIAR MESA"):
        st.session_state.mesas[m_sel] = []
        st.rerun()
