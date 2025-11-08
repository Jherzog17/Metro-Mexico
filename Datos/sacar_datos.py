import pandas as pd
import re
import copy
from geopy.distance import geodesic
import numpy as np

'''
Cargar csv de rutas en el cual se encuentra una columna que identifica los
distintos medios de transporte (metro, trolebus, etc). Filtrar por filas para
quedarme solo con que sean de metro
'''
routes = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/routes.txt")

routes = routes[routes["agency_id"] == "METRO"]#Filtrar por las filas que contengan sean metro
route_id = routes["route_id"].tolist() #Sacar las route_id que usaremos a continuación

'''
Cargar el csv de trips en el cual se encuentran los trips_id que servirán
para sacar luego las estaciones de metro y también para sacar los shape_id
que nos darán el camino exacto entre estaciones
'''
trips = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/trips.txt")
trips = trips[trips["route_id"].isin(route_id)]
trips = trips[trips["direction_id"] == 0]

trips_sin_duplicar = []
for elem in trips["trip_id"].to_list():
    elimn_dupl = re.match(r"\d{2}1.*", elem)
    if elimn_dupl is not None:
        trips_sin_duplicar.append(elem)

trips = trips[trips["trip_id"].isin(trips_sin_duplicar)]
trips_id = trips["trip_id"].tolist()
shape_id = trips["shape_id"].tolist()

'''
Cargar el csv de stop_times en el cual se encuentran los ids de las
estaciones que luego filtraremos en el csv de stops
'''

stops_times = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/stop_times.txt")
stops_times = stops_times[stops_times["trip_id"].isin(trips_id)]
stops_id = stops_times["stop_id"].tolist()  

'''
Cargar el csv que contiene todas las estaciones de metro con sus
coordenadas. Aquí unificar las que salen repetidas y obtener las 
coordenadas.
'''

stops = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/stops.txt")
stops = stops[stops["stop_id"].isin(stops_id)]
nombres_repes = stops["stop_name"].value_counts()
nombres_repes = nombres_repes[nombres_repes > 1]

new_stops = copy.copy(stops)#Copia del df
nuevas_lineas = ""
#For que recorre los nombre de las estaciones de más de una línea
for index in nombres_repes.index:
    filas = stops[stops["stop_name"] == index].copy() #Saca las filas de la estación repetida
    
    filas.drop(filas.index[0], inplace=True)#Quitamos la primera fila, ya que sobre esa fila solo vamos a cambiar el valor LineID por el nuevo
    
    #Borrar todas las otras filas que no queremos
    for inx in filas.index:
        new_stops.drop(inx, inplace=True)

new_stops = new_stops.reset_index(drop=True)#Reiniciar los index de las filas

new_stops.to_csv("Datos/Limpio/estaciones_limpias.csv", index=False)


'''
Cargar el csv de shapes en el cual se encuentran los recorridos
exactos entre estaciones, con ello sacaremos la distancia real
entre estaciones
'''

shapes = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/shapes.txt")
shapes = shapes[shapes["shape_id"].isin(shape_id)]

#Agrupar los shapes por línea
grupos = shapes.groupby("shape_id")
lista_shapes = []#Lista que contiene los distintas rutas exactas
for elem in shape_id:
    ruta = grupos.get_group(elem)
    lista_shapes.append(ruta)

#Ordenar la lista de los shapes para que vaya en orden
#Es decir, que primero esté la linea 1,luego la 2, etc
lista_shapes.insert(0, lista_shapes[9])
lista_shapes.insert(8, lista_shapes[12])
del lista_shapes[11]
del lista_shapes[12]


#Agrupar las estaciones por linea 
estaciones_por_linea = []
lineas = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "12"]
for linea in lineas:
    if linea == "12":
        pattrn = "020L12"
    else:
        pattrn = f"0200L{linea}"
    estacion = stops[stops["stop_id"].str.startswith(pattrn)]
    estaciones_por_linea.append(estacion)

def encontrar_coordenada_mas_cercana(estacion, coords_shape):
    '''
    Función que dados dos dfs, encuentra la latitud mas parecida que aparece
    en el df de las estaciones con respecto a las latitudes del df de shapes.
    Luego, coge la longitud asociada a esa latitud y devuelve una tupla con 
    las coordenadas que luego se podrán encontrar en el df de shapes 
    '''
    new_df = pd.DataFrame()
    lon = coords_shape["shape_pt_lon"].values
    lat = coords_shape["shape_pt_lat"].values

    matriz_dif = np.abs(estacion["stop_lon"].values[:,None]- np.array(lon) ) 

    indices_min = np.argmin(matriz_dif, axis=1)
    min_lon = np.array(lon)[indices_min]
    min_lat = np.array(lat)[indices_min]

    new_df["Nombre_Estacion"] = estacion["stop_name"].values
    new_df["Latitud"] = min_lat
    new_df["Longitud"] = min_lon
    return new_df


stops_df_new_coords = pd.DataFrame()
for i in range(len(estaciones_por_linea)):
    linea = []
    for k in range(len(estaciones_por_linea[i])):
        linea.append(lineas[i])
    estacion = estaciones_por_linea[i]
    coords = lista_shapes[i]
    nombre_y_coords = encontrar_coordenada_mas_cercana(estacion, coords)
    nombre_y_coords["Linea"] = linea
    stops_df_new_coords = pd.concat([stops_df_new_coords, nombre_y_coords])

stops_df_new_coords = stops_df_new_coords.reset_index(drop=True)

def unificar_estaciones_repetidas(stops_df_new_coords):
    nombres_repes = stops_df_new_coords["Nombre_Estacion"].value_counts()
    nombres_repes = nombres_repes[nombres_repes > 1]

    new_stops_df_new_coords = copy.copy(stops_df_new_coords)#Copia del df
    #For que recorre los nombre de las estaciones de más de una línea
    for index in nombres_repes.index:
        
        filas = stops_df_new_coords[stops_df_new_coords["Nombre_Estacion"] == index].copy() #Saca las filas de la estación repetida
        filas.drop(filas.index[0], inplace=True)#Quitamos la primera fila, ya que sobre esa fila solo vamos a cambiar el valor LineID por el nuevo
        #Borrar todas las otras filas que no queremos
        for inx in filas.index:
            new_stops_df_new_coords.drop(inx, inplace=True)

    new_stops_df_new_coords = new_stops_df_new_coords.reset_index(drop=True)
    return new_stops_df_new_coords
    
new_stops_df_new_coords = unificar_estaciones_repetidas(stops_df_new_coords)
new_stops_df_new_coords.to_csv("Datos/Limpio/estaciones_limpias_new_coords.csv", index=False)
