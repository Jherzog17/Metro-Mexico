import pandas as pd
from geopy.distance import geodesic
import numpy as np
from pathlib import Path

# Obtener la ruta raíz del proyecto
directorio_root = Path(__file__).parent.parent

posibles_estaciones = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "12"]

#Las distintas columnas del dataframe final
origen = []
destino = []
dist = []
linea = []

'''
Por cada linea de metro hemos sacado su ruta real a base de ir consiguiendo
distancia entre un punto de shape y su contiguo y sumandolos asi hasta encontrar
una estación de metro
'''
for lin in posibles_estaciones:
    estacion = pd.read_csv(directorio_root / f"Datos/Limpio/Estaciones/estacion_{lin}.csv")
    shape = pd.read_csv(directorio_root / f"Datos/Limpio/Shapes/shape_linea_{lin}.csv")
    
    #Coge solámente los datos de la línea correspondiente
    for i in range(len(estacion)-1):
        #nombres de origbne y destino
        nombre_org = estacion.iloc[i]["Nombre_Estacion"].strip() + f"_L{lin}"
        nombre_dest = estacion.iloc[i+1]["Nombre_Estacion"].strip() + f"_L{lin}"

        #Cojo el segmento que es un conjunto de puntos entre una línea y la siguiente
        #El conjunto de puntos se guarda en tramo
        inx_inicio = shape[shape["shape_pt_sequence"] == estacion.iloc[i]["Sequence"]].index[0]
        inx_final = shape[shape["shape_pt_sequence"] == estacion.iloc[i+1]["Sequence"]].index[0]
        if inx_inicio < inx_final:
            tramo = shape.iloc[inx_inicio:inx_final+1]
        else:
            tramo = shape.iloc[inx_final:inx_inicio+1]
        
        #Cada segmento esta formado por un conjunto de puntos, pues la distancia será la suma de las distancias entre los puntos
        distancia_total = 0.0
        for i in range(len(tramo)-1):
            distancia = geodesic( (tramo.iloc[i]["shape_pt_lat"], tramo.iloc[i]["shape_pt_lon"]),
                                 (tramo.iloc[i+1]["shape_pt_lat"], tramo.iloc[i+1]["shape_pt_lon"]) ).meters
            distancia_total += distancia

        #Anñadir los valores al data frame final
        origen.append(nombre_org)
        destino.append(nombre_dest)
        dist.append(distancia_total)
        linea.append(lin)

#Creo un diccionario para posteriormente crear un dataframe
datos = {"Origen": origen, "Destino": destino, "Distancia": dist, "Linea":linea}
df_dist_real = pd.DataFrame(datos)#Data frame final

# Guardar el archivo original sin transbordos
df_dist_real.to_csv(directorio_root / "Datos/Limpio/distancias_reales.csv", index=False)

#Obtener transbordos

estaciones_unicas = pd.concat([df_dist_real['Origen'], df_dist_real['Destino']]).unique()

# Agrupar estaciones por su nombre sin la linea es decir, sin el _L1,2,3 etc
estaciones_por_nombre = {} #Este diccionario tendrá las estaciones como clave y como valor sus estaciones mas linea por ejemplo Pantitlan: [Pantitlan_L1, Pantitlan_L5] etc
for nombre_completo in estaciones_unicas:

    # Buscamos el último guion bajo para separar nombre y línea
    if "_" in nombre_completo:
        nombre_base = nombre_completo.rsplit("_", 1)[0]
        if nombre_base not in estaciones_por_nombre:
            estaciones_por_nombre[nombre_base] = []
        estaciones_por_nombre[nombre_base].append(nombre_completo)

# Listas para las nuevas filas
origen_trans = []
destino_trans = []
dist_trans = []
linea_trans = []

# Recorre las estaciones y se fija en las que tienen mas de una conexión
for nombre_base in estaciones_por_nombre:
    nodos = estaciones_por_nombre[nombre_base]#Lista con todas las lineas asociadas
    if len(nodos) > 1:
        #Bucle por cada conexión que haya
        for i in range(len(nodos)):
            #Conecta esa conexión con todas las demas que haya
            for j in range(i + 1, len(nodos)):
                nodo_a = nodos[i]
                nodo_b = nodos[j]
                
                origen_trans.append(nodo_a)
                destino_trans.append(nodo_b)
                dist_trans.append(np.nan)# Luego meteremos las distancias a mano
                
                # Sacar las líneas
                linea_a = nodo_a.split("_L")[-1]
                linea_b = nodo_b.split("_L")[-1]
                
                lineas = sorted([linea_a, linea_b])#Pone las lineas en orden
                linea_trans.append(f"{lineas[0]}-{lineas[1]}")

# Crear df de transbordos 
df_transbordos = pd.DataFrame({
    "Origen": origen_trans,
    "Destino": destino_trans,
    "Distancia": dist_trans,
    "Linea": linea_trans
})

#Unir el df al original
df_dist_real_transbordos = pd.concat([df_dist_real, df_transbordos], ignore_index=True)

# Guardar el archivo con transbordos
df_dist_real_transbordos.to_csv(directorio_root / "Datos/Limpio/distancias_reales_transbordos.csv", index=False)

#--------Para hacer Raul---------------
#Añadir las distancias a entre los distintos transbordos