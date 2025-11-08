import pandas as pd
from geopy.distance import geodesic

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
    estacion = pd.read_csv(f"Datos/Limpio/Estaciones/estacion_{lin}.csv")
    shape = pd.read_csv(f"Datos/Limpio/Shapes/shape_linea_{lin}.csv")
    
    #Coge solámente los datos de la línea correspondiente
    for i in range(len(estacion)-1):
        #nombres de origbne y destino
        nombre_org = estacion.iloc[i]["Nombre_Estacion"]
        nombre_dest = estacion.iloc[i+1]["Nombre_Estacion"]

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

df_dist_real.to_csv("Datos/Limpio/distancias_reales.csv", index=False)