import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN E IMPRESIÓN
st.set_page_config(page_title="Resto Samuel - Pro", layout="wide")

def script_impresion():
    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# 2. CONEXIÓN AL EXCEL
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3ePfVd6ZQquJqSmd_uB515tMaH20P5xeK9rKJUa0YD3bVj4XLpb4L5Hfos-e5YyRwrA3y7PUj-Fbs/pub?output=csv"

@st.cache_data(ttl=30)
def cargar_menu():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [str(c).strip().lower() for c in df.columns]
        return dict(zip(df['producto'], df['precio']))
    except:
        return {"Lomo completo": 8500, "Papas grandes": 7500, "Gaseosa 1L": 1500}

menu = cargar_menu()

# 3. MEMORIA
if 'mesas' not in st.session_state:
    st.session_state.mesas = {i: [] for i in range(1, 51)}
if 'historial' not in st.session_state:
    st.session_state.historial = []

# 4. NAVEGACIÓN
st.sidebar.title("🏨 Menú Principal")
modo = st.sidebar.radio("Ir a:", ["📍 Vista Mozo", "💰 Vista Caja", "📊 Cierre Z"])

# --- VISTA MOZO (50 MESAS) ---
if modo == "📍 Vista Mozo":
    st.header("📍 Control de Mesas (1-50)")
    cols = st.columns(10)
    for i in range(1, 51):
        with cols[(i-1) % 10]:
            est = "🔴" if st.session_state.mesas[i] else "🟢"
            if st.button(f"{est}\nM{i}", key=f"m{i}"):
                st.session_state.m_act = i

    if 'm_act' in st.session_state:
        m = st.session_state.m_act
        st.divider()
        st.subheader(f"📝 Mesa {m}")
        c1, c2 = st.columns([3, 1])
        p = c1.selectbox("Producto:", list(menu.keys()))
        c = c2.number_input("Cant:", min_value=1, value=1)
        if st.button("➕ Agregar"):
            st.session_state.mesas[m].append({"Producto": p, "Cant": c, "Precio": menu[p], "Total": menu[p]*c})
            st.rerun()
        if st.session_state.mesas[m]:
            st.table(pd.DataFrame(st.session_state.mesas[m]))
            if st.button("🖨️ Imprimir Comanda"): script_impresion()

# --- VISTA CAJA (CON CÁLCULO DE VUELTO) ---
elif modo == "💰 Vista Caja":
    st.header("💰 Cobros")
    ocupadas = [i for i, items in st.session_state.mesas.items() if items]
    
    if not ocupadas:
        st.info("No hay mesas para cobrar.")
    else:
        m_c = st.selectbox("Mesa a cobrar:", ocupadas)
        df_c = pd.DataFrame(st.session_state.mesas[m_c])
        total = df_c["Total"].sum()
        
        st.table(df_c)
        st.write(f"## TOTAL: ${total:,.2f}")
        
        metodo = st.radio("Método:", ["Efectivo", "Tarjeta", "Transferencia"], horizontal=True)
        
        vuelto = 0.0
        recibido = total
        
        if metodo == "Efectivo":
            st.divider()
            recibido = st.number_input("¿Con cuánto paga el cliente?", min_value=float(total), step=100.0)
            vuelto = recibido - total
            if vuelto > 0:
                st.subheader(f"💵 Vuelto a entregar: ${vuelto:,.2f}")
            elif recibido == total:
                st.write("Pagó justo.")
            st.divider()

        if st.button(f"✅ REGISTRAR PAGO MESA {m_c}", use_container_width=True):
            st.session_state.historial.append({
                "Hora": datetime.now().strftime("%H:%M"),
                "Mesa": m_c,
                "Total": total,
                "Metodo": metodo,
                "Recibido": recibido,
                "Vuelto": vuelto
            })
            st.session_state.mesas[m_c] = []
            st.success(f"Cobro Mesa {m_c} realizado.")
            st.balloons()
            st.rerun()

# --- CIERRE Z ---
elif modo == "📊 Cierre Z":
    st.header("📊 Cierre de Caja")
    if not st.session_state.historial:
        st.write("Sin ventas.")
    else:
        df_z = pd.DataFrame(st.session_state.historial)
        st.dataframe(df_z, use_container_width=True)
        st.metric("VENTAS TOTALES", f"${df_z['Total'].sum():,.2f}")
        
        # Resumen de efectivo para el arqueo
        solo_efectivo = df_z[df_z["Metodo"] == "Efectivo"]["Total"].sum()
        st.metric("EFECTIVO EN CAJA (Esperado)", f"${solo_efectivo:,.2f}")
        
        if st.button("🖨️ Imprimir Cierre"): script_impresion()
