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


#Csv con las paradas
stops = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/stops.txt")
stops = stops[stops["stop_id"].isin(stops_id)]

'''
Cargar el csv de shapes en el cual se encuentran los recorridos
exactos entre estaciones, con ello sacaremos la distancia real
entre estaciones
'''

lineas = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "12"]

#Csv que contiene los recorridos exactos de las líneas
shapes = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/shapes.txt")
shapes = shapes[shapes["shape_id"].isin(shape_id)]

#Dividir los recorridos por líneade metro
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

#Guardo las distintas rutas en distintos csv para luego poder ir ruta por ruta
for i in range(len(lista_shapes)):
    lista_shapes[i].to_csv(f"Datos/Limpio/Shapes/shape_linea_{lineas[i]}.csv", index=False)

#Dividir las estaciones por linea de metro
estaciones_por_linea = []
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
    las coordenadas que luego se podrán encontrar en el df de shapes.
    '''
    new_df = pd.DataFrame()#Data frame final con los datos recopilados
    
    #Creo una lista que contendrá como tupla las coordenadas de los puntos de shapes
    puntos_shapes = []
    for i in range(len(coords_shape)):
        puntos_shapes.append( (coords_shape.iloc[i]["shape_pt_lat"], coords_shape.iloc[i]["shape_pt_lon"]) )

    #Creo una lista que contendrá como tupla las coordenadas de las estaciones de estaciones(el csv)
    puntos_estaciones = []
    for i in range(len(estacion)):
        puntos_estaciones.append( (estacion.iloc[i]["stop_lat"], estacion.iloc[i]["stop_lon"]) )

    matriz_distancias = np.zeros((len(puntos_estaciones), len(puntos_shapes)))#Matriz que contendrá la diferencia de distancias
    #Calcula la distancia entre la estación y los puntos de shape
    for i in range(len(puntos_estaciones)):
        origen = puntos_estaciones[i]
        for j in range(len(puntos_shapes)):
            destino = puntos_shapes[j]
            distancia = geodesic(origen, destino).meters
            matriz_distancias[i][j] = distancia

    indices_min = np.argmin(matriz_distancias, axis=1)#Me quedo con los indices en los que se encuentran los puntos de shapes más cercanos a las estaciones
    todas_filas = coords_shape.iloc[indices_min]#Me quedo solo con las filas en las que están los puntos cercanos

    #Añado la información al dataset final
    new_df["Nombre_Estacion"] = estacion["stop_name"].values
    new_df["Latitud"] = todas_filas["shape_pt_lat"].values
    new_df["Longitud"] =todas_filas["shape_pt_lon"].values
    new_df["Sequence"] = todas_filas["shape_pt_sequence"].values
    new_df["ID"] = todas_filas["shape_id"].values
    return new_df


stops_df_new_coords = pd.DataFrame()#Dataframe con todas las estaciones y sus coordenadas equivalente en shapes
#For que recorre todos los data frames de las estaciones por línea, es decir, df linea 1, luego df línea2 ,etc
for i in range(len(estaciones_por_linea)):
    #Una lista con la linea repetida tantas veces como elementos, esto es para que luego al añadirlo al df no  de errores
    linea = []
    for k in range(len(estaciones_por_linea[i])):
        linea.append(lineas[i])

    estacion = estaciones_por_linea[i]#df de la estacion
    coords = lista_shapes[i]#df del shape correspondiente a la estación

    nombre_y_coords = encontrar_coordenada_mas_cercana(estacion, coords)#df que devuelve las estaciones con las coordenadas de shape más parecidas a la de la estación
    nombre_y_coords["Linea"] = linea #Añado la linea al df

    nombre_y_coords.to_csv(f"Datos/Limpio/Estaciones/estacion_{linea[0]}.csv", index=False)#Guardo la info de la línea
    stops_df_new_coords = pd.concat([stops_df_new_coords, nombre_y_coords])#Lo unifico para tener en otro df todas las estaciones(el df de estaciones limpias)

stops_df_new_coords = stops_df_new_coords.reset_index(drop=True)#Ya que cada uno tenían sus índices, los reinicio para que se asignen nuevos

def unificar_estaciones_repetidas(stops_df_new_coords):
    ''''
    Función que dado el dataframe de las estaciones con las estaciones que tienen varias lineas
    repetidas, las unifica en una sola fila, poniendo en la columna Linea todas las lineas. Además,
    también guarda las lineas a las que pertenece como su secuencia y su id en shapes para que al 
    buscar el camino exacto, dependiendo de la linea se pueda encontrar.
    '''
    #Me quedo con las estaciones que aparecen mas de una vez
    nombres_repes = stops_df_new_coords["Nombre_Estacion"].value_counts()
    nombres_repes = nombres_repes[nombres_repes > 1]

    new_stops_df_new_coords = copy.copy(stops_df_new_coords)#Copia del df

    #For que recorre los nombre de las estaciones de más de una línea
    for index in nombres_repes.index:

        #Transformo la columna Sequence a str porque voy a tener varias secuencias en alguno(Los que tienen varais lineas)
        stops_df_new_coords["Sequence"] = stops_df_new_coords["Sequence"].astype(str)
        new_stops_df_new_coords["Sequence"] = new_stops_df_new_coords["Sequence"].astype(str)

        filas = stops_df_new_coords[stops_df_new_coords["Nombre_Estacion"] == index].copy() #Saca las filas de la estación repetida
        
        #Transformar a lista para que sea más fácil trabajar
        lineas = filas["Linea"].tolist()
        secuencias = filas["Sequence"].tolist()
        ids = filas["ID"].tolist()
        #Variables donde van a ir los valores finales
        todas_lineas = ""
        todas_secuencias = ""   
        todos_ids = ""
        #Por cada elemento repetido, los une en uno solo
        for i in range(len(lineas)):
            todas_lineas += lineas[i] + ","
            todas_secuencias += secuencias[i] + ","
            todos_ids += ids[i] + ","

        #Sustituye los valores antiguos por los nuevos
        new_stops_df_new_coords.loc[filas.index[0], "Linea"] = todas_lineas[:-1]
        new_stops_df_new_coords.loc[filas.index[0], "Sequence"] = todas_secuencias[:-1]
        new_stops_df_new_coords.loc[filas.index[0], "ID"] = todos_ids[:-1]

        filas.drop(filas.index[0], inplace=True)#Quitamos la primera fila ya que solo nos queremos quedar con una ocurrencia
        #Borrar todas las otras filas que no queremos
        for inx in filas.index:
            new_stops_df_new_coords.drop(inx, inplace=True)

    new_stops_df_new_coords = new_stops_df_new_coords.reset_index(drop=True)#Al haber borrado elementos vuelvo a reiniciar los índices para que todo se ajuste
    return new_stops_df_new_coords
    
new_stops_df_new_coords = unificar_estaciones_repetidas(stops_df_new_coords)
new_stops_df_new_coords.to_csv("Datos/Limpio/estaciones_limpias.csv", index=False)#Guardar el csv con todas las estaciones limpias

