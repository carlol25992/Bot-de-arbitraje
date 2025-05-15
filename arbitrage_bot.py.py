import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# Lista de monedas disponibles
MONEDAS = ["ETH", "BTC", "USDT", "USDC", "POL", "SOL", "BNB", "XRP", "DOT", "TRX", "XLM"]

# Función para obtener precios con reintentos
def obtener_precios(moneda, retries=3, delay=2):
    url = f"https://criptoya.com/api/{moneda}/BRL/1"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Error al obtener datos para {moneda}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    return None

# Función para buscar oportunidades de arbitraje
def buscar_oportunidades_arbitraje(data, exchanges_seleccionados, moneda, fee_porcentaje):
    exchanges = []
    total_asks = []
    total_bids = []
    
    for exchange, info in data.items():
        if exchange in exchanges_seleccionados and 'totalAsk' in info and 'totalBid' in info:
            try:
                ask = float(info['totalAsk'])
                bid = float(info['totalBid'])
                exchanges.append(exchange)
                total_asks.append(ask)
                total_bids.append(bid)
            except ValueError:
                st.warning(f"Datos inválidos para {exchange} en {moneda}")
                continue
    
    df = pd.DataFrame({
        'exchange': exchanges,
        'totalAsk': total_asks,
        'totalBid': total_bids
    })
    
    oportunidades = []
    for i, row_buy in df.iterrows():
        for j, row_sell in df.iterrows():
            if row_buy['exchange'] != row_sell['exchange']:
                precio_compra = row_buy['totalAsk']
                precio_venta = row_sell['totalBid']
                costo_compra = precio_compra * (1 + fee_porcentaje / 100)
                ingreso_venta = precio_venta * (1 - fee_porcentaje / 100)
                ganancia = ingreso_venta - costo_compra
                if ganancia > 0:
                    oportunidad = {
                        'Moneda': moneda,
                        'Exchange de compra': row_buy['exchange'],
                        'Exchange de venta': row_sell['exchange'],
                        'Precio de compra': precio_compra,
                        'Precio de venta': precio_venta,
                        'Ganancia en %': (ganancia / costo_compra) * 100
                    }
                    oportunidades.append(oportunidad)
    return oportunidades

# Función para obtener lista de exchanges disponibles (caché por 1 hora)
@st.cache_data(ttl=3600)
def get_exchanges():
    data = obtener_precios("BTC")
    if data:
        return sorted(list(data.keys()))
    return []

# Configuración de la interfaz de Streamlit
st.title("Bot de Monitoreo de Arbitraje de Criptomonedas")
st.write("Monitorea oportunidades de arbitraje en tiempo real usando la API de CriptoYa.")

# Selección de monedas
st.header("Selecciona las monedas para arbitrar")
monedas_seleccionadas = st.multiselect(
    "Monedas",
    options=MONEDAS,
    default=["USDT", "BTC", "ETH"],
    help="Selecciona las monedas que deseas monitorear."
)

# Obtener y mostrar exchanges disponibles
exchanges_disponibles = get_exchanges()
if not exchanges_disponibles:
    st.error("No se pudieron obtener los exchanges disponibles. Verifica la conexión a la API.")
else:
    st.sidebar.header("Selecciona Exchanges")
    exchanges_seleccionados = []
    for exchange in exchanges_disponibles:
        if st.sidebar.checkbox(exchange, value=True, key=f"exchange_{exchange}"):
            exchanges_seleccionados.append(exchange)

# Configuración en la barra lateral
st.sidebar.header("Configuración")
fee_porcentaje = st.sidebar.number_input(
    "Comisión por transacción (%)",
    min_value=0.0,
    max_value=5.0,
    value=0.5,
    step=0.1,
    help="Porcentaje estimado de comisión por transacción."
)
min_ganancia = st.sidebar.slider(
    "Ganancia mínima (%)",
    0.0,
    10.0,
    1.0,
    help="Filtra oportunidades con ganancia mayor a este porcentaje."
)
intervalo = st.sidebar.selectbox(
    "Intervalo de actualización (segundos)",
    [10, 15, 30, 60],
    index=1,
    help="Frecuencia de actualización de los datos."
)
monitoring = st.sidebar.checkbox("Monitorear oportunidades", value=True)

# Contenedores para tabla y timestamp
st.subheader("Oportunidades de Arbitraje")
tabla_placeholder = st.empty()
timestamp_placeholder = st.empty()

# Lógica de monitoreo
if monitoring and monedas_seleccionadas and len(exchanges_seleccionados) >= 2:
    with st.spinner("Actualizando oportunidades..."):
        while True:
            oportunidades_totales = []
            for moneda in monedas_seleccionadas:
                data = obtener_precios(moneda)
                if data:
                    oportunidades = buscar_oportunidades_arbitraje(data, exchanges_seleccionados, moneda, fee_porcentaje)
                    oportunidades_totales.extend([op for op in oportunidades if op['Ganancia en %'] >= min_ganancia])
                else:
                    st.warning(f"No se pudieron cargar datos para {moneda}/BRL.")
            
            if oportunidades_totales:
                df_oportunidades = pd.DataFrame(oportunidades_totales)
                df_oportunidades['Ganancia en %'] = df_oportunidades['Ganancia en %'].map('{:.2f}%'.format)
                df_oportunidades['Precio de compra'] = df_oportunidades['Precio de compra'].map('{:.2f}'.format)
                df_oportunidades['Precio de venta'] = df_oportunidades['Precio de venta'].map('{:.2f}'.format)
                tabla_placeholder.dataframe(df_oportunidades, use_container_width=True)
            else:
                tabla_placeholder.write("No hay oportunidades de arbitraje en este momento.")
            
            timestamp_placeholder.write(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(intervalo)
else:
    st.write("Selecciona al menos una moneda y dos exchanges para comenzar el monitoreo.")
