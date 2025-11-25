# Metro CDMX - Práctica IA

En esta practica hemos creado una aplicación que determina la ruta en metro más corta desde una estación a otra. Esta aplicación utiliza el algoritmo A* para determinar esta ruta más óptima.

## Cómo Ejecutar la Aplicación

```bash
cd UI
python3 arquitectura.py
```

## Librerías Necesarias

Todas estas librerias son necesarias para ejecutar la app:

```bash
pip install networkx
pip install pandas
pip install PySide6
pip install geopy
pip install numpy
```

## Descripción de las Librerías

- **networkx**: Biblioteca para la creación, manipulación y estudio de grafos. Utilizada para implementar el algoritmo A*.
- **pandas**: Biblioteca para análisis y manipulación de datos. Utilizada para leer y procesar archivos CSV.
- **PySide6**: Framework Qt para Python. Utilizada para crear la interfaz gráfica de usuario.
- **geopy**: Biblioteca para cálculos geográficos. Utilizada para calcular distancias geodésicas entre estaciones.
- **numpy**: Biblioteca fundamental para computación científica. Utilizada para operaciones numéricas.

## Estructura del Proyecto

```
PracticaMetroMexico/
├── aestrella.py              # Implementación del algoritmo A*
├── UI/
│   ├── interfaz_epica.py     # Interfaz gráfica principal
│   └── metro_data.py         # Funciones de carga de datos
├── Datos/
│   ├── Limpio/               # Datos procesados (CSV)
│   ├── sacar_datos.py        # Script para procesar datos
│   ├── sacar_dist_real.py    # Script para calcular distancias
│   └── tabla_heuristicas.py  # Script para generar heurísticas
└── README.md                 # Este archivo
```

