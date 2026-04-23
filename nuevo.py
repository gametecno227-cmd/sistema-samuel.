import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN E IMPRESIÓN
st.set_page_config(page_title="Resto Samuel - SISTEMA FINAL", layout="wide")

def script_impresion():
    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# 2. CONEXIÓN AL EXCEL
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3ePfVd6ZQquJqSmd_uB515tMaH20P5xeK9rKJUa0YD3bVj4XLpb4L5Hfos-e5YyRwrA3y7PUj-Fbs/pub?output=csv"

@st.cache_data(ttl=10)
def cargar_menu():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [str(c).strip().lower() for c in df.columns]
        return dict(zip(df['producto'], df['precio']))
    except:
        return {"Lomo completo": 8500, "Papas grandes": 7500}

menu = cargar_menu()

# 3. MEMORIA
if 'mesas' not in st.session_state:
    st.session_state.mesas = {i: [] for i in range(1, 51)}
if 'historial' not in st.session_state:
    st.session_state.historial = []

# 4. NAVEGACIÓN
st.sidebar.title("🏨 PANEL DE CONTROL")
modo = st.sidebar.radio("Ir a:", ["📍 MOZO", "💰 CAJA", "📊 CIERRE Z"])

# --- PANTALLA MOZO ---
if modo == "📍 MOZO":
    st.header("📍 Pedidos - 50 Mesas")
    cols = st.columns(10)
    for i in range(1, 51):
        with cols[(i-1) % 10]:
            color = "🔴" if st.session_state.mesas[i] else "🟢"
            if st.button(f"{color}\nM{i}", key=f"m{i}"):
                st.session_state.m_act = i

    if 'm_act' in st.session_state:
        m = st.session_state.m_act
        st.divider()
        st.subheader(f"📝 Mesa {m}")
        c1, c2 = st.columns([3, 1])
        p = c1.selectbox("Producto:", list(menu.keys()), key=f"sel_{m}")
        c = c2.number_input("Cant:", min_value=1, value=1, key=f"cant_{m}")
        
        if st.button("➕ AGREGAR PEDIDO"):
            st.session_state.mesas[m].append({"Producto": p, "Cant": c, "Precio": menu[p], "Total": menu[p]*c})
            st.rerun()
            
        if st.session_state.mesas[m]:
            st.table(pd.DataFrame(st.session_state.mesas[m]))
            if st.button("🖨️ Comanda"): script_impresion()

# --- PANTALLA CAJA (CON VUELTO CORREGIDO) ---
elif modo == "💰 CAJA":
    st.header("💰 Facturación")
    ocupadas = [i for i, items in st.session_state.mesas.items() if items]
    
    if not ocupadas:
        st.info("No hay mesas activas.")
    else:
        m_c = st.selectbox("Seleccione mesa para cobrar:", ocupadas)
        items = st.session_state.mesas[m_c]
        df_c = pd.DataFrame(items)
        total = df_c["Total"].sum()
        
        st.table(df_c)
        st.write(f"## TOTAL: ${total:,.2f}")
        
        metodo = st.radio("Forma de Pago:", ["Efectivo", "Tarjeta", "Transferencia"], horizontal=True)
        
        # Lógica de Vuelto
        recibido = total
        vuelto = 0.0
        
        if metodo == "Efectivo":
            st.warning("PAGO EN EFECTIVO")
            recibido = st.number_input("Monto entregado por cliente:", min_value=float(total), step=100.0)
            vuelto = recibido - total
            st.write(f"### 💵 VUELTO: ${vuelto:,.2f}")

        # EL BOTÓN AHORA ESTÁ AQUÍ ABAJO Y REGISTRA TODO
        if st.button(f"✅ REGISTRAR PAGO Y LIBERAR MESA {m_c}", use_container_width=True):
            st.session_state.historial.append({
                "Hora": datetime.now().strftime("%H:%M"),
                "Mesa": m_c,
                "Total": total,
                "Metodo": metodo,
                "PagoCon": recibido,
                "Vuelto": vuelto
            })
            st.session_state.mesas[m_c] = [] # Se libera la mesa
            st.success("Cobro exitoso.")
            st.balloons()
            st.rerun()

# --- PANTALLA CIERRE Z ---
elif modo == "📊 CIERRE Z":
    st.header("📊 Cierre de Caja")
    if not st.session_state.historial:
        st.write("Sin ventas.")
    else:
        df_z = pd.DataFrame(st.session_state.historial)
        st.dataframe(df_z, use_container_width=True)
        st.metric("VENTAS TOTALES", f"${df_z['Total'].sum():,.2f}")
        
        # Desglose por método
        resumen = df_z.groupby("Metodo")["Total"].sum()
        st.write("### Desglose por Medio de Pago")
        st.table(resumen)
        
        if st.button("🖨️ Imprimir Z"): script_impresion()
