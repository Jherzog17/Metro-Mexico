import pandas as pd
from geopy.distance import geodesic

df = pd.read_csv("Datos/Limpio/metro_stations_clean.csv")

#Creo el dataframe donde voy a guardar todos los datos
estaciones = {}
lista_vacia = [0]*len(df)
for est in df["Name"]:
    estaciones[est] = lista_vacia

tabla_heuristicas = pd.DataFrame(estaciones, index=estaciones.keys())

#Vamos rellenando la información por filas
for inx_origen in df.index:
    origen = (df.loc[inx_origen, "Lat"], df.loc[inx_origen, "Lng"])#Coordenadas de la estación de la fila
    #Recorro todas las columnas
    for inx_dest in df.index:
        destino = (df.loc[inx_dest, "Lat"], df.loc[inx_dest, "Lng"])#Coordenadas de la estación columna
        linea_recta = geodesic(origen, destino)#Función que da la distancia en línea recta entre coordenadas
        tabla_heuristicas.loc[df.loc[inx_origen, "Name"],df.loc[inx_dest, "Name"]] = linea_recta.meters #Añadir a la tabla

tabla_heuristicas.to_csv("Datos/Limpio/tabla_heuristicas.csv")#Guardar la tabla con las heurísticas