# Documentación del Módulo de Horarios (`Datos/horarios_metro.py`)

Este documento describe la funcionalidad y estructura del módulo `horarios_metro.py`, diseñado para calcular los tiempos de llegada de trenes en el Metro de la CDMX utilizando datos GTFS.

## Ubicación
- **Archivo Principal**: `Datos/horarios_metro.py`
- **Datos GTFS**: `Datos/Crudo/f-9g3-semovi-latest/`

## Estructura y Diseño
El módulo ha sido refactorizado para utilizar un **paradigma funcional** (sin clases), facilitando su integración y simplicidad. Utiliza variables globales a nivel de módulo para cachear los DataFrames de pandas y evitar recargas innecesarias de los archivos CSV.

### Variables Globales (Caché)
- `_STOPS`, `_CALENDAR`, `_TRIPS`, `_FREQUENCIES`, `_STOP_TIMES`, `_ROUTES`: Almacenan los datos GTFS una vez cargados.

### Funciones Principales

#### `obtener_proximo_tren(estacion_origen, hora_actual_str)`
Es la función principal que debe ser llamada por otros scripts.
- **Entradas**:
    - `estacion_origen`: Nombre del nodo (ej. "Observatorio_L1").
    - `hora_actual_str`: Hora en formato "HH:MM:SS".
- **Lógica**:
    1. **Carga de Datos**: Llama a `_cargar_datos()` si es necesario.
    2. **Mapeo**: Convierte nombre de estación a `stop_id`s GTFS.
    3. **Servicios**: Identifica qué servicios operan hoy.
    4. **Ruta**: Determina la `route_id` basándose en la línea.
    5. **Cálculo**: Busca todos los viajes que pasan por la estación de origen y calcula sus tiempos de llegada.
    6. **Selección**: Devuelve el tren con la llegada más próxima posterior a la hora actual, sin importar la dirección.
- **Salida**: Diccionario con `proxima_llegada`, `tiempo_espera`, `direccion` (del tren encontrado), etc.

### Funciones Auxiliares (Internas)
- `_cargar_datos()`: Carga los CSVs si las variables globales están vacías.
- `_str_hora_a_segundos(hora_str)`: Convierte "HH:MM:SS" a segundos enteros.
- `_segundos_a_str_hora(segundos)`: Convierte segundos a "HH:MM:SS".
- `_obtener_stop_ids_candidatos(nodo_estacion)`: Busca IDs en `stops.txt` que coincidan con el nombre y línea.
- `_obtener_service_ids_activos(fecha_obj)`: Filtra `calendar.txt` por fecha y día de la semana.

## Cómo Usar
Para usar este módulo desde otro script (ej. en la raíz):

```python
from Datos import horarios_metro

resultado = horarios_metro.obtener_proximo_tren("Observatorio_L1", "14:30:00")
print(resultado)
```

## Notas para Desarrolladores
- **Rutas**: Las rutas a los archivos de datos son relativas a la ubicación del script `horarios_metro.py`. Si mueves el archivo, asegúrate de actualizar `_RUTA_GTFS`.
- **Nombres de Estaciones**: El sistema espera el formato `Nombre_Línea` (ej. `_L1`). Espacios en nombres de estaciones son manejados reemplazando guiones bajos.
