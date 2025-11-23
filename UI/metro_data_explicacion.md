# Explicación Detallada de metro_data.py (Versión Actualizada)

## Descripción General

`metro_data.py` es un módulo adaptador que conecta la interfaz gráfica (`interfaz_epica.py`) con el algoritmo A* implementado en `aestrella.py`. Su función principal es:
1. Cargar coordenadas de estaciones para visualización
2. Crear mapeos entre nombres simples y nombres con línea
3. Delegar el cálculo de rutas a `aestrella.py`

**Filosofía de diseño:** No duplicar código. Reutilizar el grafo y algoritmo ya implementados en `aestrella.py`.

---

## Imports

```python
import sys
from pathlib import Path
import pandas as pd

# Añadir el directorio padre al path para poder importar aestrella
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar funciones de aestrella.py
from aestrella import G_mexico, heuristica_mexico, trayecto_optimo_distancia, heuristicas
```

### Explicación de Imports

- **`sys.path.insert(0, ...)`**: Añade el directorio raíz del proyecto al path de Python
  - Permite importar `aestrella.py` que está en la raíz
  - `Path(__file__).parent.parent`: Sube dos niveles desde `UI/metro_data.py` → raíz

- **Imports desde aestrella.py:**
  - **`G_mexico`**: Grafo NetworkX ya construido con todas las conexiones del metro
  - **`heuristica_mexico`**: Función que calcula valores heurísticos
  - **`trayecto_optimo_distancia`**: Función que ejecuta A* y retorna ruta completa
  - **`heuristicas`**: DataFrame con la tabla de heurísticas precalculadas

**Ventaja:** No reconstruimos el grafo ni recargamos las heurísticas. Todo ya está en memoria.

---

## Constantes de Configuración

```python
SCALE_FACTOR = 30000
OFFSET_X = 0
OFFSET_Y = 0
```

Estas constantes se usan para **convertir coordenadas GPS a píxeles** para la visualización del mapa.

- **`SCALE_FACTOR`**: Amplifica las diferencias entre coordenadas GPS
- **`OFFSET_X` y `OFFSET_Y`**: Desplazamiento (actualmente 0)

---

## Función 1: `cargar_datos()`

### Propósito
Carga coordenadas de estaciones y construye mapeos de nombres. **NO construye el grafo** (ya existe en `aestrella.py`).

### Código con Explicaciones

```python
def cargar_datos():
    """
    Carga todos los datos necesarios desde los archivos CSV.
    Usa el grafo G_mexico y la tabla de heurísticas ya cargados en aestrella.py.
    
    Returns:
        tuple: (stations_list, stations_xy, edges_list, graph, heuristics_df, 
                station_mapping, reverse_mapping)
    """
```

---

#### Paso 1: Ruta a los archivos CSV

```python
    # Ruta base a los archivos CSV (partiendo desde la raíz del proyecto)
    directorio_root = Path(__file__).parent.parent / "Datos" / "Limpio"
```

**Explicación:**
- `Path(__file__)`: Ubicación de `metro_data.py` → `UI/metro_data.py`
- `.parent.parent`: Sube dos niveles → raíz del proyecto
- `/ "Datos" / "Limpio"`: Navega a la carpeta de datos limpios

**Resultado:** Ruta absoluta que funciona desde cualquier directorio de ejecución.

---

#### Paso 2: Cargar coordenadas de estaciones

```python
    # 1. Cargar estaciones (coordenadas)
    df_stations = pd.read_csv(directorio_root / "estaciones_limpias.csv")
    
    # Centrar el mapa
    mean_lat = df_stations["Latitud"].mean()
    mean_lon = df_stations["Longitud"].mean()
```

**¿Por qué cargar esto si ya está en aestrella.py?**
- `aestrella.py` solo carga el grafo y heurísticas
- **NO** carga las coordenadas GPS necesarias para dibujar el mapa
- La UI necesita las coordenadas en píxeles para visualización

---

```python
    # Diccionario de coordenadas en píxeles
    stations_xy = {}
    for _, row in df_stations.iterrows():
        name = row["Nombre_Estacion"].strip()
        lat = row["Latitud"]
        lon = row["Longitud"]
        
        # Convertir GPS a píxeles
        px = (lon - mean_lon) * SCALE_FACTOR + OFFSET_X
        py = -(lat - mean_lat) * SCALE_FACTOR + OFFSET_Y
        stations_xy[name] = (px, py)
```

**Conversión GPS → Píxeles:**
1. Resta el promedio para centrar el mapa
2. Multiplica por `SCALE_FACTOR` (30000) para escalar
3. **Nota el `-` en `py`**: Invierte el eje Y (en pantalla Y crece hacia abajo)

**Resultado:** `{"Observatorio": (150.5, 230.8), ...}`

---

#### Paso 3: Construir mapeos de nombres

```python
    # 2. Cargar conexiones (para construir mapeos y edges_list)
    df_edges = pd.read_csv(directorio_root / "distancias_reales_transbordos.csv")
    
    edges_list = []
    station_mapping = {}  # nombre simple -> [nombres con línea]
    reverse_mapping = {}  # nombre con línea -> nombre simple
```

**¿Por qué cargar las conexiones si ya están en G_mexico?**
- Necesitamos construir los **mapeos de nombres**
- `G_mexico` usa nombres con línea ("Observatorio_L1")
- La UI muestra nombres simples ("Observatorio")
- Necesitamos traducir entre ambos formatos

---

```python
    for _, row in df_edges.iterrows():
        u = row["Origen"].strip()
        v = row["Destino"].strip()
        
        # Extraer nombres simples
        u_simple = u.split("_L")[0] if "_L" in u else u
        v_simple = v.split("_L")[0] if "_L" in v else v
```

**Extracción de nombres:**
- "Observatorio_L1" → `split("_L")[0]` → "Observatorio"
- "Tacubaya_L7" → "Tacubaya"

---

```python
        # Construir mapeos
        if u_simple not in station_mapping:
            station_mapping[u_simple] = []
        if u not in station_mapping[u_simple]:
            station_mapping[u_simple].append(u)
        reverse_mapping[u] = u_simple
        
        # (Lo mismo para v_simple y v)
```

**Construcción de mapeos:**

**`station_mapping`**: Nombre simple → Lista de nombres con línea
```python
{
    "Observatorio": ["Observatorio_L1", "Observatorio_L7"],
    "Pantitlán": ["Pantitlán_L1", "Pantitlán_L5", "Pantitlán_L9", "Pantitlán_LA"]
}
```

**`reverse_mapping`**: Nombre con línea → Nombre simple
```python
{
    "Observatorio_L1": "Observatorio",
    "Observatorio_L7": "Observatorio",
    "Pantitlán_L1": "Pantitlán",
    ...
}
```

**¿Por qué necesitamos esto?**
- Algunas estaciones tienen múltiples líneas
- Al calcular rutas, probamos todas las combinaciones
- Luego convertimos el resultado a nombres simples para mostrar en UI

---

```python
        # Lista de aristas para UI (sin duplicados)
        edge_ui = (u_simple, v_simple)
        if edge_ui not in edges_list and (v_simple, u_simple) not in edges_list:
            edges_list.append(edge_ui)
```

**Lista de aristas para dibujar:**
- Usa nombres simples
- Evita duplicados (no añade si ya existe en orden inverso)
- Solo para visualización en el mapa

---

#### Paso 4: Retornar datos

```python
    # Lista de estaciones ordenada
    stations_list = sorted(list(stations_xy.keys()))
    
    # Usar el grafo y heurísticas de aestrella.py
    return stations_list, stations_xy, edges_list, G_mexico, heuristicas, station_mapping, reverse_mapping
```

**Retorna 7 elementos:**
1. **`stations_list`**: Lista ordenada de nombres (para dropdowns)
2. **`stations_xy`**: Coordenadas en píxeles (para dibujar mapa)
3. **`edges_list`**: Conexiones para dibujar (nombres simples)
4. **`G_mexico`**: Grafo de aestrella.py (para A*)
5. **`heuristicas`**: Tabla de aestrella.py (para A*)
6. **`station_mapping`**: Mapeo simple → con línea
7. **`reverse_mapping`**: Mapeo con línea → simple

**Importante:** No creamos un nuevo grafo. Reutilizamos `G_mexico` de `aestrella.py`.

---

## Función 2: `obtener_heuristica()`

### Propósito
Delega a la función `heuristica_mexico` de `aestrella.py`.

### Código

```python
def obtener_heuristica(current, target, heuristics_df):
    """
    Obtiene el valor heurístico entre dos estaciones.
    Usa la función heuristica_mexico de aestrella.py.
    
    Args:
        current: Estación actual (puede tener sufijo _L)
        target: Estación objetivo (puede tener sufijo _L)
        heuristics_df: DataFrame con la tabla de heurísticas (no se usa, se mantiene por compatibilidad)
    
    Returns:
        float: Valor heurístico
    """
    # Usar la función de aestrella.py
    return heuristica_mexico(current, target)
```

**Explicación:**
- **Función wrapper**: Solo llama a `heuristica_mexico` de `aestrella.py`
- **`heuristics_df` no se usa**: Se mantiene el parámetro por compatibilidad con la interfaz
- **`heuristica_mexico`** ya maneja:
  - Quitar sufijos de línea
  - Buscar en la tabla de heurísticas
  - Retornar 0.0 si no encuentra

**Ventaja:** No duplicamos la lógica de heurísticas.

---

## Función 3: `calcular_ruta()`

### Propósito
Calcula la ruta óptima usando `trayecto_optimo_distancia` de `aestrella.py`.

### Código con Explicaciones

```python
def calcular_ruta(origen, destino, graph, station_mapping, reverse_mapping, heuristics_df):
    """
    Calcula la ruta óptima entre dos estaciones usando A*.
    Usa la función trayecto_optimo_distancia de aestrella.py.
    
    Args:
        origen: Nombre simple de la estación de origen
        destino: Nombre simple de la estación de destino
        graph: Grafo NetworkX con las conexiones (no se usa, usa G_mexico de aestrella.py)
        station_mapping: Diccionario de mapeo nombre simple -> nombres con línea
        reverse_mapping: Diccionario de mapeo nombre con línea -> nombre simple
        heuristics_df: DataFrame con la tabla de heurísticas (no se usa)
    
    Returns:
        list: Lista de estaciones en la ruta (nombres simples)
    """
```

**Nota:** `graph` y `heuristics_df` no se usan. Se mantienen por compatibilidad.

---

#### Paso 1: Obtener opciones de líneas

```python
    # Obtener todas las opciones de líneas para origen y destino
    start_options = station_mapping.get(origen, [])
    goal_options = station_mapping.get(destino, [])
    
    if not start_options or not goal_options:
        return []
```

**Ejemplo:**
- Usuario selecciona: "Observatorio" → "Pantitlán"
- `start_options`: `["Observatorio_L1", "Observatorio_L7"]`
- `goal_options`: `["Pantitlán_L1", "Pantitlán_L5", "Pantitlán_L9", "Pantitlán_LA"]`

---

#### Paso 2: Probar todas las combinaciones

```python
    # Probar todas las combinaciones y encontrar la ruta más corta
    best_path = None
    best_length = float('inf')
    
    for start in start_options:
        for goal in goal_options:
```

**Doble bucle:**
- Prueba todas las combinaciones de líneas
- En el ejemplo: 2 × 4 = 8 combinaciones
- Encuentra la más corta

---

```python
            try:
                # Usar la función de aestrella.py
                resultado = trayecto_optimo_distancia(start, goal)
                
                # Extraer ruta y distancia del resultado
                path = resultado["ruta"]
                length = resultado["distancia"]
                
                if length < best_length:
                    best_length = length
                    best_path = path
                    
            except Exception:
                # Si no hay camino, continuar con la siguiente combinación
                continue
```

**Uso de `trayecto_optimo_distancia`:**
- Función de `aestrella.py` que ejecuta A*
- Retorna un diccionario:
  ```python
  {
      "ruta": ["Observatorio_L1", "Tacubaya_L1", ...],
      "distancia": 5432.1,
      "tiempo": "15 mins 23 segs"
  }
  ```
- Extraemos `ruta` y `distancia`
- Guardamos la mejor (más corta)

**Manejo de errores:**
- Si no hay camino entre esas dos versiones de línea, continúa
- Prueba la siguiente combinación

---

#### Paso 3: Convertir a nombres simples

```python
    if best_path is None:
        return []
    
    # Convertir a nombres simples para la UI
    simple_path = [reverse_mapping.get(node, node.split("_L")[0] if "_L" in node else node)
                   for node in best_path]
    
    return simple_path
```

**Conversión:**
- `best_path`: `["Observatorio_L1", "Tacubaya_L7", "Pantitlán_L9"]`
- Usa `reverse_mapping` para convertir
- `simple_path`: `["Observatorio", "Tacubaya", "Pantitlán"]`

**Fallback:** Si no está en `reverse_mapping`, usa `split("_L")[0]`

---

## Flujo Completo de Datos

### 1. Al iniciar la aplicación:

```
aestrella.py se importa
    ↓
Carga tabla_heuristicas.csv → heuristicas
Carga distancias_reales_transbordos.csv → distancias
Construye grafo → G_mexico
    ↓
metro_data.py importa: G_mexico, heuristicas, heuristica_mexico, trayecto_optimo_distancia
    ↓
interfaz_epica.py llama load_metro_data()
    ↓
cargar_datos() carga coordenadas y construye mapeos
Retorna: stations_list, stations_xy, edges_list, G_mexico, heuristicas, mappings
```

### 2. Al calcular una ruta:

```
Usuario selecciona: "Observatorio" → "Pantitlán"
    ↓
find_metro_route("Observatorio", "Pantitlán")
    ↓
calcular_ruta() obtiene opciones de líneas
    ↓
Prueba combinaciones llamando trayecto_optimo_distancia()
    ↓
trayecto_optimo_distancia() ejecuta A* en G_mexico
Usa heuristica_mexico() para guiar la búsqueda
    ↓
Retorna mejor ruta con nombres con línea
    ↓
calcular_ruta() convierte a nombres simples
    ↓
UI muestra: ["Observatorio", "Tacubaya", "Centro Médico", "Pantitlán"]
```

---

## Diferencias con la Versión Anterior

### Antes (versión antigua):
- ❌ Construía su propio grafo NetworkX
- ❌ Cargaba su propia tabla de heurísticas
- ❌ Implementaba su propia lógica de A*
- ❌ Duplicaba código de `aestrella.py`

### Ahora (versión actual):
- ✅ Reutiliza `G_mexico` de `aestrella.py`
- ✅ Reutiliza `heuristicas` de `aestrella.py`
- ✅ Delega A* a `trayecto_optimo_distancia()`
- ✅ Solo maneja adaptación de nombres y coordenadas para UI
- ✅ Código más simple y mantenible

---

## Ventajas de Esta Arquitectura

✅ **Sin duplicación**: No reimplementa A* ni carga datos dos veces  
✅ **Separación de responsabilidades**:
  - `aestrella.py`: Algoritmo y datos del grafo
  - `metro_data.py`: Adaptador para la UI
  - `interfaz_epica.py`: Solo interfaz gráfica  
✅ **Mantenibilidad**: Cambios en A* se reflejan automáticamente  
✅ **Eficiencia**: Datos cargados una sola vez en memoria  
✅ **Claridad**: Cada módulo tiene un propósito claro

---

## Resumen de Funciones

| Función | Propósito | Delega a aestrella.py |
|---------|-----------|----------------------|
| `cargar_datos()` | Carga coordenadas y construye mapeos | Usa `G_mexico` y `heuristicas` |
| `obtener_heuristica()` | Obtiene valor heurístico | Llama a `heuristica_mexico()` |
| `calcular_ruta()` | Calcula ruta óptima | Llama a `trayecto_optimo_distancia()` |

**Filosofía:** `metro_data.py` es un **adaptador** que traduce entre la UI (nombres simples, coordenadas en píxeles) y `aestrella.py` (nombres con línea, algoritmo A*).


## Descripción General

`metro_data.py` es un módulo que contiene funciones simples para cargar datos del sistema de metro desde archivos CSV y calcular rutas óptimas usando el algoritmo A*. Este módulo separa la lógica de datos de la interfaz gráfica.

---

## Imports

```python
import pandas as pd
import networkx as nx
from pathlib import Path
```

- **`pandas`**: Biblioteca para leer y manipular archivos CSV
- **`networkx`**: Biblioteca para crear y trabajar con grafos (usado para el algoritmo A*)
- **`pathlib.Path`**: Para manejar rutas de archivos de forma multiplataforma

---

## Constantes de Configuración

```python
SCALE_FACTOR = 30000
OFFSET_X = 0
OFFSET_Y = 0
```

### ¿Para qué sirven?

Estas constantes se usan para **convertir coordenadas GPS** (latitud/longitud) a **coordenadas de píxeles** para mostrar el mapa en la interfaz gráfica.

- **`SCALE_FACTOR`**: Factor de escala para ampliar las diferencias entre coordenadas GPS
  - Las coordenadas GPS son números muy pequeños (ej: 19.4163, -99.0747)
  - Multiplicar por 30000 las convierte en píxeles visibles en pantalla
  
- **`OFFSET_X` y `OFFSET_Y`**: Desplazamiento horizontal y vertical
  - Actualmente en 0, pero se pueden ajustar para centrar el mapa

---

## Función 1: `cargar_datos()`

### Propósito
Carga todos los datos necesarios del metro desde 3 archivos CSV y los procesa para su uso en la aplicación.

### Código Completo con Explicaciones

```python
def cargar_datos():
    """
    Carga todos los datos necesarios desde los archivos CSV.
    
    Returns:
        tuple: (stations_list, stations_xy, edges_list, graph, heuristics_df, 
                station_mapping, reverse_mapping)
    """
```

#### Paso 1: Determinar la ruta a los archivos CSV

```python
    base_dir = Path(__file__).parent.parent / "Datos" / "Limpio"
```

**Explicación:**
- `Path(__file__)`: Ruta del archivo actual (`metro_data.py`)
- `.parent`: Carpeta padre (sube un nivel → carpeta `UI`)
- `.parent`: Sube otro nivel (carpeta raíz del proyecto)
- `/ "Datos" / "Limpio"`: Navega a la carpeta donde están los CSV

**Resultado:** `/ruta/al/proyecto/Datos/Limpio/`

---

#### Paso 2: Cargar estaciones y convertir coordenadas

```python
    # 1. Cargar estaciones (coordenadas)
    df_stations = pd.read_csv(base_dir / "estaciones_limpias.csv")
    
    # Centrar el mapa
    mean_lat = df_stations["Latitud"].mean()
    mean_lon = df_stations["Longitud"].mean()
```

**Explicación:**
- Lee el CSV con información de estaciones (nombre, latitud, longitud, etc.)
- Calcula el **promedio** de latitud y longitud para centrar el mapa

**¿Por qué centrar?**
- Si no centramos, el mapa podría quedar desplazado
- Al restar el promedio, el centro del mapa queda en (0, 0)

---

```python
    # Diccionario de coordenadas en píxeles
    stations_xy = {}
    for _, row in df_stations.iterrows():
        name = row["Nombre_Estacion"].strip()
        lat = row["Latitud"]
        lon = row["Longitud"]
        
        # Convertir GPS a píxeles
        px = (lon - mean_lon) * SCALE_FACTOR + OFFSET_X
        py = -(lat - mean_lat) * SCALE_FACTOR + OFFSET_Y
        stations_xy[name] = (px, py)
```

**Explicación línea por línea:**

1. **`for _, row in df_stations.iterrows()`**: Itera sobre cada fila del CSV
   - `_`: Ignora el índice de la fila
   - `row`: Contiene los datos de la fila actual

2. **`name = row["Nombre_Estacion"].strip()`**: Obtiene el nombre y elimina espacios

3. **Conversión de coordenadas:**
   - `px = (lon - mean_lon) * SCALE_FACTOR + OFFSET_X`
     - Resta el promedio para centrar
     - Multiplica por 30000 para escalar
     - Suma offset (actualmente 0)
   
   - `py = -(lat - mean_lat) * SCALE_FACTOR + OFFSET_Y`
     - **Nota el signo negativo `-`**: En pantalla, Y crece hacia abajo
     - En GPS, latitud crece hacia arriba
     - El negativo invierte el eje Y

4. **`stations_xy[name] = (px, py)`**: Guarda las coordenadas en píxeles

**Resultado:** Diccionario `{"Observatorio": (150.5, 230.8), "Tacubaya": (180.2, 250.3), ...}`

---

#### Paso 3: Cargar conexiones y construir el grafo

```python
    # 2. Cargar conexiones y construir grafo
    df_edges = pd.read_csv(base_dir / "distancias_reales_transbordos.csv")
    
    graph = nx.Graph()
    edges_list = []
    station_mapping = {}  # nombre simple -> [nombres con línea]
    reverse_mapping = {}  # nombre con línea -> nombre simple
```

**Explicación de las estructuras de datos:**

- **`graph`**: Grafo de NetworkX que contendrá todas las conexiones del metro
- **`edges_list`**: Lista de aristas para dibujar en la UI (sin duplicados)
- **`station_mapping`**: Mapea nombres simples a nombres con línea
  - Ejemplo: `{"Observatorio": ["Observatorio_L1", "Observatorio_L7"]}`
  - Útil porque algunas estaciones tienen múltiples líneas
- **`reverse_mapping`**: Mapea nombres con línea a nombres simples
  - Ejemplo: `{"Observatorio_L1": "Observatorio", "Observatorio_L7": "Observatorio"}`

---

```python
    for _, row in df_edges.iterrows():
        u = row["Origen"].strip()
        v = row["Destino"].strip()
        w = float(row["Distancia"])
        
        # Añadir arista al grafo (con sufijo de línea)
        graph.add_edge(u, v, weight=w)
```

**Explicación:**
- Lee cada conexión del CSV
- `u`: Estación origen (ej: "Observatorio_L1")
- `v`: Estación destino (ej: "Tacubaya_L1")
- `w`: Distancia en metros entre ambas
- **`graph.add_edge(u, v, weight=w)`**: Añade la conexión al grafo con su peso (distancia)

---

```python
        # Extraer nombres simples
        u_simple = u.split("_L")[0] if "_L" in u else u
        v_simple = v.split("_L")[0] if "_L" in v else v
```

**Explicación:**
- **`split("_L")[0]`**: Divide el nombre por "_L" y toma la primera parte
  - "Observatorio_L1" → ["Observatorio", "1"] → "Observatorio"
  - "Tacubaya_L7" → ["Tacubaya", "7"] → "Tacubaya"
- **`if "_L" in u`**: Verifica si tiene sufijo de línea antes de dividir

---

```python
        # Construir mapeos
        if u_simple not in station_mapping:
            station_mapping[u_simple] = []
        if u not in station_mapping[u_simple]:
            station_mapping[u_simple].append(u)
        reverse_mapping[u] = u_simple
        
        if v_simple not in station_mapping:
            station_mapping[v_simple] = []
        if v not in station_mapping[v_simple]:
            station_mapping[v_simple].append(v)
        reverse_mapping[v] = v_simple
```

**Explicación paso a paso:**

1. **Crear entrada en `station_mapping` si no existe:**
   - Si "Observatorio" no está en el diccionario, crea una lista vacía

2. **Añadir nombre con línea a la lista:**
   - Si "Observatorio_L1" no está ya en la lista, lo añade
   - Evita duplicados con `if u not in station_mapping[u_simple]`

3. **Crear entrada en `reverse_mapping`:**
   - Mapea "Observatorio_L1" → "Observatorio"

**Resultado:**
```python
station_mapping = {
    "Observatorio": ["Observatorio_L1", "Observatorio_L7"],
    "Tacubaya": ["Tacubaya_L1", "Tacubaya_L7", "Tacubaya_L9"]
}

reverse_mapping = {
    "Observatorio_L1": "Observatorio",
    "Observatorio_L7": "Observatorio",
    "Tacubaya_L1": "Tacubaya",
    ...
}
```

---

```python
        # Lista de aristas para UI (sin duplicados)
        edge_ui = (u_simple, v_simple)
        if edge_ui not in edges_list and (v_simple, u_simple) not in edges_list:
            edges_list.append(edge_ui)
```

**Explicación:**
- Crea una tupla con nombres simples: `("Observatorio", "Tacubaya")`
- Verifica que no esté ya en la lista (ni en orden inverso)
- Esto evita dibujar la misma línea dos veces en el mapa

---

#### Paso 4: Cargar tabla de heurísticas

```python
    # 3. Cargar tabla de heurísticas
    heuristics_df = pd.read_csv(base_dir / "tabla_heuristicas.csv", index_col=0)
    heuristics_df.index = heuristics_df.index.str.strip()
    heuristics_df.columns = heuristics_df.columns.str.strip()
```

**Explicación:**
- **`index_col=0`**: La primera columna del CSV se usa como índice (nombres de estaciones)
- **`.str.strip()`**: Elimina espacios en blanco de nombres de filas y columnas
- **Resultado**: DataFrame donde puedes buscar `heuristics_df.loc["Origen", "Destino"]`

---

#### Paso 5: Retornar todos los datos

```python
    # Lista de estaciones ordenada
    stations_list = sorted(list(stations_xy.keys()))
    
    return stations_list, stations_xy, edges_list, graph, heuristics_df, station_mapping, reverse_mapping
```

**Retorna 7 elementos:**
1. **`stations_list`**: Lista ordenada de nombres de estaciones
2. **`stations_xy`**: Diccionario con coordenadas en píxeles
3. **`edges_list`**: Lista de conexiones para dibujar
4. **`graph`**: Grafo NetworkX para A*
5. **`heuristics_df`**: Tabla de heurísticas
6. **`station_mapping`**: Mapeo simple → con línea
7. **`reverse_mapping`**: Mapeo con línea → simple

---

## Función 2: `obtener_heuristica()`

### Propósito
Obtiene el valor heurístico entre dos estaciones desde la tabla precalculada.

### Código con Explicaciones

```python
def obtener_heuristica(current, target, heuristics_df):
    """
    Obtiene el valor heurístico entre dos estaciones.
    
    Args:
        current: Estación actual (puede tener sufijo _L)
        target: Estación objetivo (puede tener sufijo _L)
        heuristics_df: DataFrame con la tabla de heurísticas
    
    Returns:
        float: Valor heurístico
    """
    if heuristics_df is None:
        return 0.0
```

**Verificación de seguridad:** Si no hay tabla, retorna 0

---

```python
    # Quitar sufijo de línea si existe
    current_simple = current.split("_L")[0] if "_L" in current else current
    target_simple = target.split("_L")[0] if "_L" in target else target
```

**¿Por qué?**
- El grafo usa nombres con línea: "Observatorio_L1"
- La tabla de heurísticas usa nombres simples: "Observatorio"
- Necesitamos convertir antes de buscar

---

```python
    try:
        return float(heuristics_df.loc[current_simple, target_simple])
    except:
        return 0.0
```

**Explicación:**
- **`heuristics_df.loc[fila, columna]`**: Busca el valor en la tabla
- **`try/except`**: Si hay algún error (estación no encontrada), retorna 0
- **`float()`**: Convierte el valor a número decimal

---

## Función 3: `calcular_ruta()`

### Propósito
Calcula la ruta óptima entre dos estaciones usando el algoritmo A*.

### Código con Explicaciones

```python
def calcular_ruta(origen, destino, graph, station_mapping, reverse_mapping, heuristics_df):
    """
    Calcula la ruta óptima entre dos estaciones usando A*.
    
    Args:
        origen: Nombre simple de la estación de origen
        destino: Nombre simple de la estación de destino
        graph: Grafo NetworkX con las conexiones
        station_mapping: Diccionario de mapeo nombre simple -> nombres con línea
        reverse_mapping: Diccionario de mapeo nombre con línea -> nombre simple
        heuristics_df: DataFrame con la tabla de heurísticas
    
    Returns:
        list: Lista de estaciones en la ruta (nombres simples)
    """
```

---

#### Paso 1: Obtener opciones de líneas

```python
    # Obtener todas las opciones de líneas para origen y destino
    start_options = station_mapping.get(origen, [])
    goal_options = station_mapping.get(destino, [])
    
    if not start_options or not goal_options:
        return []
```

**Explicación:**
- **`station_mapping.get(origen, [])`**: Busca todas las versiones con línea
  - Ejemplo: "Observatorio" → ["Observatorio_L1", "Observatorio_L7"]
- **Si no hay opciones**: Retorna lista vacía (no hay ruta)

**¿Por qué múltiples opciones?**
- Algunas estaciones tienen varias líneas
- Necesitamos probar todas las combinaciones para encontrar la ruta más corta

---

#### Paso 2: Probar todas las combinaciones

```python
    # Probar todas las combinaciones y encontrar la ruta más corta
    best_path = None
    best_length = float('inf')
    
    for start in start_options:
        for goal in goal_options:
```

**Explicación:**
- **Doble bucle**: Prueba todas las combinaciones de líneas
  - Si origen tiene 2 líneas y destino tiene 3, prueba 2×3 = 6 combinaciones
- **`best_length = float('inf')`**: Inicializa con infinito (cualquier ruta será mejor)

---

```python
            try:
                # Ejecutar A* con la función heurística
                path = nx.astar_path(
                    graph,
                    start,
                    goal,
                    heuristic=lambda n, g: obtener_heuristica(n, g, heuristics_df),
                    weight='weight'
                )
```

**Explicación del algoritmo A*:**

- **`nx.astar_path()`**: Función de NetworkX que ejecuta A*
- **Parámetros:**
  - `graph`: El grafo con todas las conexiones
  - `start`: Nodo inicial (ej: "Observatorio_L1")
  - `goal`: Nodo objetivo (ej: "Pantitlán_L5")
  - `heuristic`: Función que estima la distancia restante
    - `lambda n, g`: Función anónima que recibe nodo actual (n) y objetivo (g)
    - Llama a `obtener_heuristica()` para obtener el valor
  - `weight='weight'`: Usa el atributo 'weight' de las aristas (distancia real)

**¿Qué hace A*?**
1. Explora nodos vecinos
2. Para cada nodo calcula: `f(n) = g(n) + h(n)`
   - `g(n)`: Distancia real recorrida hasta ahora
   - `h(n)`: Estimación heurística de lo que falta
3. Siempre expande el nodo con menor `f(n)`
4. Encuentra la ruta más corta de forma eficiente

---

```python
                # Calcular longitud del camino
                length = nx.astar_path_length(
                    graph,
                    start,
                    goal,
                    heuristic=lambda n, g: obtener_heuristica(n, g, heuristics_df),
                    weight='weight'
                )
                
                if length < best_length:
                    best_length = length
                    best_path = path
```

**Explicación:**
- **`nx.astar_path_length()`**: Calcula la longitud total de la ruta
- **Comparación**: Si esta ruta es más corta que la mejor encontrada, la guarda

---

```python
            except nx.NetworkXNoPath:
                continue
```

**Manejo de errores:**
- Si no hay camino posible entre esas dos versiones de línea, continúa con la siguiente

---

#### Paso 3: Convertir a nombres simples

```python
    if best_path is None:
        return []
    
    # Convertir a nombres simples para la UI
    simple_path = [reverse_mapping.get(node, node.split("_L")[0] if "_L" in node else node)
                   for node in best_path]
    
    return simple_path
```

**Explicación:**
- **Si no se encontró ruta**: Retorna lista vacía
- **Conversión**: Usa `reverse_mapping` para convertir cada nodo
  - "Observatorio_L1" → "Observatorio"
  - "Tacubaya_L7" → "Tacubaya"
- **Fallback**: Si no está en el diccionario, usa `split("_L")[0]`

**Resultado:** `["Observatorio", "Tacubaya", "Centro Médico", "Pantitlán"]`

---

## Resumen del Flujo Completo

1. **`cargar_datos()`**: Carga CSV → Construye grafo → Retorna estructuras de datos
2. **`calcular_ruta()`**: Recibe nombres simples → Prueba combinaciones → Ejecuta A* → Retorna ruta
3. **`obtener_heuristica()`**: Función auxiliar usada por A* para estimar distancias

## Ventajas de Esta Arquitectura

✅ **Modular**: Lógica de datos separada de la UI  
✅ **Simple**: Funciones en lugar de clases  
✅ **Eficiente**: Usa NetworkX (biblioteca optimizada)  
✅ **Flexible**: Fácil de modificar o extender  
✅ **Reutilizable**: Puede usarse en otros proyectos
