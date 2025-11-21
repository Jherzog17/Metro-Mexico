import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from networkx.algorithms.shortest_paths.astar import astar_path, astar_path_length

heuristicas=pd.read_csv('tabla_heuristicas.csv', index_col=0)
G_mexico = nx.Graph()
#Conexiones linea 1
G_mexico.add_edge("Observatorio", "Tacubaya", weight=5)
G_mexico.add_edge("Tacubaya", "Juanacatlan", weight=5)
G_mexico.add_edge("Juanacatlan", "Chapultepec", weight=5)
G_mexico.add_edge("Chapultepec", "Sevilla", weight=5)
G_mexico.add_edge("Sevilla", "Insurgentes", weight=5)
G_mexico.add_edge("Insurgentes", "Cuauhtemoc", weight=5)
G_mexico.add_edge("Cuauhtemoc", "Balderas", weight=5)
#Conexiones linea 3
G_mexico.add_edge("Universidad", "Copilco", weight=5)
G_mexico.add_edge("Copilco", "M.A.De Quevedo", weight=5)
G_mexico.add_edge("M.A.De Quevedo", "Viveros", weight=5)
G_mexico.add_edge("Viveros", "Coyoacan", weight=5)
G_mexico.add_edge("Coyoacan", "Zapata", weight=5)
G_mexico.add_edge("Zapata", "Division del Norte", weight=5)
G_mexico.add_edge("Division del Norte", "Eugenia", weight=5)
G_mexico.add_edge("Eugenia", "Etiopia", weight=5)
G_mexico.add_edge("Etiopia", "Centro Medico", weight=5)
G_mexico.add_edge("Centro Medico", "Hospital General", weight=5)
G_mexico.add_edge("Hospital General", "Niños Heroes", weight=5)
G_mexico.add_edge("Niños Heroes", "Balderas", weight=5)
G_mexico.add_edge("Balderas", "Juarez", weight=5)
#Conexiones linea 7
G_mexico.add_edge("Barranca del Muerto", "Mixcoac", weight=5)
G_mexico.add_edge("Mixcoac", "San Antonio", weight=5)
G_mexico.add_edge("San Antonio", "San Pedro de los Pinos", weight=5)
G_mexico.add_edge("San Pedro de los Pinos", "Tacubaya", weight=5)
G_mexico.add_edge("Tacubaya", "Constituyentes", weight=5)
G_mexico.add_edge("Constituyentes", "Auditorio", weight=5)
G_mexico.add_edge("Auditorio", "Polanco", weight=5)
#Conexiones linea 9
G_mexico.add_edge("Tacubaya", "Patriotismo", weight=5)
G_mexico.add_edge("Patriotismo", "Chilpancingo", weight=5)
G_mexico.add_edge("Chilpancingo", "Centro Medico", weight=5)
G_mexico.add_edge("Centro Medico", "Lazaro Cardenas", weight=5)
#Conexiones linea 12
G_mexico.add_edge("Mixcoac", "Insurgentes Sur", weight=5)
G_mexico.add_edge("Insurgentes Sur", "Hospital 20 Noviembre", weight=5)
G_mexico.add_edge("Hospital 20 Noviembre", "Zapata", weight=5)
G_mexico.add_edge("Zapata", "Parque de los Venados", weight=5)
G_mexico.add_edge( "Parque de los Venados", "Eje Central", weight=5)




def heuristica_mexico(current, target):
    if current in heuristicas.index and target in heuristicas.columns:
        return float(heuristicas.at[current, target])
    else:
        return 0.0

def trayecto_optimo_distancia(origen, destino):
    camino=nx.astar_path(G_mexico, origen, destino, heuristic=heuristica_mexico, weight="weight")
    dist_total=nx.astar_path_length(G_mexico, origen, destino, heuristic=heuristica_mexico, weight="weight")
    return f"El camino encontrado por A*:{camino}\nDistancia total: {dist_total}"

print(trayecto_optimo_distancia("Observatorio", "Eje Central"))