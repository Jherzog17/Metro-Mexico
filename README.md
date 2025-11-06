# Practica Metro de Mexico

Esta info luego se quita pero es para llevar registro de las cosas que he ido haciendo y no se olviden luego
### Jorge, cosas que he ido haciendo

He limpiado el csv, metro_stations.csv uniendo las estaciones que aparecen varias veces porque tienen varias lineas en uno solo con todas esas lineas, todo esto utilizando pandas. Luego he creado la tabla de las heurísticas a partir del csv limpio. En esa tabla cada fila, es una estación y cada columna es una estación. Los valores de la tabla son las distancia en línea recta de un lugar a otro, esto luego se puede utilizar en el algoritmo A*. Para hallar la distancia en linea recta partía de coordenadas asi que he utlizado la librería geopy para ello utilizando la función geodesic, que es mucho más precisa que utilizar la funcion haversiana o como se diga. He guardado la tabla en un csv pero es **MUY IMPORTANTE que al importar la tabla de heuristicas hacerlo con esta opcion pd.read_csv("Ruta", index_col="Unnamed: 0"), esto es lo importante: index_col="Unnamed: 0"**

metro_stations.csv salido de https://datos.cdmx.gob.mx/gl/dataset/lineas-y-estaciones-del-metro/resource/0869e0dd-6876-4446-a199-8f670a359c00

estaciones_separaciones.txt salido https://github.com/IgorEM/Melhor-Rota---Metro-da-cidade-do-Mexico---Dijkstra-/blob/main/183arestasOrigDestPesoVirgulasSemEspacoNaoDirecional.txt, corroborada la información con https://metro.cdmx.gob.mx/longitud-de-estacion