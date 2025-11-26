import pandas as pd
from pathlib import Path

# Obtener la ruta raíz del proyecto
directorio_root = Path(__file__).parent.parent

V_TREN_KMH = 35.0
V_PIE_KMH = 4.8

FACTOR_EQUIVALENCIA = V_TREN_KMH / V_PIE_KMH  # ≈ 7.2916

def cargar_transbordos(ruta_csv= directorio_root / "Datos/Limpio/Transbordos/distancias_transbordos_original.csv"):
    df = pd.read_csv(ruta_csv)
    # la diistancia “equivalente” para A* (como si todo fuera a 35 km/h)
    df["Coste_Aestrella"] = df["Distancia"] * FACTOR_EQUIVALENCIA
    return df

def guardar_csv_para_aestrella( ruta_salida= directorio_root / "Datos/Limpio/Transbordos/distancias_transbordos_para_aestrella.csv" ):
    """
    Usa cargar_transbordos() y guarda un nuevo CSV con las columnas:
    Coste_Aestrella (metros equivalentes para A*)
    más las columnas originales que ya tuviera el CSV
    """
    df = cargar_transbordos()  # usa la ruta por defecto
    df.to_csv(ruta_salida, index=False)
    print(f"CSV guardado en: {ruta_salida}")


if __name__ == "__main__":
    guardar_csv_para_aestrella()

    # Rutas relativas desde la raíz del proyecto
    RUTA_INTRODUCIR_DATOS = directorio_root / "Datos/Limpio/distancias_reales_transbordos.csv"
    RUTA_DATOS_TRANSBORDOS = directorio_root / "Datos/Limpio/Transbordos/distancias_transbordos_para_aestrella.csv"

    # Cargar el fichero grande (todas las aristas, con 0 en los transbordos)
    df_main = pd.read_csv(RUTA_INTRODUCIR_DATOS)

    # Cargar el fichero de transbordos con Coste_Aestrella
    df_costes = pd.read_csv(RUTA_DATOS_TRANSBORDOS)

    # Filtrar solo las filas de transbordo (es decir las que tienen distancia = 0)
    mask_transbordos = df_main["Distancia"] == 0
    df_transbordos = df_main[mask_transbordos].copy()

    # aqui aprovecho que el orden es el mismo
    # sustuir los 0 por los Coste_Aestrella 
    df_transbordos["Distancia"] = df_costes["Coste_Aestrella"].values

    # Volvemos a meter esas distancias en el dataframe original
    df_main.loc[mask_transbordos, "Distancia"] = df_transbordos["Distancia"]

    # Guardamos sobre el MISMO fichero
    df_main.to_csv(RUTA_INTRODUCIR_DATOS, index=False)