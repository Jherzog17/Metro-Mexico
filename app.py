#!/usr/bin/env python3
"""
Metro CDMX - Aplicación Principal
Punto de entrada para ejecutar el navegador de rutas del Metro de la Ciudad de México.
"""

import sys
from pathlib import Path

# Añadir el directorio UI al path para poder importar los módulos
ui_path = Path(__file__).parent / "UI"
sys.path.insert(0, str(ui_path))

# Importar y ejecutar la aplicación
from arquitectura import main

if __name__ == "__main__":
    main()
