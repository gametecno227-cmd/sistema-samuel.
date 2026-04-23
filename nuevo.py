import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Resto Samuel - Sistema Profesional", layout="wide")

# 2. CONEXIÓN A TU GOOGLE SHEETS (Link CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3ePfVd6ZQquJqSmd_uB515tMaH20P5xeK9rKJUa0YD3bVj4XLpb4L5Hfos-e5YyRwrA3y7PUj-Fbs/pub?output=csv"

@st.cache_data(ttl=60) # Actualiza los precios del Excel cada 60 segundos
def cargar_menu():
    try:
        # Leemos el Excel desde la web
        df = pd.read_csv(SHEET_URL)
        # Limpiamos espacios por las dudas y creamos el diccionario de productos
        df.columns = df.columns.str.strip().str.lower()
        return dict(zip(df['producto'], df['precio']))
    except Exception as e:
        # Si falla el internet o el link, usa este menú de emergencia
        return {"Error de Conexión": 0, "Lomito (Local)": 8500}

# Cargamos los productos que pusiste en el Excel
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
                          "📊 Cierre Z / Auditoría"])

# --- LÓGICA DE VISTA MOZO ---
if modo == "📍 Vista Mozo (Pedidos)":
    st.header("Panel de Mesas")
    
    cols = st.columns(5)
    for i in range(1, 51):
        with cols[(i-1) % 5]:
            estado = "🔴" if st.session_state.mesas[i] else "🟢"
            if st.button(f"{estado} Mesa {i}", key=f"btn_m_{i}"):
                st.session_state.mesa_seleccionada = i

    if 'mesa_seleccionada' in st.session_state:
        m = st.session_state.mesa_seleccionada
        st.divider()
        st.subheader(f"📝 Tomando Pedido: Mesa {m}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            # Aquí aparecen los productos que tenés en tu Google Sheets
            prod = st.selectbox("Seleccionar Producto (Desde Excel)", list(menu_real.keys()))
        with col2:
            cant = st.number_input("Cantidad", min_value=1, value=1)
        
        if st.button("➕ Agregar a la Comanda"):
            precio_unitario = menu_real[prod]
            st.session_state.mesas[m].append({
                "Producto": prod, 
                "Cantidad": cant, 
                "Precio U.": precio_unitario, 
                "Subtotal": precio_unitario * cant
            })
            st.rerun()

        if st.session_state.mesas[m]:
            df_m = pd.DataFrame(st.session_state.mesas[m])
            st.table(df_m)
            total_m = df_m["Subtotal"].sum()
            st.write(f"**Subtotal Mesa {m}: ${total_m:,.2f}**")
            
            c_enviar, c_vaciar = st.columns(2)
            with c_enviar:
                if st.button("🚀 ENVIAR COMANDA", use_container_width=True):
                    st.success(f"✅ Comanda de Mesa {m} enviada.")
            with c_vaciar:
                if st.button("🗑️ Vaciar Mesa", use_container_width=True):
                    st.session_state.mesas[m] = []
                    st.rerun()

# --- LÓGICA DE VISTA CAJA ---
elif modo == "💰 Vista Caja (Cobros)":
    st.header("Facturación y Cobros")
    ocupadas = [i for i, items in st.session_state.mesas.items() if items]
    
    if not ocupadas:
        st.info("No hay mesas con consumos activos.")
    else:
        m_cobrar = st.selectbox("Seleccione la mesa a cobrar:", ocupadas)
        
        if m_cobrar:
            items_caja = st.session_state.mesas[m_cobrar]
            df_caja = pd.DataFrame(items_caja)
            total = df_caja["Subtotal"].sum()
            
            st.table(df_caja)
            st.divider()
            
            col_t1, col_t2 = st.columns(2)
            col_t1.metric("TOTAL A PAGAR", f"${total:,.2f}")
            
            metodo = st.radio("Forma de pago:", ["Efectivo", "Tarjeta / Posnet", "Transferencia / QR"], horizontal=True)
            
            vuelto = 0.0
            recibido = total
            
            if metodo == "Efectivo":
                st.write("---")
                c1, c2 = st.columns(2)
                recibido = c1.number_input("Monto recibido:", min_value=float(total), step=100.0, value=float(total))
                vuelto = recibido - total
                c2.metric("Vuelto a entregar:", f"${vuelto:,.2f}")
                st.write("---")

            if st.button("✅ REGISTRAR PAGO Y LIBERAR MESA", use_container_width=True):
                st.session_state.historial_ventas.append({
                    "Hora": datetime.now().strftime("%H:%M"),
                    "Mesa": m_cobrar,
                    "Total": total,
                    "Método": metodo,
                    "Recibido": recibido,
                    "Vuelto": vuelto
                })
                st.session_state.mesas[m_cobrar] = []
                st.success("Mesa liberada.")
                st.balloons()
                st.rerun()

# --- LÓGICA DE CIERRE Z ---
elif modo == "📊 Cierre Z / Auditoría":
    st.header("Cierre de Caja")
    
    if not st.session_state.historial_ventas:
        st.warning("No hay ventas registradas hoy.")
    else:
        df_z = pd.DataFrame(st.session_state.historial_ventas)
        st.write("### Movimientos del Día")
        st.dataframe(df_z, use_container_width=True)
        
        efectivo_esp = df_z[df_z["Método"] == "Efectivo"]["Total"].sum()
        total_dia = df_z["Total"].sum()
        
        res1, res2 = st.columns(2)
        res1.metric("Efectivo esperado", f"${efectivo_esp:,.2f}")
        res2.metric("TOTAL RECAUDADO", f"${total_dia:,.2f}")
        
        st.divider()
        efectivo_real = st.number_input("Efectivo físico en caja:", min_value=0.0, step=100.0)
        
        if st.button("Generar Reporte de Cierre"):
            diff = efectivo_real - efectivo_esp
            if diff == 0: st.success("Caja exacta.")
            elif diff > 0: st.info(f"Sobran: ${diff:,.2f}")
            else: st.error(f"Faltan: ${abs(diff):,.2f}")