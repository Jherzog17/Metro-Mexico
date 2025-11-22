import pandas as pd
import os
import datetime


stops = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/stops.txt")
calendar = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/calendar.txt")
trips = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/trips.txt")
freq = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/frequencies.txt")
stop_times = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/stop_times.txt")
routes = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/routes.txt")

def hora_a_segundos(hora):
    """
    Convierte un string de hora HH:MM:SS a segundos
    """
    partes = list(map(int, hora.split(':')))
    return partes[0] * 3600 + partes[1] * 60 + partes[2]

def segundos_a_hora(segundos):
    """
    Convierte segundos a string HH:MM:SS
    """
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    return f"{horas:02d}:{minutos:02d}:{segs:02d}"

def obtener_stop_ids_candidatos(nodo_estacion, linea_filtro=None):
    """
    Obtiene una lista de stop_ids candidatos para un nombre que esté en el grafo.
    Si se especifica linea_filtro, fuerza a buscar stops en esa línea.
    """
    if "_L" not in nodo_estacion:
        return []

    partes = nodo_estacion.split("_L")
    nombre_estacion = partes[0].replace("_", " ")
    
    # Si nos dan un filtro de línea, lo usamos. Si no, usamos el del nodo.
    if linea_filtro:
        codigo_linea = f"L{linea_filtro}"
    else:
        codigo_linea = f"L{partes[1]}"
    
    stops_potenciales = stops[stops['stop_name'].str.lower() == nombre_estacion.lower()]
    
    candidatos = []
    for inx, stop in stops_potenciales.iterrows():
        if codigo_linea in stop['stop_id']:
            candidatos.append(stop['stop_id'])
    
    return candidatos

def obtener_service_ids_activos(fecha_obj):
    """
    Retorna una lista de service_ids activos para la fecha dada.
    La fecha tendra el formato Año-Mes-Día Hora:Minuto:Segundo.Microsegundos
    """
    dia_semana = fecha_obj.strftime('%A').lower()#Da el dia de la semana en minusculas
    fecha_int = int(fecha_obj.strftime('%Y%m%d'))
    
    #Comprueba que el servicio está entre las fechas correctas y que el dia de la 
    #semana está a 1, es decir, está activo
    servicios_activos = calendar[
        (calendar['start_date'] <= fecha_int) &
        (calendar['end_date'] >= fecha_int) &
        (calendar[dia_semana] == 1)
    ]
    
    return servicios_activos['service_id'].tolist()

def obtener_proximo_tren(estacion_origen, hora_actual_str):
    """
    Calcula la llegada del próximo tren en la estación de origen (cualquier dirección).
    """
    # Obtener la línea del origen
    if "_L" not in estacion_origen:
        return {"error": "Formato de estación origen inválido"}
        
    linea_origen = estacion_origen.split("_L")[1]

    # Obtener candidatos de stop_id para el origen
    candidatos_origen = obtener_stop_ids_candidatos(estacion_origen, linea_filtro=linea_origen)
    
    if not candidatos_origen:
        return {"error": f"Estación origen {estacion_origen} no encontrada"}
        
    # Obtener servicios activos
    hoy = datetime.datetime.now()
    service_ids_activos = obtener_service_ids_activos(hoy)
    if not service_ids_activos:
        return {"error": "No hay servicios activos para hoy"}

    # Obtener el route id usando la línea del origen
    nombre_corto_ruta = linea_origen
    
    ruta_row = routes[
        (routes['route_short_name'] == nombre_corto_ruta) & 
        (routes['agency_id'] == 'METRO')
    ]
    
    if ruta_row.empty:
        return {"error": f"Ruta de Metro para la Línea {linea_origen} no encontrada"}
        
    route_id = ruta_row.iloc[0]['route_id']

    # Obtener Viajes Válidos
    trips_validos = trips[
        (trips['route_id'] == route_id) &
        (trips['service_id'].isin(service_ids_activos))
    ]
    
    if trips_validos.empty:
        return {"error": "No se encontraron viajes válidos"}
        
    trip_ids_validos = trips_validos['trip_id'].tolist()
    stop_times_validos = stop_times[stop_times['trip_id'].isin(trip_ids_validos)]
    
    # Tomamos todos los trips que pasan por el origen
    st_origen_final = stop_times_validos[stop_times_validos['stop_id'].isin(candidatos_origen)]
    
    if st_origen_final.empty:
            return {"error": "No hay trenes pasando por la estación de origen"}
            
    trip_ids_finales = st_origen_final['trip_id'].unique().tolist()

    # Calcular Próximo Tren
    trip_freqs = freq[freq['trip_id'].isin(trip_ids_finales)]
    
    segundos_actuales = hora_a_segundos(hora_actual_str)
    proxima_llegada_segundos = float('inf')
    mejor_trip = None
    
    for _, row in st_origen_final.iterrows():
        trip_id = row['trip_id']
        offset_llegada = hora_a_segundos(row['arrival_time'])
        
        freq_row = trip_freqs[trip_freqs['trip_id'] == trip_id]
        
        if freq_row.empty:
            if offset_llegada > segundos_actuales:
                if offset_llegada < proxima_llegada_segundos:
                    proxima_llegada_segundos = offset_llegada
                    mejor_trip = trip_id
            continue
        
        for _, freq_item in freq_row.iterrows():
            inicio_servicio = hora_a_segundos(freq_item['start_time'])
            fin_servicio = hora_a_segundos(freq_item['end_time'])
            headway = int(freq_item['headway_secs'])
            
            llegada_base = inicio_servicio + offset_llegada
            
            if llegada_base > segundos_actuales:
                if llegada_base < proxima_llegada_segundos:
                    proxima_llegada_segundos = llegada_base
                    mejor_trip = trip_id
            else:
                diferencia = segundos_actuales - llegada_base
                k = int(diferencia // headway) + 1
                proxima_llegada = llegada_base + k * headway
                
                salida_origen_viaje = inicio_servicio + k * headway
                if salida_origen_viaje <= fin_servicio:
                    if proxima_llegada < proxima_llegada_segundos:
                        proxima_llegada_segundos = proxima_llegada
                        mejor_trip = trip_id

    if proxima_llegada_segundos == float('inf'):
        return {"mensaje": "No hay más trenes hoy"}
        
    segundos_espera = proxima_llegada_segundos - segundos_actuales
    info_trip = trips[trips['trip_id'] == mejor_trip].iloc[0]
    direccion = info_trip['trip_headsign']
    
    return {
        "estacion_origen": estacion_origen,
        "proxima_llegada": segundos_a_hora(proxima_llegada_segundos),
        "tiempo_espera": segundos_a_hora(segundos_espera),
        "trip_id": mejor_trip,
        "direccion": direccion
    }

def obtener_proximos_trenes(estacion_origen, hora_actual_str, n=5):
    """
    Devuelve una lista de los próximos n trenes en la estación de origen.
    """
    # Obtener la línea del origen
    if "_L" not in estacion_origen:
        return []
        
    linea_origen = estacion_origen.split("_L")[1]

    # Obtener candidatos de stop_id para el origen
    candidatos_origen = obtener_stop_ids_candidatos(estacion_origen, linea_filtro=linea_origen)
    
    if not candidatos_origen:
        return []
        
    # Obtener servicios activos
    hoy = datetime.datetime.now()
    service_ids_activos = obtener_service_ids_activos(hoy)
    if not service_ids_activos:
        return []

    # Obtener el route id usando la línea del origen
    nombre_corto_ruta = linea_origen
    
    ruta_row = routes[
        (routes['route_short_name'] == nombre_corto_ruta) & 
        (routes['agency_id'] == 'METRO')
    ]
    
    if ruta_row.empty:
        return []
        
    route_id = ruta_row.iloc[0]['route_id']

    # Obtener Viajes Válidos
    trips_validos = trips[
        (trips['route_id'] == route_id) &
        (trips['service_id'].isin(service_ids_activos))
    ]
    
    if trips_validos.empty:
        return []
        
    trip_ids_validos = trips_validos['trip_id'].tolist()
    stop_times_validos = stop_times[stop_times['trip_id'].isin(trip_ids_validos)]
    
    # Tomamos todos los trips que pasan por el origen
    st_origen_final = stop_times_validos[stop_times_validos['stop_id'].isin(candidatos_origen)]
    
    if st_origen_final.empty:
            return []
            
    trip_ids_finales = st_origen_final['trip_id'].unique().tolist()

    # Calcular Próximos Trenes
    trip_freqs = freq[freq['trip_id'].isin(trip_ids_finales)]
    
    segundos_actuales = hora_a_segundos(hora_actual_str)
    llegadas = []
    
    for _, row in st_origen_final.iterrows():
        trip_id = row['trip_id']
        offset_llegada = hora_a_segundos(row['arrival_time'])
        
        freq_row = trip_freqs[trip_freqs['trip_id'] == trip_id]
        
        # Obtener dirección
        info_trip = trips[trips['trip_id'] == trip_id].iloc[0]
        direccion = info_trip['trip_headsign']

        if freq_row.empty:
            if offset_llegada > segundos_actuales:
                llegadas.append({
                    "hora_llegada": offset_llegada,
                    "trip_id": trip_id,
                    "direccion": direccion
                })
            continue
        
        for _, freq_item in freq_row.iterrows():
            inicio_servicio = hora_a_segundos(freq_item['start_time'])
            fin_servicio = hora_a_segundos(freq_item['end_time'])
            headway = int(freq_item['headway_secs'])
            
            llegada_base = inicio_servicio + offset_llegada
            
            if llegada_base > segundos_actuales:
                llegadas.append({
                    "hora_llegada": llegada_base,
                    "trip_id": trip_id,
                    "direccion": direccion
                })
            else:
                diferencia = segundos_actuales - llegada_base
                k = int(diferencia // headway) + 1
                proxima_llegada = llegada_base + k * headway
                
                salida_origen_viaje = inicio_servicio + k * headway
                if salida_origen_viaje <= fin_servicio:
                    llegadas.append({
                        "hora_llegada": proxima_llegada,
                        "trip_id": trip_id,
                        "direccion": direccion
                    })
                    # Agregar siguientes llegadas de este mismo trip (frecuencia)
                    # para llenar la lista si es necesario, aunque simplificaremos tomando solo la próxima de cada trip
                    # o podríamos agregar más iteraciones de k si n es grande.
                    # Por ahora, tomamos la próxima inmediata de este patrón.

    # Ordenar por hora de llegada
    llegadas.sort(key=lambda x: x['hora_llegada'])
    
    # Formatear salida
    resultados = []
    for item in llegadas[:n]:
        segundos_espera = item['hora_llegada'] - segundos_actuales
        resultados.append({
            "proxima_llegada": segundos_a_hora(item['hora_llegada']),
            "tiempo_espera": segundos_a_hora(segundos_espera),
            "direccion": item['direccion']
        })
        
    return resultados
