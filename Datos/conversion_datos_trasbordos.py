import pandas as pd

V_TREN_KMH = 35.0
V_PIE_KMH = 4.8

FACTOR_EQUIVALENCIA = V_TREN_KMH / V_PIE_KMH  # ≈ 7.2916

def cargar_transbordos(ruta_csv="Datos/Limpio/distancias_transbordos_original.csv"):
    df = pd.read_csv(ruta_csv)
    # la diistancia “equivalente” para A* (como si todo fuera a 35 km/h)
    df["Coste_Aestrella"] = df["Distancia"] * FACTOR_EQUIVALENCIA
    return df

def guardar_csv_para_aestrella( ruta_salida="Datos/Limpio/distancias_transbordos_para_aestrella.csv" ):
    """
    Usa cargar_transbordos() y guarda un nuevo CSV con las columnas:
    - Distancia_fisica_m (metros reales)
    - Coste_Aestrella (metros equivalentes para A*)
    - más las columnas originales que ya tuviera el CSV
    """
    df = cargar_transbordos()  # usa la ruta por defecto
    df.to_csv(ruta_salida, index=False)
    print(f"CSV guardado en: {ruta_salida}")


if __name__ == "__main__":
    guardar_csv_para_aestrella()

