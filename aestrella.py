import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from networkx.algorithms.shortest_paths.astar import astar_path, astar_path_length

heuristicas=pd.read_csv('Datos/Limpio/tabla_heuristicas.csv', index_col=0)
G_mexico = nx.Graph()
#Conexiones linea 1
G_mexico.add_edge("Observatorio_L1", "Tacubaya_L1", weight=5)
G_mexico.add_edge("Tacubaya_L1", "Juanacatlan_L1", weight=5)
G_mexico.add_edge("Juanacatlan_L1", "Chapultepec_L1", weight=5)
G_mexico.add_edge("Chapultepec_L1", "Sevilla_L1", weight=5)
G_mexico.add_edge("Sevilla_L1", "Insurgentes_L1", weight=5)
G_mexico.add_edge("Insurgentes_L1", "Cuauhtemoc_L1", weight=5)
G_mexico.add_edge("Cuauhtemoc_L1", "Balderas_L1", weight=5)
#Conexiones linea 3
G_mexico.add_edge("Universidad_L3", "Copilco_L3", weight=5)
G_mexico.add_edge("Copilco_L3", "M.A.De Quevedo_L3", weight=5)
G_mexico.add_edge("M.A.De Quevedo_L3", "Viveros_L3", weight=5)
G_mexico.add_edge("Viveros_L3", "Coyoacan_L3", weight=5)
G_mexico.add_edge("Coyoacan_L3", "Zapata_L3", weight=5)
G_mexico.add_edge("Zapata_L3", "Division del Norte_L3", weight=5)
G_mexico.add_edge("Division del Norte_L3", "Eugenia_L3", weight=5)
G_mexico.add_edge("Eugenia_L3", "Etiopia_L3", weight=5)
G_mexico.add_edge("Etiopia_L3", "Centro Medico_L3", weight=5)
G_mexico.add_edge("Centro Medico_L3", "Hospital General_L3", weight=5)
G_mexico.add_edge("Hospital General_L3", "Niños Heroes_L3", weight=5)
G_mexico.add_edge("Niños Heroes_L3", "Balderas_L3", weight=5)
G_mexico.add_edge("Balderas_L3", "Juarez_L3", weight=5)
#Conexiones linea 7
G_mexico.add_edge("Barranca del Muerto_L7", "Mixcoac_L7", weight=5)
G_mexico.add_edge("Mixcoac_L7", "San Antonio_L7", weight=5)
G_mexico.add_edge("San Antonio_L7", "San Pedro de los Pinos_L7", weight=5)
G_mexico.add_edge("San Pedro de los Pinos_L7", "Tacubaya_L7", weight=5)
G_mexico.add_edge("Tacubaya_L7", "Constituyentes_L7", weight=5)
G_mexico.add_edge("Constituyentes_L7", "Auditorio_L7", weight=5)
G_mexico.add_edge("Auditorio_L7", "Polanco_L7", weight=5)
#Conexiones linea 9
G_mexico.add_edge("Tacubaya_L9", "Patriotismo_L9", weight=5)
G_mexico.add_edge("Patriotismo_L9", "Chilpancingo_L9", weight=5)
G_mexico.add_edge("Chilpancingo_L9", "Centro Medico_L9", weight=5)
G_mexico.add_edge("Centro Medico_L9", "Lazaro Cardenas_L9", weight=5)
#Conexiones linea 12
G_mexico.add_edge("Mixcoac_L12", "Insurgentes Sur_L12", weight=5)
G_mexico.add_edge("Insurgentes Sur_L12", "Hospital 20 Noviembre_L12", weight=5)
G_mexico.add_edge("Hospital 20 Noviembre_L12", "Zapata_L12", weight=5)
G_mexico.add_edge("Zapata_L12", "Parque de los Venados_L12", weight=5)
G_mexico.add_edge( "Parque de los Venados_L12", "Eje Central_L12", weight=5)
#Duplicamos los nodos en los que se realizan transbordos
G_mexico.add_edge("Tacubaya_L1", "Tacubaya_L7", weight=5)
G_mexico.add_edge("Tacubaya_L1", "Tacubaya_L9", weight=5)
G_mexico.add_edge("Tacubaya_L7", "Tacubaya_L9", weight=5)
G_mexico.add_edge("Mixcoac_L7", "Mixcoac_L12", weight=5)
G_mexico.add_edge("Centro Medico_L3", "Centro Medico_L9", weight=5)
G_mexico.add_edge("Balderas_L3", "Balderas_L1", weight=5)
G_mexico.add_edge("Zapata_L12", "Zapata_L3", weight=5)

def heuristica_mexico(current, target):
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
print(heuristica_mexico("Observatorio", "Eje Central"))


def trayecto_optimo_distancia(origen, destino):
    camino=nx.astar_path(G_mexico, origen, destino, heuristic=heuristica_mexico, weight="weight")
    dist_total=nx.astar_path_length(G_mexico, origen, destino, heuristic=heuristica_mexico, weight="weight")
    return camino, dist_total

ruta, distancia = trayecto_optimo_distancia("Observatorio_L1", "Eje Central_L12")
print(f"El camino encontrado por A*:{ruta}\nDistancia total: {distancia}")

