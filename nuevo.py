import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Resto Samuel - Sistema Profesional", layout="wide")

def script_impresion():
    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# 2. CONEXIÓN AL EXCEL (LINK CSV ACTUALIZADO)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3ePfVd6ZQquJqSmd_uB515tMaH20P5xeK9rKJUa0YD3bVj4XLpb4L5Hfos-e5YyRwrA3y7PUj-Fbs/pub?output=csv"

@st.cache_data(ttl=5) # Actualización rápida cada 5 segundos
def cargar_menu():
    try:
        response = requests.get(SHEET_URL)
        response.encoding = 'utf-8'
        # Leemos el contenido como texto para evitar errores de columnas
        df = pd.read_csv(io.StringIO(response.text))
        
        # Limpieza profunda de columnas y datos
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Función para limpiar los precios ($8,500 -> 8500)
        def limpiar_precio(valor):
            if isinstance(valor, str):
                valor = valor.replace('$', '').replace(',', '').strip()
            return float(valor)

        # Creamos el diccionario final
        return {str(row['producto']).strip(): limpiar_precio(row['precio']) for _, row in df.iterrows()}
    except Exception as e:
        st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
        return {}

menu_real = cargar_menu()

# 3. MEMORIA (Estado de sesión)
if 'mesas' not in st.session_state:
    st.session_state.mesas = {i: [] for i in range(1, 51)}
if 'historial' not in st.session_state:
    st.session_state.historial = []

# 4. NAVEGACIÓN
st.sidebar.title("🏨 Menú Principal")
modo = st.sidebar.radio("Ir a:", ["📍 Vista Mozo", "💰 Vista Caja", "📊 Cierre Z"])

# --- VISTA MOZO (50 MESAS) ---
if modo == "📍 Vista Mozo":
    st.header("📍 Panel de Mesas")
    
    # Cuadrícula de 50 mesas
    cols = st.columns(10)
    for i in range(1, 51):
        with cols[(i-1) % 10]:
            estado = "🔴" if st.session_state.mesas[i] else "🟢"
            if st.button(f"{estado}\nMesa {i}", key=f"m{i}"):
                st.session_state.m_act = i

    if 'm_act' in st.session_state:
        m = st.session_state.m_act
        st.divider()
        st.subheader(f"📝 Mesa {m}")
        
        if not menu_real:
            st.warning("Cargando menú desde Excel... si el error persiste, revisá el archivo de Google.")
        else:
            c1, c2 = st.columns([3, 1])
            p_nom = c1.selectbox("Producto:", list(menu_real.keys()), key=f"p_{m}")
            cant = c2.number_input("Cant:", min_value=1, value=1, key=f"c_{m}")
            
            if st.button("➕ AGREGAR PEDIDO", use_container_width=True):
                p_u = menu_real[p_nom]
                st.session_state.mesas[m].append({
                    "Producto": p_nom,
                    "Cantidad": cant,
                    "Precio": p_u,
                    "Subtotal": p_u * cant
                })
                st.rerun()

        if st.session_state.mesas[m]:
            st.table(pd.DataFrame(st.session_state.mesas[m]))
            if st.button("🖨️ Imprimir Comanda"): script_impresion()

# --- VISTA CAJA (COBROS Y VUELTO) ---
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
        
        metodo = st.radio("Pago:", ["Efectivo", "Tarjeta", "Transferencia"], horizontal=True)
        
        vuelto = 0.0
        pago_con = total
        
        if metodo == "Efectivo":
            st.divider()
            pago_con = st.number_input("Paga con:", min_value=float(total), step=100.0)
            vuelto = pago_con - total
            st.subheader(f"💵 Vuelto: ${vuelto:,.2f}")
            st.divider()

        if st.button(f"✅ REGISTRAR PAGO Y LIBERAR MESA {m_c}", use_container_width=True):
            st.session_state.historial.append({
                "Fecha": datetime.now().strftime("%H:%M"),
                "Mesa": m_c, "Total": total, "Metodo": metodo, 
                "Recibido": pago_con, "Vuelto": vuelto
            })
            st.session_state.mesas[m_c] = []
            st.success(f"Mesa {m_c} liberada.")
            st.balloons()
            st.rerun()

# --- CIERRE Z ---
elif modo == "📊 Cierre Z":
    st.header("📊 Resumen del Día")
    if not st.session_state.historial:
        st.warning("Sin ventas.")
    else:
        df_z = pd.DataFrame(st.session_state.historial)
        st.dataframe(df_z, use_container_width=True)
        st.metric("RECAUDACIÓN TOTAL", f"${df_z['Total'].sum():,.2f}")
        st.write("### Por medio de pago")
        st.table(df_z.groupby("Metodo")["Total"].sum())
        if st.button("🖨️ Imprimir Cierre"): script_impresion()
