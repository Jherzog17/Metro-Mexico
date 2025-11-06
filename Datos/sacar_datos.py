import pandas as pd
import re
import copy

'''
Cargar csv de rutas en el cual se encuentra una columna que identifica los
distintos medios de transporte (metro, trolebus, etc). Filtrar por filas para
quedarme solo con que sean de metro
'''
routes = pd.read_csv("Datos/Crudo/f-9g3-semovi-latest/routes.txt")

routes = routes[routes["agency_id"] == "METRO"]#Filtro por las filas que contengan sean metro
route_id = routes["route_id"].tolist() #Saco lso route_id que usaré a continuación

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

'''
Cargar el csv de stop_times en el cual se encuentran los ids de las
estaciones que luego filtraré en el csv de stops
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
    
    filas.drop(filas.index[0], inplace=True)#Quito la primera fila, ya que sobre esa fila solo voy a cambiar el valor LineID por el nuevo
    
    #Borra todas las otras filas que no queremos
    for inx in filas.index:
        new_stops.drop(inx, inplace=True)

new_stops = new_stops.reset_index(drop=True)#Reiniciar los index de las filas

new_stops.to_csv("Datos/Limpio/estaciones_limpias.csv", index=False)
