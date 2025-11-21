import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import unicodedata
from networkx.algorithms.shortest_paths.astar import astar_path, astar_path_length

def normalize(text):
    if not isinstance(text, str):
        return str(text)
    text = text.strip()
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn').lower()

def get_normalized_name(name):
    norm = normalize(name)
    mapping = {
        'm.a.de quevedo': normalize('Miguel Ángel de Quevedo'),
        'viveros': normalize('Viveros y  Derechos Humanos'),
        'etiopia': normalize('Etiopía y Plaza de la Transparencia'),
        'ninos heroes': normalize('Niños Héroes y  Poder Judicial CDMX'),
        'hospital 20 noviembre': normalize('Hospital 20 de Noviembre')
    }
    return mapping.get(norm, norm)

# Cargar datos y normalizar claves
heuristicas = pd.read_csv('Datos/Limpio/tabla_heuristicas.csv', index_col=0)
heuristicas.index = [normalize(x) for x in heuristicas.index]
heuristicas.columns = [normalize(x) for x in heuristicas.columns]

estaciones = pd.read_csv('Datos/Limpio/estaciones_limpias.csv')
pos_lookup = {normalize(row['Nombre_Estacion']): (row['Longitud'], row['Latitud']) for index, row in estaciones.iterrows()}

# Cargar aristas del grafo completo
distancias = pd.read_csv('Datos/Limpio/distancias_reales.csv')
G_mexico = nx.Graph()

for index, row in distancias.iterrows():
    origen = row['Origen']
    destino = row['Destino']
    peso = row['Distancia']
    G_mexico.add_edge(origen, destino, weight=peso)

def heuristica_mexico(current, target):
    c_norm = get_normalized_name(current)
    t_norm = get_normalized_name(target)
    if c_norm in heuristicas.index and t_norm in heuristicas.columns:
        return float(heuristicas.at[c_norm, t_norm])
    else:
        return 0.0

def trayecto_optimo_distancia(origen, destino):
    try:
        camino = nx.astar_path(G_mexico, origen, destino, heuristic=heuristica_mexico, weight="weight")
        dist_total = nx.astar_path_length(G_mexico, origen, destino, heuristic=heuristica_mexico, weight="weight")
    except nx.NetworkXNoPath:
        return f"No se encontró camino entre {origen} y {destino}"
    except Exception as e:
        return f"Error al calcular camino: {e}"
    
    # Construir pos para el grafo actual
    pos = {}
    for node in G_mexico.nodes():
        norm_node = get_normalized_name(node)
        if norm_node in pos_lookup:
            pos[node] = pos_lookup[norm_node]
        else:
            print(f"Advertencia: No se encontró coordenadas para '{node}' (normalizado: '{norm_node}')")
            pos[node] = (0, 0) 

    # Visualización con Plotly
    edge_x = []
    edge_y = []
    for edge in G_mexico.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    node_text = []
    for node in G_mexico.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color='lightblue',
            size=10,
            line_width=2),
        text=node_text)

    # Resaltar el camino óptimo
    path_x = []
    path_y = []
    for i in range(len(camino) - 1):
        u, v = camino[i], camino[i+1]
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        path_x.append(x0)
        path_x.append(x1)
        path_x.append(None)
        path_y.append(y0)
        path_y.append(y1)
        path_y.append(None)
        
    path_trace = go.Scatter(
        x=path_x, y=path_y,
        line=dict(width=4, color='red'),
        hoverinfo='none',
        mode='lines',
        name='Ruta Óptima')

    # Nodos del camino óptimo para resaltarlos
    path_nodes_x = []
    path_nodes_y = []
    path_nodes_text = []
    for node in camino:
        x, y = pos[node]
        path_nodes_x.append(x)
        path_nodes_y.append(y)
        path_nodes_text.append(node)

    path_nodes_trace = go.Scatter(
        x=path_nodes_x, y=path_nodes_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            color='red',
            size=12,
            line_width=2),
        text=path_nodes_text,
        name='Estaciones Ruta')

    fig = go.Figure(data=[edge_trace, node_trace, path_trace, path_nodes_trace],
                layout=go.Layout(
                    title=dict(
                        text=f"Ruta óptima de {origen} a {destino} (Distancia: {dist_total:.2f})",
                        font=dict(size=16)
                    ),
                    showlegend=True,
                    hovermode='closest',
                    dragmode='pan',
                    margin=dict(b=20,l=5,r=5,t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
    fig.show()
    
    return f"El camino encontrado por A*:{camino}\nDistancia total: {dist_total}"

print(trayecto_optimo_distancia("Observatorio", "Eje Central"))