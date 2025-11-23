import pandas as pd
import heapq

# AJUSTES VISUALES
SCALE_FACTOR = 30000  # Aumenta esto si el mapa se ve muy chico
OFFSET_X = 0
OFFSET_Y = 0


class MetroDataHandler:
    def __init__(self):
        self.graph = {}  # Conexiones reales
        self.stations_xy = {}  # Coordenadas para dibujar
        self.heuristics_df = None  # Tabla de heurísticas cargada
        self.loaded = False

    def load_data(self):
        """Carga los 3 archivos CSV clave."""
        try:
            # 1. CARGAR ESTACIONES (Para pintar en pantalla)
            df_stations = pd.read_csv("estaciones_limpias.csv")

            # Centrar el mapa
            mean_lat = df_stations["Latitud"].mean()
            mean_lon = df_stations["Longitud"].mean()

            for _, row in df_stations.iterrows():
                name = row["Nombre_Estacion"].strip()
                lat = row["Latitud"]
                lon = row["Longitud"]

                # Convertir GPS a Píxeles (Proyección simple)
                px = (lon - mean_lon) * SCALE_FACTOR + OFFSET_X
                py = -(lat - mean_lat) * SCALE_FACTOR + OFFSET_Y
                self.stations_xy[name] = (px, py)

            # 2. CARGAR ARISTAS (Conexiones reales)
            df_edges = pd.read_csv("distancias_reales.csv")
            edges_list_ui = []  # Lista solo para que la UI dibuje las líneas

            for _, row in df_edges.iterrows():
                u = row["Origen"].strip()
                v = row["Destino"].strip()
                w = float(row["Distancia"])

                # Grafo bidireccional
                if u not in self.graph: self.graph[u] = []
                if v not in self.graph: self.graph[v] = []
                self.graph[u].append((v, w))
                self.graph[v].append((u, w))

                edges_list_ui.append((u, v))

            # 3. CARGAR HEURÍSTICAS (La tabla gigante)
            # Asumimos que la primera columna son los nombres de las filas
            self.heuristics_df = pd.read_csv("tabla_heuristicas.csv", index_col=0)

            # Limpieza: Aseguramos que índices y columnas no tengan espacios extra
            self.heuristics_df.index = self.heuristics_df.index.str.strip()
            self.heuristics_df.columns = self.heuristics_df.columns.str.strip()

            self.loaded = True

            # Devolvemos datos necesarios para la Interfaz Gráfica
            stations_list = sorted(list(self.stations_xy.keys()))
            return stations_list, self.stations_xy, edges_list_ui

        except FileNotFoundError as e:
            # Error útil para saber qué archivo falta
            raise Exception(f"Falta el archivo: {e.filename}")
        except Exception as e:
            raise Exception(f"Error cargando datos: {str(e)}")

    def get_heuristic(self, start_node, end_node):
        """Busca el valor en tu tabla_heuristicas.csv"""
        if self.heuristics_df is None:
            return 0.0
        try:
            # Busca en la tabla: Fila = Origen, Columna = Destino
            return float(self.heuristics_df.loc[start_node, end_node])
        except:
            # Si no encuentra el valor (ej. nombre mal escrito), devuelve 0
            return 0.0

    def find_path_astar(self, start, goal):
        """Algoritmo A* usando tu tabla de heurísticas."""
        if not self.loaded:
            return []
        if start not in self.graph or goal not in self.graph:
            return []

        # Cola: (f_score, g_score, nodo_actual, camino)
        queue = [(0, 0, start, [start])]
        visited = set()
        g_score = {start: 0}

        while queue:
            # Sacamos el nodo con menor f_score (mejor candidato)
            _, current_g, current_node, path = heapq.heappop(queue)

            if current_node == goal:
                return path

            if current_node in visited:
                continue
            visited.add(current_node)

            # Explorar vecinos
            for neighbor, weight in self.graph.get(current_node, []):
                tentative_g = current_g + weight

                # Si encontramos un camino más corto a este vecino
                if tentative_g < g_score.get(neighbor, float('inf')):
                    g_score[neighbor] = tentative_g

                    # f = g (coste real) + h (coste tabla heurística)
                    h = self.get_heuristic(neighbor, goal)
                    f = tentative_g + h

                    heapq.heappush(queue, (f, tentative_g, neighbor, path + [neighbor]))

        return []


# Instancia lista para usar
metro_system = MetroDataHandler()