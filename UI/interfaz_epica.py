from __future__ import annotations
import sys
import math
from typing import Callable, Dict, List, Tuple, Optional
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPolygonF, QBrush, QColor, QPen, QPainter
from metro_data import cargar_datos, calcular_ruta


# --- CONFIGURACIÓN DE ESTILO (CSS) ---
# Esto le da el look "App Moderna" en lugar de "Programa de Contabilidad"
STYLESHEET = """
QMainWindow {
    background-color: #121212; /* Fondo muy oscuro */
}
QLabel {
    color: #E0E0E0;
    font-family: 'Segoe UI', sans-serif;
}
/* El panel lateral "flotante" */
QWidget#SidePanel {
    background-color: #511B18;
    border-right: 1px solid #333;
}
/* Botones modernos y redondeados */
QPushButton {
    background-color: #305853;
    color: #000000;
    border-radius: 8px;
    padding: 10px;
    font-weight: bold;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #B06821;
}
QPushButton:pressed {
    background-color: #1B2A30;
}
QPushButton#btn_limpiar {
    background-color: #305853; /* Rojo suave para borrar */
    color: white;
}
/* Combos estilizados */
QComboBox {
    background-color: #1B2A30;
    color: white;
    border: 1px solid #0d1518;
    border-radius: 5px;
    padding: 5px;
}
QComboBox::drop-down {
    border: 2px;
    
}
/* Lista de pasos limpia */
QListWidget {
    background-color: #481716;
    border: none;
    color: #AAAAAA;
    font-size: 13px;
}
QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid #b06821;
}
QListWidget::item:selected {
    background-color: #1b2a30;
    color: #BB86FC;
}
/* La barra de estado */
QStatusBar {
    background-color: #121212;
    color: #777;
}
"""

# Tipos simples
StationId = str
Point = Tuple[float, float]
Edge = Tuple[StationId, StationId]


class MapView(QtWidgets.QGraphicsView):
    """Visor de mapa estilo 'Google Maps Dark Mode'."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Configuramos la escena con fondo oscuro
        self.setScene(QtWidgets.QGraphicsScene(self))
        self.setBackgroundBrush(QBrush(QColor("#1B2A30")))

        # CALIDAD GRÁFICA: Esto es vital para que no se vea pixelado
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)

        # Navegación
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

        # Quitamos los bordes feos del widget
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def wheelEvent(self, event):
        # Zoom suave tipo Google Maps
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def draw_network(
            self,
            stations_xy: Dict[StationId, Point],
            edges: List[Edge],
            station_radius: float = 16.0,  # Estaciones un poco más grandes
    ) -> None:
        scene = self.scene()
        scene.clear()

        # 1. Dibujar conexiones (aristas) estilo "Línea de Metro"
        # Usamos un color gris medio para las líneas inactivas
        pen_edge = QPen(QColor("#B06821"))
        pen_edge.setWidthF(5.0)  # Líneas más gruesas
        pen_edge.setCapStyle(Qt.RoundCap)  # Bordes de línea redondeados

        for a, b in edges:
            if a in stations_xy and b in stations_xy:
                xa, ya = stations_xy[a]
                xb, yb = stations_xy[b]
                scene.addLine(xa, ya, xb, yb, pen_edge)

        # 2. Dibujar estaciones (nodos)
        # Color blanco brillante con borde oscuro
        brush_station = QBrush(QColor("#E0FFFF"))
        pen_station = QPen(QColor("#511B18"))
        pen_station.setWidthF(8.0)

        for stationid, (x, y) in stations_xy.items():
            # Dibujamos el círculo
            circle = scene.addEllipse(
                x - station_radius,
                y - station_radius,
                2 * station_radius,
                2 * station_radius,
                pen_station,
                brush_station,
            )
            # Añadir tooltips modernos (podría requerir HTML básico)
            circle.setToolTip(f"Estación: {stationid}")

        self.fitInView(scene.itemsBoundingRect().marginsAdded(QtCore.QMarginsF(50, 50, 50, 50)), Qt.KeepAspectRatio)

    def draw_route(self, stations_xy: Dict[StationId, Point], path: List[StationId]) -> None:
        if not path:
            return
        scene = self.scene()

        # 3. Resaltar ruta (Efecto Neón)
        # Usamos un color brillante (ej. Cian o Verde Ácido)
        route_color = QColor("#ADD8E6")  # Cian eléctrico

        # Efecto "Glow" (Simulado dibujando una línea gruesa semitransparente debajo)
        pen_glow = QPen(route_color)
        pen_glow.setWidthF(10.0)
        pen_glow.setColor(QColor(3, 218, 198, 60))  # Mismo color, transparencia alta
        pen_glow.setCapStyle(Qt.RoundCap)

        pen_route = QPen(route_color)
        pen_route.setWidthF(4.0)
        pen_route.setCapStyle(Qt.RoundCap)

        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            if a in stations_xy and b in stations_xy:
                xa, ya = stations_xy[a]
                xb, yb = stations_xy[b]

                # Dibujar brillo
                scene.addLine(xa, ya, xb, yb, pen_glow)
                # Dibujar línea central
                scene.addLine(xa, ya, xb, yb, pen_route)

                # --- Flecha direccional ---
                dx = xb - xa
                dy = yb - ya
                angle = math.atan2(dy, dx)

                # Posicionamos la flecha a mitad de camino, no al final, queda más limpio
                mid_x = (xa + xb) / 2
                mid_y = (ya + yb) / 2

                arrow_size = 8
                p1 = QPointF(mid_x + arrow_size * math.cos(angle), mid_y + arrow_size * math.sin(angle))
                p2 = QPointF(mid_x + arrow_size * math.cos(angle + 2.6), mid_y + arrow_size * math.sin(angle + 2.6))
                p3 = QPointF(mid_x + arrow_size * math.cos(angle - 2.6), mid_y + arrow_size * math.sin(angle - 2.6))

                arrow_head = QtWidgets.QGraphicsPolygonItem(QPolygonF([p1, p2, p3]))
                arrow_head.setBrush(QBrush(QColor("#E0FFFF")))  # Flecha azul sobre línea brillante
                arrow_head.setPen(Qt.NoPen)
                scene.addItem(arrow_head)


class MainWindow(QtWidgets.QMainWindow):
    route_requested = QtCore.Signal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Metro CDMX – Navegador")
        self.resize(1280, 800)

        # Hooks
        self._data_loader = None
        self._route_finder = None
        self.stations_list = []
        self.stations_xy = {}
        self.edges = []

        self._build_ui()
        self._connect_signals()

        # APLICAR EL CSS GLOBAL
        self.setStyleSheet(STYLESHEET)

    def _build_ui(self):
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)

        # Usamos un layout horizontal sin márgenes para que se vea 'full screen'
        main_layout = QtWidgets.QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- PANEL IZQUIERDO (CONTROLES) ---
        # Contenedor para darle color de fondo específico
        left_container = QtWidgets.QWidget()
        left_container.setObjectName("SidePanel")  # ID para CSS
        #left_container.setStyleSheet("background-color: #511B18;")
        left_container.setFixedWidth(350)  # Ancho fijo elegante

        left_layout = QtWidgets.QVBoxLayout(left_container)
        left_layout.setContentsMargins(20, 30, 20, 30)  # Margen interno
        left_layout.setSpacing(15)

        # Título
        title = QtWidgets.QLabel("METRO CDMX")
        title.setStyleSheet("font-size: 24px; font-weight: 900; color: #B06821; letter-spacing: 2px;")
        left_layout.addWidget(title)

        subtitle = QtWidgets.QLabel("Planificador de Ruta Inteligente")
        subtitle.setStyleSheet("color: #305853; font-size: 12px; margin-bottom: 10px;")
        left_layout.addWidget(subtitle)

        # Inputs
        self.cmb_origen = QtWidgets.QComboBox()
        self.cmb_origen.setPlaceholderText("Selecciona Origen...")
        self.cmb_destino = QtWidgets.QComboBox()
        self.cmb_destino.setPlaceholderText("Selecciona Destino...")
        self.cmb_origen.setEditable(True)
        self.cmb_destino.setEditable(True)

        lbl_orig = QtWidgets.QLabel("ORIGEN")
        lbl_orig.setStyleSheet("font-size: 10px; font-weight: bold; color: #305853;")
        left_layout.addWidget(lbl_orig)
        left_layout.addWidget(self.cmb_origen)

        lbl_dest = QtWidgets.QLabel("DESTINO")
        lbl_dest.setStyleSheet("font-size: 10px; font-weight: bold; color: #305853;")
        left_layout.addWidget(lbl_dest)
        left_layout.addWidget(self.cmb_destino)

        # Botones Acción
        self.btn_calcular = QtWidgets.QPushButton("CALCULAR RUTA")
        self.btn_calcular.setCursor(Qt.PointingHandCursor)
        left_layout.addWidget(self.btn_calcular)

        # Separador
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("color: #305853;")
        left_layout.addWidget(line)

        # Resultados
        self.lbl_resumen = QtWidgets.QLabel("Esperando ruta...")
        self.lbl_resumen.setStyleSheet("font-size: 14px; font-style: italic; color: #305853;")
        self.lbl_resumen.setWordWrap(True)
        left_layout.addWidget(self.lbl_resumen)

        self.steps_list = QtWidgets.QListWidget()
        left_layout.addWidget(self.steps_list)

        # Botones secundarios
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_cargar = QtWidgets.QPushButton("Recargar Datos")
        self.btn_cargar.setStyleSheet("background-color: #305853; color: white; font-size: 11px;")
        self.btn_limpiar = QtWidgets.QPushButton("Limpiar")
        self.btn_limpiar.setObjectName("btn_limpiar")  # ID para CSS rojo

        btn_row.addWidget(self.btn_cargar)
        btn_row.addWidget(self.btn_limpiar)
        left_layout.addLayout(btn_row)

        # --- PANEL DERECHO (MAPA) ---
        self.map = MapView()

        # Añadir al layout principal
        main_layout.addWidget(left_container)
        main_layout.addWidget(self.map, 1)  # 1 = estirar mapa todo lo posible

        # Barra de estado minimalista
        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)

    def _connect_signals(self):
        self.btn_cargar.clicked.connect(self.on_load_data)
        self.btn_calcular.clicked.connect(self.on_calculate)
        self.btn_limpiar.clicked.connect(self.on_clear)
        self.route_requested.connect(self._handle_route_requested)

    # ---------- Integración (IGUAL QUE ANTES) ----------
    def set_data_loader(self, loader: Callable):
        self._data_loader = loader

    def set_route_finder(self, finder: Callable):
        self._route_finder = finder

    # ---------- Slots ----------
    @QtCore.Slot()
    def on_load_data(self):
        if not self._data_loader:
            return
        try:
            stations, stations_xy, edges = self._data_loader()
            self.stations_list = stations
            self.stations_xy = stations_xy
            self.edges = edges

            self.cmb_origen.clear()
            self.cmb_destino.clear()
            self.cmb_origen.addItems(self.stations_list)
            self.cmb_destino.addItems(self.stations_list)

            self.map.draw_network(self.stations_xy, self.edges)
            self.status.showMessage(f"Sistema en línea • {len(stations)} estaciones operativas")
        except Exception as e:
            self.status.showMessage(f"Error: {str(e)}")

    @QtCore.Slot()
    def on_calculate(self):
        origen = self.cmb_origen.currentText().strip()
        destino = self.cmb_destino.currentText().strip()
        if not origen or not destino:
            return
        self.route_requested.emit(origen, destino)

    @QtCore.Slot()
    def on_clear(self):
        self.steps_list.clear()
        self.lbl_resumen.setText("Esperando ruta...")
        self.map.draw_network(self.stations_xy, self.edges)  # Redibuja limpio

    @QtCore.Slot(str, str)
    def _handle_route_requested(self, origen: str, destino: str):
        if not self._route_finder:
            return
        result = self._route_finder(origen, destino)
        if not result:
            self.lbl_resumen.setText("⚠ No hay ruta disponible.")
            return

        # result is now just a list of station names
        path = result
        
        self.steps_list.clear()
        for i, stationid in enumerate(path):
            # Icono bonito en la lista
            item = QtWidgets.QListWidgetItem(f"{i + 1}. {stationid}")
            self.steps_list.addItem(item)

        # Calculate number of stations (not transfers)
        num_stations = len(path) - 1
        self.lbl_resumen.setText(f"✔ Ruta calculada: {num_stations} estaciones")
        self.map.draw_network(self.stations_xy, self.edges)
        self.map.draw_route(self.stations_xy, path)


# --------- VARIABLES GLOBALES PARA DATOS DEL METRO ---------
# Se cargarán al iniciar la aplicación
stations_list = []
stations_xy = {}
edges_list = []
graph = None
heuristics_df = None
station_mapping = {}
reverse_mapping = {}


def load_metro_data():
    """Carga los datos del metro desde los CSV."""
    global stations_list, stations_xy, edges_list, graph, heuristics_df, station_mapping, reverse_mapping
    
    stations_list, stations_xy, edges_list, graph, heuristics_df, station_mapping, reverse_mapping = cargar_datos()
    
    return stations_list, stations_xy, edges_list


def find_metro_route(origen, destino):
    """Calcula la ruta óptima entre dos estaciones."""
    global graph, station_mapping, reverse_mapping, heuristics_df
    
    return calcular_ruta(origen, destino, graph, station_mapping, reverse_mapping, heuristics_df)


def main():
    app = QtWidgets.QApplication(sys.argv)

    # Configuración de fuente
    font = QtGui.QFont("Segoe UI", 10)
    app.setFont(font)

    win = MainWindow()

    # --- CONFIGURACIÓN DEL SISTEMA ---
    # Usar funciones simples para cargar datos y calcular rutas
    win.set_data_loader(load_metro_data)
    win.set_route_finder(find_metro_route)
    # --------------------------

    win.show()

    # Esto hace que cargue los datos nada más abrirse
    # (Asegúrate de tener los 3 CSVs en la misma carpeta)
    win.on_load_data()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()