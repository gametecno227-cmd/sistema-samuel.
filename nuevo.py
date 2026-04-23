import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA E IMPRESIÓN
st.set_page_config(page_title="Resto Samuel - Sistema Profesional", layout="wide")

# Función para disparar la impresión del navegador
def script_impresion():
    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# 2. CONEXIÓN AL EXCEL (URL CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3ePfVd6ZQquJqSmd_uB515tMaH20P5xeK9rKJUa0YD3bVj4XLpb4L5Hfos-e5YyRwrA3y7PUj-Fbs/pub?output=csv"

@st.cache_data(ttl=30)
def cargar_menu():
    try:
        df = pd.read_csv(SHEET_URL)
        # Limpieza de columnas para evitar errores de mayúsculas/minúsculas
        df.columns = [str(c).strip().lower() for c in df.columns]
        return dict(zip(df['producto'], df['precio']))
    except:
        # Menú de respaldo por si falla la conexión
        return {"Lomo completo": 8500, "Papas grandes": 7500, "Gaseosa 1L": 1500, "Cerveza": 3500}

menu = cargar_menu()

# 3. ESTADO DE SESIÓN (MEMORIA)
if 'mesas' not in st.session_state:
    st.session_state.mesas = {i: [] for i in range(1, 51)}
if 'historial_ventas' not in st.session_state:
    st.session_state.historial_ventas = []

# 4. NAVEGACIÓN LATERAL
st.sidebar.title("🏨 Menú Principal")
modo = st.sidebar.radio("Ir a:", ["📍 Vista Mozo", "💰 Vista Caja", "📊 Cierre Z"])

# --- PANTALLA: VISTA MOZO (50 MESAS) ---
if modo == "📍 Vista Mozo":
    st.header("📍 Control de Mesas")
    
    # Dibujamos las 50 mesas en una cuadrícula
    cols = st.columns(10)
    for i in range(1, 51):
        with cols[(i-1) % 10]:
            # Verde si está vacía, Rojo si tiene algo
            estado = "🔴" if st.session_state.mesas[i] else "🟢"
            if st.button(f"{estado}\nM{i}", key=f"btn_m{i}"):
                st.session_state.m_actual = i

    # Si se selecciona una mesa, mostramos para cargar pedido
    if 'm_actual' in st.session_state:
        m = st.session_state.m_actual
        st.divider()
        st.subheader(f"📝 Tomando Pedido: Mesa {m}")
        
        c1, c2 = st.columns([3, 1])
        prod_sel = c1.selectbox("Producto:", list(menu.keys()))
        cant_sel = c2.number_input("Cantidad:", min_value=1, value=1)
        
        if st.button("➕ Agregar a la Comanda"):
            st.session_state.mesas[m].append({
                "Producto": prod_sel,
                "Cantidad": cant_sel,
                "Precio": menu[prod_sel],
                "Total": menu[prod_sel] * cant_sel
            })
            st.rerun()

        if st.session_state.mesas[m]:
            df_m = pd.DataFrame(st.session_state.mesas[m])
            st.table(df_m)
            st.write(f"### Subtotal Mesa {m}: ${df_m['Total'].sum():,.2f}")
            
            if st.button("🖨️ MANDAR COMANDA A COCINA"):
                st.success(f"Comanda Mesa {m} enviada. ¡Imprimiendo...!")
                script_impresion() # Abre diálogo de impresión

# --- PANTALLA: VISTA CAJA ---
elif modo == "💰 Vista Caja":
    st.header("💰 Facturación y Cobros")
    ocupadas = [i for i, items in st.session_state.mesas.items() if items]
    
    if not ocupadas:
        st.info("No hay mesas con consumos activos.")
    else:
        m_a_cobrar = st.selectbox("Seleccione mesa para cobrar:", ocupadas)
        items_caja = st.session_state.mesas[m_a_cobrar]
        df_caja = pd.DataFrame(items_caja)
        total_caja = df_caja["Total"].sum()
        
        st.table(df_caja)
        st.metric("TOTAL A PAGAR", f"${total_caja:,.2f}")
        
        metodo = st.radio("Forma de pago:", ["Efectivo", "Tarjeta", "Transferencia / QR"], horizontal=True)
        
        if st.button(f"✅ FINALIZAR COBRO MESA {m_a_cobrar}", use_container_width=True):
            # Guardamos en el historial para el Cierre Z
            st.session_state.historial_ventas.append({
                "Hora": datetime.now().strftime("%H:%M"),
                "Mesa": m_a_cobrar,
                "Total": total_caja,
                "Metodo": metodo
            })
            st.session_state.mesas[m_a_cobrar] = [] # Liberamos la mesa
            st.success("Venta registrada y mesa liberada.")
            st.balloons()
            st.rerun()

# --- PANTALLA: CIERRE Z ---
elif modo == "📊 Cierre Z":
    st.header("📊 Resumen de Ventas Diarias")
    
    if not st.session_state.historial_ventas:
        st.warning("No hay ventas realizadas en esta sesión.")
    else:
        df_z = pd.DataFrame(st.session_state.historial_ventas)
        st.write("### Detalle de Movimientos")
        st.dataframe(df_z, use_container_width=True)
        
        total_general = df_z["Total"].sum()
        
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("RECAUDACIÓN TOTAL", f"${total_general:,.2f}")
        
        # Desglose rápido por método de pago
        st.write("### Ventas por Medio de Pago")
        st.table(df_z.groupby("Metodo")["Total"].sum())
        
        if st.button("🖨️ IMPRIMIR REPORTE Z"):
            script_impresion()
