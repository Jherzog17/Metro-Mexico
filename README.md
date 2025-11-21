# Practica Metro de Mexico

Esta info luego se quita pero es para llevar registro de las cosas que he ido haciendo y no se olviden luego
### Jorge, cosas que he ido haciendo


estaciones_separaciones.txt salido https://github.com/IgorEM/Melhor-Rota---Metro-da-cidade-do-Mexico---Dijkstra-/blob/main/183arestasOrigDestPesoVirgulasSemEspacoNaoDirecional.txt, corroborada la información con https://metro.cdmx.gob.mx/longitud-de-estacion


## Sacar estaciones, tabla heurísticas y distancias reales

### Sacar estaciones juntos otros datos

Primero me he descargado un zip con todos los datos relevantes al tranporte en ciudad de mexico, https://www.transit.land/feeds/f-9g3-semovi

Dentro de este zip hay varios archivos y prodeceré del siguiente modo:

1.-Routes.txt: Aquí aparece una columna llamada route_type que da el tipo de transporte, Bus, Metrobus, Metro etc, el metro == 1, asi que saco todos los relacionados con el metro y que quedo con la columna route_id

2.-Trips.txt: Aquí me voy quedar con los viajes del route_id encontrados previamente y me quedaré con sus trip_id.

3.-Stop_times.txt: Aquí partiendo de los trip_id, saco los stop_id que son las estaciones de metro.

4.-Hay dos archivos, el archivo de stops.txt que contiene las estaciones con sus coordenadas y el archivo de shapes.txt que contiene una secuencia de puntos(o coordenadas)que equivalen al recorrido exacto del metro. El problema, la única forma de relacionar ambos archivos es mediante coordenadas y no coinciden excactamente, por lo que hay un problema. Antes de seguri, ¿por que esto es necesario?. Bueno con el archivo de shapes.txt yo puedo sacar el recorrido exacto de un extremo a otro extremo, sin embargo no se donde se situan las paradas y sin las paradas, no puedo sacar la distancia entre paradas(los pesos del grafo). Solución: relacionar ambos csv como se pueda. Lo que he hecho es buscar los puntos más cercanos dentro de shapes con respecto a las estaciones(archivo de stops.txt). Posteriormente, tomar como valor real de ubicación de la parada de metro esa coordenada más similar a la real dentro de shape. Esto, no es la ubicación excta de la parada de metro, pero es una ubicación muy  cercana(el error es bajo), y es la única manera que se me ha ocurrido de unir por así decirlo ambos csv.

5.-A partir de esas nuevas coordenadas y más info como la línea a la que pertenece, la secuencia(en shapes) y el id que lo identifica en shapes, he creado el csv con todas las estaciones(estaciones_limpias.csv)



### Tabla de las heurísticas a partir de las estaciones
A partir de estaciones_limpias.csv, he creado un script que saca un dataframe con las distancias en línea recta de una estación a otra, es decir, las heurísticas. Para crear este script primero he creado un data frame con las dimensiones necesarias(creo que 163x163) con valores por defecto(0.0), para luego ir fila por fila y columna por columna sustituyendo el valor por la distancia. Para calcular la distancia he utilizado una librería llamada geopy, utilizando su función geodisic que a partir de dos puntos te saca la distancia en metros, bueno la saca en km creo pero yo las he puesto en metros. He guardado la tabla en un csv pero es **MUY IMPORTANTE que al importar la tabla de heuristicas hacerlo con esta opción pd.read_csv("Ruta", index_col="Unnamed: 0"), esto es lo importante: index_col="Unnamed: 0"**. Esto es pq los index del dataset son los nombres de las estaciones y al guardarlo a csv, esos index pasan a ser una columna,  y por tanto, al abrirlo hay que especificar que quieres que esa primera columna sean los indices

### Distancias reales
En este apartado, he sacado la distancia real(pesos del grafo), entre dos estaciones contiguas. Para ello he partido de los csv que hay en las carpetas Limpio/Estaciones y Limpio/Shapes, aquí se encuentran los datos de cada estación individual y la ruta excta de cada estación individual. Para lograr esto primero he identificado el conjunto de puntos que conforman la ruta entre una estación y otra. Por ejemplo, si tengo 200 puntos que conforman la línea entera(de extremo a extremo), de la estación 1 a la 2 quiza coge 15 puntos, de la 2 a la 3, 20 puntos, etc. Una vez tengo esos datos calculo la distancia entre un punto y su contiguo y asi sucesivamente. Voy acumulando esos valores y me da la distancia entre una estación y otra. Posteriormente guardo todos los datos en el csv de distancias_reales.csv

## Sacar distancia y tiempos de transbordos

Datos obtenidos de https://www.adn40.mx/ciudad/2025-10-13/lista-los-transbordos-del-metro-cdmx-y-cuanto-miden

-Atlalilco: 881 metros, 20 minutos
-Pantitlan: 602 metros, 14 minutos
-Ermita: 585 metros, 14 minutos
-Jamaica: 384 m, 9 min
