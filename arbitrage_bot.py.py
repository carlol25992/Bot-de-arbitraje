import streamlit as st
import requests
import pandas as pd
import time

# Función para obtener precios de la API
def obtener_precios():
    url = "https://criptoya.com/api/USDT/BRL/1"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error al consultar la API: {e}")
        return None

# Función para buscar oportunidades de arbitraje
def buscar_oportunidades_arbitraje(data, exchanges_seleccionados):
    exchanges = []
    total_asks = []
    total_bids = []
    
    # Filtrar exchanges seleccionados
    for exchange, info in data.items():
        if exchange in exchanges_seleccionados:
            exchanges.append(exchange)
            total_asks.append(info['totalAsk'])
            total_bids.append(info['totalBid'])
    
    # Crear DataFrame
    df = pd.DataFrame({
        'exchange': exchanges,
        'totalAsk': total_asks,
        'totalBid': total_bids
    })
    
    # Buscar oportunidades
    oportunidades = []
    for i, row_buy in df.iterrows():
        for j, row_sell in df.iterrows():
            if row_buy['exchange'] != row_sell['exchange']:
                ganancia = row_sell['totalBid'] - row_buy['totalAsk']
                if ganancia > 0:
                    oportunidad = {
                        'Exchange de compra': row_buy['exchange'],
                        'Exchange de venta': row_sell['exchange'],
                        'Precio de compra': row_buy['totalAsk'],
                        'Precio de venta': row_sell['totalBid'],
                        'Ganancia en %': (ganancia / row_buy['totalAsk']) * 100
                    }
                    oportunidades.append(oportunidad)
    
    return oportunidades

# Configuración de la interfaz de Streamlit
st.title("Bot de Monitoreo de Arbitraje USDT/BRL")

# Barra lateral para seleccionar exchanges
st.sidebar.header("Selecciona Exchanges")
data = obtener_precios()
if data:
    todos_exchanges = list(data.keys())
    exchanges_seleccionados = []
    
    # Crear checkboxes para cada exchange
    for exchange in todos_exchanges:
        if st.sidebar.checkbox(exchange, value=True):
            exchanges_seleccionados.append(exchange)
    
    # Placeholder para la tabla
    tabla_placeholder = st.empty()
    
    # Bucle para actualizar la tabla
    while True:
        data = obtener_precios()
        if data and exchanges_seleccionados:
            oportunidades = buscar_oportunidades_arbitraje(data, exchanges_seleccionados)
            if oportunidades:
                df_oportunidades = pd.DataFrame(oportunidades)
                # Formatear la columna de porcentaje
                df_oportunidades['Ganancia en %'] = df_oportunidades['Ganancia en %'].map('{:.2f}%'.format)
                tabla_placeholder.dataframe(df_oportunidades, use_container_width=True)
            else:
                tabla_placeholder.write("No hay oportunidades de arbitraje en este momento.")
        else:
            tabla_placeholder.write("No se pudieron cargar datos o no hay exchanges seleccionados.")
        
        time.sleep(10)  # Actualizar cada 10 segundos
else:
    st.write("No se pudieron cargar los datos iniciales de la API.")