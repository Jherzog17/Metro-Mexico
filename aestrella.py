import networkx as nx
#import matplotlib.pyplot as plt
import pandas as pd
from networkx.algorithms.shortest_paths.astar import astar_path, astar_path_length

#CARGAMOS LOS DATOS
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#La tabla de heurísticas, tiene como índice los nombres de las estaciones
heuristicas=pd.read_csv('Datos/Limpio/tabla_heuristicas.csv', index_col=0)
#El archivo de conexiones del metro, que contiene: estaciones origen, destino,
#distancia real entre ambas, linea a la que pertenece
#IMPORTANTE, en este archivo estan incluidos los transbordos
distancias=pd.read_csv('Datos/Limpio/distancias_reales_transbordos.csv')
#----------------------------------------------------------------------------------------------------------------------------------------------------
#INICIALIZACIÓN EL GRAFO
G_mexico = nx.Graph()
#CONSTRUCCIÓN DEL GRAFO
#Cada iteración añade una arista al grafo(add_edge),
#usando el peso real del tramo, lo mismo con los transbordos
for origen, destino, distancia, linea in distancias.values:
    G_mexico.add_edge(origen, destino, weight=float(distancia))

def heuristica_mexico(current, target):
    """
        Esta funcion calcula la heurística h(n) entre dos estaciones.
        NetworkX llama a la funcion pasando el normbre de las estaciones de origen y destino del tipo (Observatorio_L1),
        pero la tabla de heurísticas usa únicamente los nombres físicos (sin '_L1').
        Por eso eliminamos la parte anterior al '_L'.
        """
    if "_L" in current:
        current_bien = current.split("_L")[0]
    else:
        current_bien=current
    if "_L" in target:
        target_bien=target.split("_L")[0]
    else:
        target_bien=target
    if current_bien in heuristicas.index and target_bien in heuristicas.columns:
        return float(heuristicas.at[current_bien, target_bien])
    else:
        return 0.0
    
#prueba para comprobar que se calculan bien las heurísticas
print(heuristica_mexico("Observatorio", "Eje Central"))

#====================FUNCION QUE EJECUTA A*====================
def trayecto_optimo_distancia(origen, destino):
    """
       Ejecuta el algoritmo A* sobre el grafo del metro.
          -> origen y destino son estaciones del grafo, (incluyendo el sufijo de la línea)
          - weight='weight' indica que el coste g(n) es la distancia real de la arista.
          - heuristic=heuristica_mexico guia la búsqueda con la h(n).
       """
    camino=nx.astar_path(G_mexico, origen, destino, heuristic=heuristica_mexico, weight="weight")
    # Importante: astar_path_length devuelve g(n), no g(n)+h(n).
    dist_total=nx.astar_path_length(G_mexico, origen, destino, heuristic=heuristica_mexico, weight="weight")
    return f"El camino encontrado por A*:{camino}\nDistancia total: {dist_total}"

#prueba para comprobar A*
print(trayecto_optimo_distancia("Observatorio_L1", "Eje Central_L12"))

