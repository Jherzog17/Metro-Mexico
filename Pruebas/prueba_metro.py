import sys
import os

# Agregar el directorio padre (donde está Datos) al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Datos import horarios_metro

def ejecutar_pruebas():
    casos_prueba = [
        ("Observatorio_L1", "12:00:00"),
        ("Pantitlán_L1", "12:00:00"),
        ("Tacubaya_L1", "12:00:00"),
        ("Estacion_Invalida", "12:00:00")
    ]
    
    print("Ejecutando Pruebas de Verificación (API Simplificada)...\n")
    
    for origen, hora in casos_prueba:
        print(f"Prueba: {origen} a las {hora}")
        resultado = horarios_metro.obtener_proximo_tren(origen, hora)
        print(f"Resultado: {resultado}\n")

if __name__ == "__main__":
    ejecutar_pruebas()
