# Practica Metro de Mexico

Esta info luego se quita pero es para llevar registro de las cosas que he ido haciendo y no se olviden luego
### Jorge, cosas que he ido haciendo


estaciones_separaciones.txt salido https://github.com/IgorEM/Melhor-Rota---Metro-da-cidade-do-Mexico---Dijkstra-/blob/main/183arestasOrigDestPesoVirgulasSemEspacoNaoDirecional.txt, corroborada la información con https://metro.cdmx.gob.mx/longitud-de-estacion


## Sacar estaciones, tabla heurísticas y distancias reales
Primero me he descargado un zip con todos los datos relevantes al tranporte en ciudad de mexico, https://www.transit.land/feeds/f-9g3-semovi

Dentro de este zip hay varios archivos y prodeceré del siguiente modo:

1.-Routes.txt: Aquí aparece una columna llamada route_type que da el tipo de transporte, Bus, Metrobus, Metro etc, el metro == 1, asi que saco todos los relacionados con el metro y que quedo con la columna route_id

2.-Trips.txt: Aquí me voy quedar con los viajes del route_id encontrados previamente y me quedaré con sus trip_id.

3.-Stop_times.txt: Aquí partiendo de los trip_id, saco los stop_id que son las estaciones de metro.

4.-Stops.txt: Me quedo con los stops_id y ya tengo el csv solo con las paradas de metro, aqui tenog tambien sus coordenadas

5.- Una vez que tengo las estaciones, las estaciones que tienen varias lineas aparecenb varias veces por lo que las he fusionado en una sola fila. Por último he guardado el csv en estaciones_limpias.csv. 

## Tabla de las heurísticas a partir de las estaciones
Luego he creado la tabla de las heurísticas a partir del csv limpio. En esa tabla cada fila, es una estación y cada columna es una estación. Los valores de la tabla son las distancia en línea recta de un lugar a otro, esto luego se puede utilizar en el algoritmo A*. Para hallar la distancia en linea recta partía de coordenadas asi que he utlizado la librería geopy para ello utilizando la función geodesic, que es mucho más precisa que utilizar la funcion haversiana o como se diga. He guardado la tabla en un csv pero es **MUY IMPORTANTE que al importar la tabla de heuristicas hacerlo con esta opcion pd.read_csv("Ruta", index_col="Unnamed: 0"), esto es lo importante: index_col="Unnamed: 0"**

## Para las rutas exactas

1.- Partiendo de del los trips_id, estos tienen asociado un shape_id en el archivo trips.txt

2.- Partiendo de estos shape_id puedo sacar la ruta exacta

Los shapes copntienen la ruta excta de un extremo de la linea al otro extremo, es por ello que lo que he hecho es primero dividir las estaciones por linea y los shapes tambié por línea. Luego encontrar la coordenada más parecida del shape con la estación correspondiente y tomarla como punto de incio. Hacer lo mismo con la estación destino y calcular la distancia entre ambas


