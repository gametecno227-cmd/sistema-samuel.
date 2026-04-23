import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Resto Samuel - Sistema Profesional", layout="wide")

# Función para disparar la impresión del navegador
def script_impresion():
    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# 2. CONEXIÓN A TU GOOGLE SHEETS (Enlace CSV)
# Usamos el link de tu captura de pantalla
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3ePfVd6ZQquJqSmd_uB515tMaH20P5xeK9rKJUa0YD3bVj4XLpb4L5Hfos-e5YyRwrA3y7PUj-Fbs/pub?output=csv"

@st.cache_data(ttl=10) # Actualiza cada 10 segundos para ver cambios en el Excel rápido
def cargar_menu():
    try:
        df = pd.read_csv(SHEET_URL)
        # Limpiamos nombres de columnas: quitamos espacios y pasamos a minúsculas
        df.columns = [str(c).strip().lower() for c in df.columns]
        # Creamos el diccionario producto -> precio
        return dict(zip(df['producto'], df['precio']))
    except Exception as e:
        # Si falla, no inventamos productos; mostramos el error para arreglarlo
        st.error(f"⚠️ Error de conexión con el Excel: {e}")
        return {}

menu_real = cargar_menu()

# 3. MEMORIA DEL SISTEMA (Estado de sesión)
if 'mesas' not in st.session_state:
    st.session_state.mesas = {i: [] for i in range(1, 51)}
if 'historial_ventas' not in st.session_state:
    st.session_state.historial_ventas = []

# 4. BARRA LATERAL - NAVEGACIÓN
st.sidebar.title("🏨 Menú Principal")
modo = st.sidebar.radio("Seleccione una pantalla:", 
                         ["📍 Vista Mozo (Pedidos)", 
                          "💰 Vista Caja (Cobros)", 
                          "📊 Cierre Z (Auditoría)"])

# --- PANTALLA 1: VISTA MOZO (50 MESAS) ---
if modo == "📍 Vista Mozo (Pedidos)":
    st.header("📍 Panel de Mesas")
    
    # Dibujamos las 50 mesas (10 columnas x 5 filas)
    cols = st.columns(10)
    for i in range(1, 51):
        with cols[(i-1) % 10]:
            # Rojo si tiene items, Verde si está vacía
            estado = "🔴" if st.session_state.mesas[i] else "🟢"
            if st.button(f"{estado}\nMesa {i}", key=f"btn_m{i}"):
                st.session_state.m_seleccionada = i

    # Si hay una mesa seleccionada, mostramos para cargar pedido
    if 'm_seleccionada' in st.session_state:
        m = st.session_state.m_seleccionada
        st.divider()
        st.subheader(f"📝 Tomando Pedido: Mesa {m}")
        
        if not menu_real:
            st.warning("No se cargaron productos del Excel. Revisá la conexión.")
        else:
            c1, c2 = st.columns([3, 1])
            prod_nom = c1.selectbox("Producto (Desde Excel):", list(menu_real.keys()), key=f"sel_{m}")
            cant = c2.number_input("Cantidad:", min_value=1, value=1, key=f"cant_{m}")
            
            if st.button("➕ AGREGAR A LA COMANDA", use_container_width=True):
                precio_u = menu_real[prod_nom]
                st.session_state.mesas[m].append({
                    "Producto": prod_nom,
                    "Cantidad": cant,
                    "Precio": precio_u,
                    "Subtotal": precio_u * cant
                })
                st.rerun()

        # Mostrar lo que ya tiene la mesa
        if st.session_state.mesas[m]:
            df_m = pd.DataFrame(st.session_state.mesas[m])
            st.table(df_m)
            st.write(f"### Subtotal Mesa {m}: ${df_m['Subtotal'].sum():,.2f}")
            
            if st.button("🖨️ IMPRIMIR COMANDA"):
                script_impresion()

# --- PANTALLA 2: VISTA CAJA (COBROS Y VUELTO) ---
elif modo == "💰 Vista Caja (Cobros)":
    st.header("💰 Facturación")
    mesas_activas = [i for i, items in st.session_state.mesas.items() if items]
    
    if not mesas_activas:
        st.info("No hay mesas con pedidos pendientes de cobro.")
    else:
        m_cobro = st.selectbox("Mesa a cobrar:", mesas_activas)
        items_caja = st.session_state.mesas[m_cobro]
        df_caja = pd.DataFrame(items_caja)
        total_pagar = df_caja["Subtotal"].sum()
        
        st.table(df_caja)
        st.metric("TOTAL A COBRAR", f"${total_pagar:,.2f}")
        
        metodo = st.radio("Método de pago:", ["Efectivo", "Tarjeta", "Transferencia"], horizontal=True)
        
        # --- LÓGICA DE VUELTO ---
        vuelto = 0.0
        pago_con = total_pagar
        
        if metodo == "Efectivo":
            st.divider()
            pago_con = st.number_input("¿Con cuánto paga el cliente?", min_value=float(total_pagar), step=100.0)
            vuelto = pago_con - total_pagar
            if vuelto > 0:
                st.subheader(f"💵 Vuelto a entregar: ${vuelto:,.2f}")
            st.divider()

        if st.button(f"✅ FINALIZAR COBRO Y LIBERAR MESA {m_cobro}", use_container_width=True):
            # Guardamos en el historial para el Cierre Z
            st.session_state.historial_ventas.append({
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Mesa": m_cobro,
                "Total": total_pagar,
                "Metodo": metodo,
                "Recibido": pago_con,
                "Vuelto": vuelto
            })
            st.session_state.mesas[m_cobro] = [] # Vaciamos la mesa
            st.success(f"Mesa {m_cobro} cobrada y liberada con éxito.")
            st.balloons()
            st.rerun()

# --- PANTALLA 3: CIERRE Z (AUDITORÍA) ---
elif modo == "📊 Cierre Z / Auditoría":
    st.header("📊 Resumen de Ventas del Día")
    
    if not st.session_state.historial_ventas:
        st.warning("Todavía no se han registrado ventas hoy.")
    else:
        df_z = pd.DataFrame(st.session_state.historial_ventas)
        st.write("### Detalle de tickets cerrados")
        st.dataframe(df_z, use_container_width=True)
        
        total_dia = df_z["Total"].sum()
        
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("💰 RECAUDACIÓN TOTAL", f"${total_dia:,.2f}")
        
        # Desglose por método de pago
        st.write("### Resumen por medio de pago")
        st.table(df_z.groupby("Metodo")["Total"].sum())
        
        if st.button("🖨️ IMPRIMIR REPORTE DE CIERRE"):
            script_impresion()
