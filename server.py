from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import pandas as pd

# Importar módulos del proyecto
from aestrella import trayecto_optimo_distancia, G_mexico
from Datos import horarios_metro

app = Flask(__name__)
CORS(app) # Permitir peticiones desde el frontend (React)

@app.route('/api/stations', methods=['GET'])
def get_stations():
    """Retorna la lista de todas las estaciones (nodos del grafo)."""
    stations = list(G_mexico.nodes())
    stations.sort()
    return jsonify(stations)

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Retorna las coordenadas de todas las estaciones."""
    # Usamos el DataFrame de stops cargado en horarios_metro
    stops_df = horarios_metro.stops
    
    locations = {}
    for node in G_mexico.nodes():
        # Extraer nombre limpio para buscar en stops
        if "_L" in node:
            name_part = node.split("_L")[0].replace("_", " ")
            # Buscamos en stops
            match = stops_df[stops_df['stop_name'].str.lower() == name_part.lower()]
            if not match.empty:
                # Tomamos el primero
                locations[node] = {
                    "lat": float(match.iloc[0]['stop_lat']),
                    "lon": float(match.iloc[0]['stop_lon'])
                }
    
    return jsonify(locations)

@app.route('/api/station/<station_name>', methods=['GET'])
def get_station_info(station_name):
    """Retorna información detallada de una estación."""
    time = request.args.get('time')
    if not time:
        # Hora actual por defecto
        now = pd.Timestamp.now()
        time = now.strftime("%H:%M:%S")

    # Obtener próximos trenes
    next_trains = horarios_metro.obtener_proximos_trenes(station_name, time, n=5)
    
    # Obtener info básica (línea, etc)
    line = station_name.split("_L")[1] if "_L" in station_name else "?"
    
    return jsonify({
        "name": station_name,
        "line": line,
        "next_trains": next_trains
    })

@app.route('/api/lines', methods=['GET'])
def get_lines():
    """Retorna las líneas y sus estaciones."""
    # Agrupar estaciones por línea
    lines = {}
    for node in G_mexico.nodes():
        if "_L" in node:
            line = node.split("_L")[1]
            if line not in lines:
                lines[line] = []
            lines[line].append(node)
            
    # Ordenar estaciones (esto es básico, idealmente usaríamos shape_id o stop_sequence si quisiéramos orden real)
    for line in lines:
        lines[line].sort()
        
    return jsonify(lines)

@app.route('/api/route', methods=['POST'])
def get_route():
    """
    Calcula la ruta óptima y el próximo tren.
    Input: { "origin": "...", "destination": "...", "time": "HH:MM:SS" }
    """
    data = request.json
    origin = data.get('origin')
    destination = data.get('destination')
    time = data.get('time')
    
    if not origin or not destination or not time:
        return jsonify({"error": "Faltan parámetros"}), 400
        
    try:
        # 1. Calcular ruta óptima con A*
        path, distance = trayecto_optimo_distancia(origin, destination)
        
        # 2. Calcular próximo tren (usando el origen)
        # Nota: horarios_metro.obtener_proximo_tren ya no usa destino
        next_train_info = horarios_metro.obtener_proximo_tren(origin, time)
        
        # 3. Estructurar respuesta
        response = {
            "path": path,
            "distance": distance,
            "next_train": next_train_info
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Iniciando servidor Flask en puerto 5000...")
    app.run(debug=True, port=5000)
