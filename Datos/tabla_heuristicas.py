import pandas as pd
from geopy.distance import geodesic

df = pd.read_csv("Datos/Limpio/estaciones_limpias.csv")

#Creo el dataframe donde voy a guardar todos los datos
estaciones = {}
lista_vacia = [0.0]*len(df)
for est in df["stop_name"]:
    estaciones[est] = lista_vacia

tabla_heuristicas = pd.DataFrame(estaciones, index=estaciones.keys())

#Vamos rellenando la información por filas
for inx_origen in df.index:
    origen = (df.loc[inx_origen, "stop_lat"], df.loc[inx_origen, "stop_lon"])#Coordenadas de la estación de la fila
    #Recorro todas las columnas
    for inx_dest in df.index:
        destino = (df.loc[inx_dest, "stop_lat"], df.loc[inx_dest, "stop_lon"])#Coordenadas de la estación columna
        linea_recta = geodesic(origen, destino)#Función que da la distancia en línea recta entre coordenadas
        tabla_heuristicas.loc[df.loc[inx_origen, "stop_name"],df.loc[inx_dest, "stop_name"]] = linea_recta.meters #Añadir a la tabla

tabla_heuristicas.to_csv("Datos/Limpio/tabla_heuristicas.csv")#Guardar la tabla con las heurísticas