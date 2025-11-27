"""
Funciones para cargar datos del metro y calcular rutas.
Usa las funciones de aestrella.py para el cálculo de rutas.
"""
import sys
from pathlib import Path
import pandas as pd

# Añadir el directorio padre al path para poder importar aestrella
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar funciones de aestrella.py
from aestrella import G_mexico, heuristica_mexico, trayecto_optimo_distancia, heuristicas


# Configuración para conversión de coordenadas
SCALE_FACTOR = 30000
OFFSET_X = 0
OFFSET_Y = 0


def cargar_datos():
    """
    Carga todos los datos necesarios desde los archivos CSV.
    Usa el grafo G_mexico y la tabla de heurísticas ya cargados en aestrella.py.
    
    Returns:
        tuple: (stations_list, stations_xy, edges_list, graph, heuristics_df, 
                station_mapping, reverse_mapping)
    """
    # Ruta base a los archivos CSV (partiendo desde la raíz del proyecto)
    directorio_root = Path(__file__).parent.parent / "Datos" / "Limpio"
    
    # 1. Cargar estaciones (coordenadas)
    df_stations = pd.read_csv(directorio_root / "estaciones_limpias.csv")
    
    # Centrar el mapa
    mean_lat = df_stations["Latitud"].mean()
    mean_lon = df_stations["Longitud"].mean()
    
    # Diccionario de coordenadas en píxeles
    stations_xy = {}
    for _, row in df_stations.iterrows():
        name = row["Nombre_Estacion"].strip()
        lat = row["Latitud"]
        lon = row["Longitud"]
        
        # Convertir GPS a píxeles
        px = (lon - mean_lon) * SCALE_FACTOR + OFFSET_X
        py = -(lat - mean_lat) * SCALE_FACTOR + OFFSET_Y
        stations_xy[name] = (px, py)
    
    # 2. Cargar conexiones (para construir mapeos y edges_list)
    df_edges = pd.read_csv(directorio_root / "distancias_reales_transbordos.csv")
    
    edges_list = []
    station_mapping = {}  # nombre simple -> [nombres con línea]
    reverse_mapping = {}  # nombre con línea -> nombre simple
    
    for _, row in df_edges.iterrows():
        u = row["Origen"].strip()
        v = row["Destino"].strip()
        
        # Extraer nombres simples
        u_simple = u.split("_L")[0] if "_L" in u else u
        v_simple = v.split("_L")[0] if "_L" in v else v
        
        # Construir mapeos
        if u_simple not in station_mapping:
            station_mapping[u_simple] = []
        if u not in station_mapping[u_simple]:
            station_mapping[u_simple].append(u)
        reverse_mapping[u] = u_simple
        
        if v_simple not in station_mapping:
            station_mapping[v_simple] = []
        if v not in station_mapping[v_simple]:
            station_mapping[v_simple].append(v)
        reverse_mapping[v] = v_simple
        
        # Lista de aristas para UI (sin duplicados)
        edge_ui = (u_simple, v_simple)
        if edge_ui not in edges_list and (v_simple, u_simple) not in edges_list:
            edges_list.append(edge_ui)
    
    # Lista de estaciones ordenada
    stations_list = sorted(list(stations_xy.keys()))
    
    # Cargar tiempos de entrada
    tiempos_entrada = cargar_tiempos_entrada(directorio_root)

    # Usar el grafo y heurísticas de aestrella.py
    return stations_list, stations_xy, edges_list, G_mexico, heuristicas, station_mapping, reverse_mapping, tiempos_entrada


def cargar_tiempos_entrada(directorio_root):
    """
    Carga los tiempos de entrada a las estaciones desde el CSV.
    
    Returns:
        dict: Diccionario {Nombre_Estacion: Tiempo_Entrada_Minutos}
    """
    try:
        df = pd.read_csv(directorio_root / "estaciones_limpias_tiempos.csv")
        # Crear diccionario: Nombre_Estacion -> Tiempo_Entrada_Minutos
        # Asumimos que el nombre es único o tomamos el primero si hay duplicados (generalmente es por línea)
        # Para simplificar, usaremos el nombre simple y si hay conflicto, el promedio o el primero.
        # Dado que el usuario pide "Desde la boca de metro de estacion origen", 
        # y el CSV tiene "Nombre_Estacion" y "Linea", pero la UI usa nombres simples para el origen.
        
        tiempos = {}
        for _, row in df.iterrows():
            nombre = row["Nombre_Estacion"].strip()
            tiempo = row["Tiempo_Entrada_Minutos"]
            # Guardamos el tiempo. Si ya existe (otra línea), lo mantenemos o sobreescribimos.
            # Lo ideal sería tener tiempos por línea, pero la UI selecciona por nombre de estación.
            # Guardaremos el primero que encontremos para esa estación.
            if nombre not in tiempos:
                tiempos[nombre] = tiempo
        return tiempos
    except Exception as e:
        print(f"Error cargando tiempos de entrada: {e}")
        return {}


def obtener_heuristica(current, target, heuristics_df):
    """
    Obtiene el valor heurístico entre dos estaciones.
    Usa la función heuristica_mexico de aestrella.py.
    
    Args:
        current: Estación actual (puede tener sufijo _L)
        target: Estación objetivo (puede tener sufijo _L)
        heuristics_df: DataFrame con la tabla de heurísticas (no se usa, se mantiene por compatibilidad)
    
    Returns:
        float: Valor heurístico
    """
    # Usar la función de aestrella.py
    return heuristica_mexico(current, target)


def calcular_ruta(origen, destino, graph, station_mapping, reverse_mapping, heuristics_df):
    """
    Calcula la ruta óptima entre dos estaciones usando A*.
    Usa la función trayecto_optimo_distancia de aestrella.py.
    
    Args:
        origen: Nombre simple de la estación de origen
        destino: Nombre simple de la estación de destino
        graph: Grafo NetworkX con las conexiones (no se usa, usa G_mexico de aestrella.py)
        station_mapping: Diccionario de mapeo nombre simple -> nombres con línea
        reverse_mapping: Diccionario de mapeo nombre con línea -> nombre simple
        heuristics_df: DataFrame con la tabla de heurísticas (no se usa)
    
    Returns:
        dict: Diccionario con 'ruta' (lista de estaciones), 'distancia' y 'tiempo'
    """
    # Obtener todas las opciones de líneas para origen y destino
    start_options = station_mapping.get(origen, [])
    goal_options = station_mapping.get(destino, [])
    
    if not start_options or not goal_options:
        return None
    
    # Probar todas las combinaciones y encontrar la ruta más corta
    best_resultado = None
    best_length = float('inf')
    
    for start in start_options:
        for goal in goal_options:
            try:
                # Usar la función de aestrella.py
                resultado = trayecto_optimo_distancia(start, goal)
                
                # Extraer distancia del resultado
                length = resultado["distancia"]
                
                if length < best_length:
                    best_length = length
                    best_resultado = resultado
                    
            except Exception:
                # Si no hay camino, continuar con la siguiente combinación
                continue
    
    if best_resultado is None:
        return None
    
    # Convertir a nombres simples para la UI
    simple_path = [reverse_mapping.get(node, node.split("_L")[0] if "_L" in node else node)
                   for node in best_resultado["ruta"]]
    
    # Retornar diccionario con toda la información
    return {
        "ruta": simple_path,
        "ruta_cruda": best_resultado["ruta"],
        "distancia": best_resultado["distancia"],
        "tiempo": best_resultado["tiempo"]
    }

