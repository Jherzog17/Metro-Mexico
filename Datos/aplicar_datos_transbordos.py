import pandas as pd

from pathlib import Path

# Obtener la ruta raíz del proyecto
directorio_root = Path(__file__).parent.parent

# Rutas relativas desde la raíz del proyecto
RUTA_INTRODUCIR_DATOS = directorio_root / "Datos/Limpio/distancias_reales_transbordos.csv"
RUTA_DATOS_TRANSBORDOS = directorio_root / "Datos/Limpio/Transbordos/distancias_transbordos_para_aestrella.csv"

# Cargar el fichero grande (todas las aristas, con 0 en los transbordos)
df_main = pd.read_csv(RUTA_INTRODUCIR_DATOS)

# Cargar el fichero de transbordos con Coste_Aestrella
df_costes = pd.read_csv(RUTA_DATOS_TRANSBORDOS)

# filtrar solo las filas de transbordo (es decir las que tienen distancia = 0)
mask_transbordos = df_main["Distancia"] == 0
df_transbordos = df_main[mask_transbordos].copy()

# aqui aprovecho que el orden es el mismo
# sustuir los 0 por los Coste_Aestrella 
df_transbordos["Distancia"] = df_costes["Coste_Aestrella"].values

# Volvemos a meter esas distancias en el dataframe original
df_main.loc[mask_transbordos, "Distancia"] = df_transbordos["Distancia"]

# Guardamos sobre el MISMO fichero
df_main.to_csv(RUTA_INTRODUCIR_DATOS, index=False)