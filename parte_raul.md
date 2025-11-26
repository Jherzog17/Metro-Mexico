## Fichero de distancias de transbordos de mi parte
Esto lo redacto para saber mas o menos lo que voy haceindo yo tmb, no olivadrme, y sobretodo dejarlo bastante ya niquelado para la memoria 

### Objetivo
Para llevar a cabo el algoritmo A* de una manera mas realista y concreta, claramente hay que tener en cuenta el tiempo de los trasbordos, puesto que en algunos casos tienen una influencia bastante grande en términos de tiempo y por lo tanto en el algoritmo y resultado final.
Para eso he recapacitado datos de diversas fuentes, aunque como es de esperar, no todos los datos estan disponibles o son 100% precisos.
El csv esta compuesto por la distancia entre nodos en metros que como he dicho se utilizarán como pesos adicionales en el algoritmo A*, junto con las distancias reales entre estaciones consecutivas de la misma línea.

### Punto de partida

He partido de dos fuentes internas del proyecto
El fichero distancias_reales.csv, donde ya estaban definidas todas las aristas del grafo (Origen, Destino, Distancia, Línea) es decir que ya tenia las realciones entre estaciones (para saber que buscar realmente)  

A partir de ahí he obtenido la lista completa de transbordos que el grafo necesita (37 en total) y he trabajado siempre sobre esa lista, para asegurar que no falta ningun trasbordo del csv, es decir que los datos coincidan en todos los ficheros de datos


### Fuentes de información externas
Para asignar distancias reales o lo más aproximadas posibles he usado diferentes fuentes.

Datos procedentes del STC Metro publicados a través de artículos como ADN40, Sopitas, etc.  
Estos artículos indican longitudes exactas (en metros) y tiempos aproximados para los transbordos más importantes, es decir los que mas afectaran o los comparativos que afectan poco, como por ejemplo
Atlalilco (L8–L12) ≈ 881 m  
Pantitlán (L1–LA) ≈ 602 m  
Ermita (L2–L12) ≈ 585 m  
Jamaica (L4–L9) ≈ 384 m  
Candelaria (L1–L4) ≈ 353 m  
La Raza (L3–L5) ≈ 501 m  
Consulado (L4–L5) ≈ 488 m  
Instituto del Petróleo (L5–L6) ≈ 473 m  
San Lázaro (L1–LB) ≈ 411 m  
Oceanía (L5–LB) ≈ 59 m  
El Rosario (L6–L7) ≈ 37 m  
Bellas Artes (L2–L8) ≈ 72 m  

Para las estimaciones, es decir el resto de datos, que no existen datos exactos porque como ya he comentado, para muchos transbordos el STC solo publica tiempos (por ejemplo 3 minutos1) pero no metros, entonces con esto tambén se puede hacer una estimacion de los metros, para ello he usado una velocidad de una persona típica (que aplicaré para la próxima transformacion para que el algorimo A* pueda interpretar estos datos) y he codigo unos 80 metros por minuto, para asi pasar de minutos a metros
Por otro lado también he determinado los rangos razonables dependiendo del trnasborod  porque algunas fuentes solo inidicar una estimacion aproximada (que ya es mejor que nada),  como: corto (que he considerado entre 100–250 m), medio (250–400 m) y largo (400–600 m)

### Clasificación de los valores del CSV

En el CSV final he distinguido claramente tres tipos de valores (lo indico en el comentario de cada fila):

**Exacto**  
Son distancias que coinciden con valores publicados por el STC (vía ADN40, Sopitas, etc.).  

**Estimado**  
   Son transbordos de los que no existe dato público en metros, pero logicamente existen (porque salen en nuestros datos y en el mapa del metro).
   En estos casos he utilizado uno de estos criterios que ya he comentado (corto, medio o largo) o bien datos puntuales en los que solo indican el tiempo y hago una conversion aproximada
   Transbordos internos de Pantitlán sin dato oficial (L1–L5, L1–L9, L9–LA, L5–L9):  
   Aquí he usado valores altos (350–500 m) porque todas las fuentes coinciden en que Pantitlán es una de las estaciones más complejas y con pasillos largos, aunque no desglosen cada combinación de líneas.

En el propio CSV, los casos modificados o añadidos están marcados en el comentario para dejar claro qué viene de fuentes externas y que es aproximado etc

## Compatibilidad
Antes de cerrar el fichero he hecho dos comprobaciones importantes 
He comprobado que todos los transbordos que aparecen en el grafo original (distancias_reales.csv con distancia 0) tienen una fila correspondiente en el CSV de transbordos.


### Limitaciones
Aunque logicamente he intentado ser lo mas preciso posible, logicamente esta parte ha tendio ciertas limitaciones inevitables
aunque he intentado ser lo más riguroso posible, hay que dejar claro que logicamente solo una parte de los trasborods tienen un dato bastante preciso, y el resto estimaciones razonables basadas en descripciones cualitativas (transbordo muy largo / muy corto) rangos típicos para transbordos de metro y tiempos aproximados de caminata

## transformacion de los datos
Una vez he conseguido todos los datos sobre los trasbordos, hay que llevar a cabo una converison para que el algoritmo A* pueda interpretar los datos; he aqui el problema, que las distancias en el algoritmo A* se recorren siempre a una velocidad concreta, a la que se mueve el tren, es por ello que es necesario llevar a cabo dicha conversión. 
“Para compatibilizar los trasbordos (a 4,8 km/h) con el resto de las aristas (a 35 km/h) sin modificar el código del A*, se ha aplicado un factor de conversión 
vel del tren/ vel a pie = 35/4.8 ≈ 7,29
Con este factor de conversion bastante sencillo, las distancias de trasbordo se ‘inflan’ en el grafo, y el A* puede seguir trabajando como si todas las aristas se recorrieran a la velocidad del tren, pero el tiempo efectivo de los trasbordos queda representado correctamente.
Esto lo he hecho bascicamente primero realizando una funcion que se encargue del factor de converiosn, y posteriormente otras que recoja los dato sde las distancias reales de los trasbordos, los pase por la funcion de conversion y luego se devuelvan en un csv apto ya para procesar la información en el algoritmo A*  todo ello esta contenido en conversion_datos_trasbordos.py
Por lo tanto los datos relamente que haran falta a Alba e Irene son los que estan en la utlima columna del csv de distancias_trasborods_para_aestrella, en la columna de Coste_Aestrella

Por último he puesto los datos de distancias_rtasbordos_para_aestrella (concretamente la columna Coste_Aestrella) en el dataset inicial de distancias_reales_transbordos, con el fichero de aplicar_datos_trasbordos donde he filtrado primero que filas tenian un  0 en la distancia(es decir que eran un trasborod) y luego he sustituido cada valor correspondiente en base a la tabla que he realizado antes de las distancias de los trasbrodos para el algoritmo A*.

## Tiempo en entrada a estaciones
A estos datos y tiempo de trasbordo, también hay que añadirle otro dato, auque no tan considerable por su peso (en tiempo) en comparación por ejemplo de un trasborod largo o un trayecto en metro: el tiempo que tardan las personas en entrar en las estacion.
Al igual que para las distancias de los trasborodos, no existe  registro oficial público que cronometre este intervalo para cada estación, y de nuevo he optado por hacer una estimación basada en la ingeniería civil de la red, es decir, asumo que este tiempo extra varia según la profundidad física de la estación y su complejidad de trasborods y arquitectura.

Para hacer esta clasificaicon he extraido los datos principalmente de 4 fuentes:
Infraestructura del Sistema (STC Metro): 

https://metro.cdmx.gob.mx/la-red

Organismo Regulador de Transporte (ORT)

https://www.ort.cdmx.gob.mx

Artículo de investigación que citan datos del STC sobre la profundidad de estaciones

https://www.sopitas.com/noticias/estacion-linea-mas-profunda-metro-cdmx-bunker/

video Las 15 Interestaciones MÁS LARGAS del Metro CDMX.
https://www.youtube.com/watch?v=vIx_7eLZQ3g

Con ello he podido sacar mi clasificacion que consiste en, las estaciones superficiales (como en la Línea A) en las que les he puesto  un tiempo mínimo de 1.5 minutos por su acceso directo. Por otro lado, las estaciones elevadas y las subterráneas estándar (construidas a cielo abierto) que les he asignado  tiempos de entre 2.5 y 3.5 minutos y otras estaciones que tienen un extra, las de "túnel profundo (Línea 7 y tramo oeste de la Línea 12) y a los Centros de transferencia m odal (CETRAM).
Tambien he de comentar que he asignado el tiempo basándome en la línea más profunda o compleja de ese grupo (por ejemplo, en Tacubaya, aunque la L1 es superficial, la entrada se le pone tiempo por la L7 que es profunda).

Finalmente una vez con toda la informacion lo he juntado en un csv, adjuntando cada estaion con su correspondiente tiempo de entrada aproxiamdo.

