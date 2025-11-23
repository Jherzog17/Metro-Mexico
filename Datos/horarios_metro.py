import pandas as pd
import os
import datetime

# =============================================================================
# EXPLICACIÓN GENERAL DEL SCRIPT
# =============================================================================
# Este script se encarga de calcular los horarios de llegada de los trenes del Metro
# de la Ciudad de México utilizando datos en formato GTFS (General Transit Feed Specification).
#
# Lógica Principal:
# 1. Carga de Datos: Se cargan los archivos .txt del GTFS (stops, calendar, trips, etc.) en DataFrames de Pandas.
# 2. Filtrado de Estaciones: Se busca el 'stop_id' correspondiente al nombre de la estación solicitada.
# 3. Filtrado de Servicios Activos: Se determina qué servicios (horarios) están operando hoy basándose en la fecha y día de la semana.
# 4. Búsqueda de Viajes (Trips): Se buscan los viajes asociados a la línea y servicios activos.
# 5. Cálculo de Tiempos:
#    - Se cruzan los viajes con 'stop_times' para saber a qué hora pasa cada tren por la estación.
#    - Se maneja la lógica de "frecuencias" (frequencies.txt), común en metros, donde no hay un horario fijo
#      sino un intervalo de paso (headway) entre una hora de inicio y fin.
# =============================================================================

# Carga de las tablas GTFS necesarias.
# - stops: Información de las estaciones (nombre, coordenadas, id).
# - calendar: Define qué días de la semana opera cada 'service_id' y en qué rango de fechas.
# - trips: Define los viajes individuales, vinculando una ruta (route_id) con un servicio (service_id).
# - freq: (frequencies) Define la frecuencia de paso de los trenes para viajes que no tienen horario fijo.
# - stop_times: Horarios de paso (o secuencia) de cada viaje por cada estación.
# - routes: Definición de las líneas (rutas) del sistema.
stops = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/stops.txt")
calendar = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/calendar.txt")
trips = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/trips.txt")
freq = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/frequencies.txt")
stop_times = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/stop_times.txt")
routes = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/routes.txt")

def hora_a_segundos(hora):
    """
    Convierte un string de hora en formato HH:MM:SS a segundos totales desde la medianoche.
    Útil para comparar horas numéricamente.
    """
    partes = list(map(int, hora.split(':')))
    # Horas * 3600 + Minutos * 60 + Segundos
    return partes[0] * 3600 + partes[1] * 60 + partes[2]

def segundos_a_hora(segundos):
    """
    Operación inversa: Convierte segundos totales a un string con formato HH:MM:SS.
    """
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    # Formateamos con ceros a la izquierda (ej. 05:09:02)
    return f"{horas:02d}:{minutos:02d}:{segs:02d}"

def obtener_stop_ids_candidatos(nodo_estacion, linea_filtro=None):
    """
    Busca los IDs de estación (stop_id) que corresponden a un nombre de nodo del grafo.
    
    Args:
        nodo_estacion (str): Nombre en formato "Nombre_Estacion_L#" (ej. "El_Rosario_L7").
        linea_filtro (str, opcional): Número de línea para filtrar (ej. "7").
    
    Returns:
        list: Lista de stop_ids encontrados en el GTFS que coinciden.
    """
    # Validación básica del formato esperado
    if "_L" not in nodo_estacion:
        return []

    # Separamos el nombre de la estación y la línea
    # Ejemplo: "El_Rosario_L7" -> partes[0]="El_Rosario", partes[1]="7"
    partes = nodo_estacion.split("_L")
    nombre_estacion = partes[0].replace("_", " ") # Reemplazamos guiones bajos por espacios para buscar en el CSV
    
    # Determinamos el código de línea a buscar (ej. "L7")
    if linea_filtro:
        codigo_linea = f"L{linea_filtro}"
    else:
        codigo_linea = f"L{partes[1]}"
    
    # Filtramos el DataFrame 'stops' buscando coincidencias de nombre (insensible a mayúsculas)
    stops_potenciales = stops[stops['stop_name'].str.lower() == nombre_estacion.lower()]
    
    candidatos = []
    # Iteramos sobre las coincidencias para verificar que pertenezcan a la línea correcta.
    # Asumimos que el 'stop_id' en el GTFS contiene el código de la línea (ej. "STN_L7_...")
    for inx, stop in stops_potenciales.iterrows():
        if codigo_linea in stop['stop_id']:
            candidatos.append(stop['stop_id'])
    
    return candidatos

def obtener_service_ids_activos(fecha_obj):
    """
    Identifica qué 'service_id' están operativos en una fecha específica.
    El GTFS usa 'calendar.txt' para definir qué servicios operan qué días de la semana
    y en qué rangos de fechas.
    
    Args:
        fecha_obj (datetime): Objeto fecha y hora actual.
    
    Returns:
        list: Lista de service_ids activos hoy.
    """
    # Obtenemos el nombre del día en inglés y minúsculas (ej. 'monday', 'sunday')
    # Esto coincide con las columnas del archivo calendar.txt
    dia_semana = fecha_obj.strftime('%A').lower()
    
    # Convertimos la fecha a entero YYYYMMDD para comparar con start_date y end_date
    fecha_int = int(fecha_obj.strftime('%Y%m%d'))
    
    # Filtramos el DataFrame calendar con tres condiciones:
    # 1. La fecha actual debe ser mayor o igual a la fecha de inicio del servicio.
    # 2. La fecha actual debe ser menor o igual a la fecha de fin del servicio.
    # 3. La columna correspondiente al día de hoy (ej. 'monday') debe ser 1 (activo).
    servicios_activos = calendar[
        (calendar['start_date'] <= fecha_int) &
        (calendar['end_date'] >= fecha_int) &
        (calendar[dia_semana] == 1)
    ]
    
    return servicios_activos['service_id'].tolist()

def obtener_proximo_tren(estacion_origen, hora_actual_str):
    """
    Calcula la llegada del próximo tren más cercano en la estación de origen.
    Considera tanto horarios fijos como frecuencias.
    
    Args:
        estacion_origen (str): Nombre del nodo (ej. "Tacuba_L2").
        hora_actual_str (str): Hora actual en formato "HH:MM:SS".
        
    Returns:
        dict: Diccionario con info del próximo tren o mensaje de error.
    """
    # 1. Validar y extraer la línea del nombre de la estación
    if "_L" not in estacion_origen:
        return {"error": "Formato de estación origen inválido"}
        
    linea_origen = estacion_origen.split("_L")[1]

    # 2. Obtener los stop_ids correspondientes a esa estación y línea
    candidatos_origen = obtener_stop_ids_candidatos(estacion_origen, linea_filtro=linea_origen)
    
    if not candidatos_origen:
        return {"error": f"Estación origen {estacion_origen} no encontrada"}
        
    # 3. Obtener los servicios (horarios) que operan el día de hoy
    hoy = datetime.datetime.now()
    service_ids_activos = obtener_service_ids_activos(hoy)
    if not service_ids_activos:
        return {"error": "No hay servicios activos para hoy"}

    # 4. Buscar la ruta (Route ID) en el archivo routes.txt
    # Asumimos que 'route_short_name' coincide con el número de línea (ej. "7")
    nombre_corto_ruta = linea_origen
    
    ruta_row = routes[
        (routes['route_short_name'] == nombre_corto_ruta) & 
        (routes['agency_id'] == 'METRO')
    ]
    
    if ruta_row.empty:
        return {"error": f"Ruta de Metro para la Línea {linea_origen} no encontrada"}
        
    route_id = ruta_row.iloc[0]['route_id']

    # 5. Obtener los Viajes (Trips) válidos
    # Filtramos trips que pertenezcan a la ruta encontrada Y a un servicio activo hoy.
    trips_validos = trips[
        (trips['route_id'] == route_id) &
        (trips['service_id'].isin(service_ids_activos))
    ]
    
    if trips_validos.empty:
        return {"error": "No se encontraron viajes válidos"}
        
    trip_ids_validos = trips_validos['trip_id'].tolist()
    
    # 6. Filtrar Stop Times (Horarios por estación)
    # Primero nos quedamos solo con los registros de los viajes válidos
    stop_times_validos = stop_times[stop_times['trip_id'].isin(trip_ids_validos)]
    
    # Luego, filtramos para quedarnos solo con los registros que corresponden a nuestra estación de origen
    st_origen_final = stop_times_validos[stop_times_validos['stop_id'].isin(candidatos_origen)]
    
    if st_origen_final.empty:
            return {"error": "No hay trenes pasando por la estación de origen"}
            
    trip_ids_finales = st_origen_final['trip_id'].unique().tolist()

    # 7. Calcular Próximo Tren (Lógica Principal)
    # Obtenemos información de frecuencias para estos viajes (si existen)
    trip_freqs = freq[freq['trip_id'].isin(trip_ids_finales)]
    
    segundos_actuales = hora_a_segundos(hora_actual_str)
    proxima_llegada_segundos = float('inf') # Inicializamos con infinito para buscar el mínimo
    mejor_trip = None
    
    # Iteramos sobre cada paso de tren por la estación (cada fila en stop_times filtrado)
    for _, row in st_origen_final.iterrows():
        trip_id = row['trip_id']
        # 'offset_llegada' es el tiempo relativo desde el inicio del viaje o la hora absoluta si no es frecuencia
        offset_llegada = hora_a_segundos(row['arrival_time'])
        
        # Verificamos si este viaje está definido por frecuencias
        freq_row = trip_freqs[trip_freqs['trip_id'] == trip_id]
        
        # CASO A: HORARIO FIJO (No está en frequencies.txt)
        if freq_row.empty:
            # Si la hora de llegada es futura y es menor a la mejor encontrada hasta ahora
            if offset_llegada > segundos_actuales:
                if offset_llegada < proxima_llegada_segundos:
                    proxima_llegada_segundos = offset_llegada
                    mejor_trip = trip_id
            continue
        
        # CASO B: BASADO EN FRECUENCIA (Está en frequencies.txt)
        # Los viajes por frecuencia tienen un start_time, end_time y un headway (intervalo en segundos).
        # El tren pasa cada 'headway' segundos comenzando en 'start_time'.
        for _, freq_item in freq_row.iterrows():
            inicio_servicio = hora_a_segundos(freq_item['start_time'])
            fin_servicio = hora_a_segundos(freq_item['end_time'])
            headway = int(freq_item['headway_secs'])
            
            # La llegada base es la hora de inicio del bloque de frecuencia + lo que tarda en llegar a esta estación
            llegada_base = inicio_servicio + offset_llegada
            
            # Si la llegada base ya es futura, es el primer tren de este bloque
            if llegada_base > segundos_actuales:
                if llegada_base < proxima_llegada_segundos:
                    proxima_llegada_segundos = llegada_base
                    mejor_trip = trip_id
            else:
                # Si la llegada base ya pasó, calculamos cuántos intervalos (k) han pasado
                diferencia = segundos_actuales - llegada_base
                k = int(diferencia // headway) + 1 # +1 para obtener el siguiente
                
                # Calculamos la hora de la próxima llegada proyectada
                proxima_llegada = llegada_base + k * headway
                
                # Verificamos que este tren proyectado salga antes de que termine el servicio
                salida_origen_viaje = inicio_servicio + k * headway
                if salida_origen_viaje <= fin_servicio:
                    if proxima_llegada < proxima_llegada_segundos:
                        proxima_llegada_segundos = proxima_llegada
                        mejor_trip = trip_id

    # Si no encontramos ninguna llegada futura
    if proxima_llegada_segundos == float('inf'):
        return {"mensaje": "No hay más trenes hoy"}
        
    # Calculamos tiempo de espera y obtenemos detalles finales
    segundos_espera = proxima_llegada_segundos - segundos_actuales
    info_trip = trips[trips['trip_id'] == mejor_trip].iloc[0]
    direccion = info_trip['trip_headsign'] # Dirección del tren (ej. "Pantitlán")
    
    return {
        "estacion_origen": estacion_origen,
        "proxima_llegada": segundos_a_hora(proxima_llegada_segundos),
        "tiempo_espera": segundos_a_hora(segundos_espera),
        "trip_id": mejor_trip,
        "direccion": direccion
    }

def obtener_proximos_trenes(estacion_origen, hora_actual_str, n=5):
    """
    Versión extendida de obtener_proximo_tren.
    Devuelve una lista de los próximos 'n' trenes en la estación de origen.
    
    Args:
        estacion_origen (str): Nombre de la estación.
        hora_actual_str (str): Hora actual.
        n (int): Cantidad de trenes a devolver.
        
    Returns:
        list: Lista de diccionarios con la información de cada tren.
    """
    # --- (Bloque de validación y obtención de datos idéntico a la función anterior) ---
    if "_L" not in estacion_origen:
        return []
        
    linea_origen = estacion_origen.split("_L")[1]

    candidatos_origen = obtener_stop_ids_candidatos(estacion_origen, linea_filtro=linea_origen)
    
    if not candidatos_origen:
        return []
        
    hoy = datetime.datetime.now()
    service_ids_activos = obtener_service_ids_activos(hoy)
    if not service_ids_activos:
        return []

    nombre_corto_ruta = linea_origen
    
    ruta_row = routes[
        (routes['route_short_name'] == nombre_corto_ruta) & 
        (routes['agency_id'] == 'METRO')
    ]
    
    if ruta_row.empty:
        return []
        
    route_id = ruta_row.iloc[0]['route_id']

    trips_validos = trips[
        (trips['route_id'] == route_id) &
        (trips['service_id'].isin(service_ids_activos))
    ]
    
    if trips_validos.empty:
        return []
        
    trip_ids_validos = trips_validos['trip_id'].tolist()
    stop_times_validos = stop_times[stop_times['trip_id'].isin(trip_ids_validos)]
    
    st_origen_final = stop_times_validos[stop_times_validos['stop_id'].isin(candidatos_origen)]
    
    if st_origen_final.empty:
            return []
            
    trip_ids_finales = st_origen_final['trip_id'].unique().tolist()
    # ----------------------------------------------------------------------------------

    # Calcular Próximos Trenes
    trip_freqs = freq[freq['trip_id'].isin(trip_ids_finales)]
    
    segundos_actuales = hora_a_segundos(hora_actual_str)
    llegadas = [] # Lista para almacenar todas las llegadas futuras encontradas
    
    for _, row in st_origen_final.iterrows():
        trip_id = row['trip_id']
        offset_llegada = hora_a_segundos(row['arrival_time'])
        
        freq_row = trip_freqs[trip_freqs['trip_id'] == trip_id]
        
        # Obtener dirección del viaje actual
        info_trip = trips[trips['trip_id'] == trip_id].iloc[0]
        direccion = info_trip['trip_headsign']

        # CASO A: HORARIO FIJO
        if freq_row.empty:
            if offset_llegada > segundos_actuales:
                llegadas.append({
                    "hora_llegada": offset_llegada,
                    "trip_id": trip_id,
                    "direccion": direccion
                })
            continue
        
        # CASO B: FRECUENCIAS
        for _, freq_item in freq_row.iterrows():
            inicio_servicio = hora_a_segundos(freq_item['start_time'])
            fin_servicio = hora_a_segundos(freq_item['end_time'])
            headway = int(freq_item['headway_secs'])
            
            llegada_base = inicio_servicio + offset_llegada
            
            if llegada_base > segundos_actuales:
                # Si el primer tren del bloque es futuro, lo agregamos
                llegadas.append({
                    "hora_llegada": llegada_base,
                    "trip_id": trip_id,
                    "direccion": direccion
                })
            else:
                # Si ya empezó, calculamos el siguiente inmediato
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
                    # NOTA: Aquí podríamos agregar más trenes (k+1, k+2...) si quisiéramos llenar
                    # la lista 'n' solo con este trip, pero por simplicidad tomamos el siguiente
                    # de cada patrón de viaje.

    # Ordenamos todas las llegadas encontradas por hora (ascendente)
    llegadas.sort(key=lambda x: x['hora_llegada'])
    
    # Formateamos la salida para los primeros 'n' resultados
    resultados = []
    for item in llegadas[:n]:
        segundos_espera = item['hora_llegada'] - segundos_actuales
        resultados.append({
            "proxima_llegada": segundos_a_hora(item['hora_llegada']),
            "tiempo_espera": segundos_a_hora(segundos_espera),
            "direccion": item['direccion']
        })
        
    return resultados
