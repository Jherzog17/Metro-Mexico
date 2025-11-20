from __future__ import annotations

"""
Interfaz gráfica base (PySide6/Qt) para el proyecto del Metro de CDMX.
Tu equipo puede conectar aquí:
  1) Carga de datos desde la API (paradas, líneas, trasbordos)
  2) Función de ruta (A*) que devuelva la mejor ruta entre origen y destino

Archivo único, fácil de leer y extender.
Probado con PySide6 >= 6.6.

Sugerencia de organización del equipo:
- data_provider: objeto/funciones que traen estaciones y conexiones (API)
- route_finder: función que recibe (origen, destino) y devuelve lista de nodos/estaciones
Debajo verás "hooks" (métodos set_...) para inyectar esas piezas sin tocar la UI.
"""

import sys
from typing import Callable, Dict, List, Tuple, Optional
from PySide6 import QtCore, QtGui, QtWidgets

# Tipos simples para claridad
StationId = str
Point = Tuple[float, float]  # coordenadas planas para dibujar (proyección simple)
Edge = Tuple[StationId, StationId]


class MapView(QtWidgets.QGraphicsView):
    """Visor de mapa simple con zoom con rueda y arrastre con botón izquierdo."""

    def __init__(self, parent=None): #parent = None significa que si por defecto no es especificado se pone ese valor.
        super().__init__(parent)  #hereda todo(métodos, atributos, señales)  del padre
        self.setScene(QtWidgets.QGraphicsScene(self)) # el método self.setScene espera un objeto de tipo QGraphicsScene, que hace que se pueda ver el contenido del lienzo
        #self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        #self.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)
        #fself._scale_step = 1.15

    #sobreescritura del método padre

    #def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        #if event.angleDelta().y() > 0:
            #factor = self._scale_step
        #else:
            #factor = 1 / self._scale_step #usa el inverso del factor para hacer zoom out.
        #self.scale(factor, factor)

    # === Dibujo de red y rutas ===
    # Limpia todo lo que se haya añadido a la escena (QGraphicsScene)
    def clear(self):
        self.scene().clear()

    def draw_network(
        self,
        stations_xy: Dict[StationId, Point], #crea un diccionario con el id de la estacion y sus coordenadas
        edges: List[Edge], #lista de conexiones (cada edge es una conexion : Sol-Callao
        station_radius: float = 3.0,
    ) -> None:
        scene = self.scene()
        scene.clear()

        # Dibujar conexiones (aristas)
        pen_edge = QtGui.QPen(QtGui.QColor(180, 180, 180))
        pen_edge.setWidthF(1.5)
        for a, b in edges: #primero comprueba que ambos id estén en el diccionario
            if a in stations_xy and b in stations_xy:
                xa, ya = stations_xy[a] #busca el valor que tiene en el diccionario la clave a (que es el ID de la estación)
                xb, yb = stations_xy[b]
                scene.addLine(xa, ya, xb, yb, pen_edge) #(une los puntos en una línea)

        # Dibujar estaciones (nodos)
        brush_station = QtGui.QBrush(QtGui.QColor(40, 120, 255))
        pen_station = QtGui.QPen(QtCore.Qt.black)
        for stationid, (x, y) in stations_xy.items():
            circle = scene.addEllipse(
                    x - station_radius,
                    y - station_radius,
                    2 * station_radius,
                    2 * station_radius,
                    pen_station,
                    brush_station,
            )
            circle.setToolTip(stationid)

        # Ajustar vista
        self.fitInView(scene.itemsBoundingRect().marginsAdded(QtCore.QMarginsF(20, 20, 20, 20)),
                       QtCore.Qt.KeepAspectRatio)

    def draw_route(self, stations_xy: Dict[StationId, Point], path: List[StationId]) -> None:
        if not path:
            return
        scene = self.scene()
        # Resaltar ruta encima de todo
        pen_route = QtGui.QPen(QtGui.QColor(255, 80, 80))
        pen_route.setWidthF(3.0)
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            if a in stations_xy and b in stations_xy:
                xa, ya = stations_xy[a]
                xb, yb = stations_xy[b]
                scene.addLine(xa, ya, xb, yb, pen_route)
                # añade la linea de la flecha

                dx = xb - xa
                dy = yb - ya
                angle = math.atan2(dy,
                                   dx)  # angulo entre eje x y la linea (para saber la direccion), devuelve el angulo de roacion en radianes

                # Define el tamaño de la flecha
                arrow_size = 10

                # Calcula los puntos del triángulo de la flecha
                p1 = QPointF(xb, yb)  # punta, va al final de la linea
                p2 = QPointF(xb - arrow_size * math.cos(angle - math.pi / 6),
                             yb - arrow_size * math.sin(angle - math.pi / 6))
                p3 = QPointF(xb - arrow_size * math.cos(angle + math.pi / 6),
                             yb - arrow_size * math.sin(angle + math.pi / 6))

                # Crea el polígono (flecha)
                arrow_head = QtWidgets.QGraphicsPolygonItem(QPolygonF([p1, p2, p3]))
                arrow_head.setBrush(QBrush(QColor(255, 80, 80)))
                arrow_head.setPen(QtGui.QPen(QtCore.Qt.NoPen))

                scene.addItem(arrow_head)


class MainWindow(QtWidgets.QMainWindow):
    route_requested = QtCore.Signal(str, str)  # (origen, destino) #señal emitida cuando se pulse "Calcular ruta"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Metro CDMX – Planificador de rutas (UI)")
        self.resize(1200, 750)

        # Hooks a inyectar por el equipo
        self._data_loader: Optional[Callable[[], Tuple[List[StationId], Dict[StationId, Point], List[Edge]]]] = None
        self._route_finder: Optional[Callable[[StationId, StationId], List[StationId]]] = None

        # Datos en memoria para la UI
        self.stations_list: List[StationId] = []
        self.stations_xy: Dict[StationId, Point] = {}
        self.edges: List[Edge] = []

        self._build_ui()
        self._connect_signals()
        self._apply_fusion_dark_palette()

    # ---------- UI ----------
    def _build_ui(self):
        central = QtWidgets.QWidget(self) #crea el contenedor principal, es el widget central
        self.setCentralWidget(central) #establece el contenedor
        main_layout = QtWidgets.QHBoxLayout(central) #crea un objeto y lo aplica al widget central

        # Panel izquierdo (controles)
        left_panel = QtWidgets.QVBoxLayout()
        main_layout.addLayout(left_panel, 0)

        title = QtWidgets.QLabel("Planificador Metro CDMX")
        #title.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        left_panel.addWidget(title)

        # Origen / Destino
        form = QtWidgets.QFormLayout() #crea el gestor de diseño del formulario
        self.cmb_origen = QtWidgets.QComboBox()
        self.cmb_destino = QtWidgets.QComboBox()
        self.cmb_origen.setEditable(True)   # permite escribir para filtrar
        self.cmb_destino.setEditable(True)
        form.addRow("Origen:", self.cmb_origen)
        form.addRow("Destino:", self.cmb_destino)
        left_panel.addLayout(form)

        # Botones
        btn_row = QtWidgets.QHBoxLayout() #contenedor que coloca widgets (en este caso en horizontal)
        self.btn_cargar = QtWidgets.QPushButton("Cargar datos")
        self.btn_calcular = QtWidgets.QPushButton("Calcular ruta")
        self.btn_limpiar = QtWidgets.QPushButton("Limpiar ruta")
        btn_row.addWidget(self.btn_cargar)
        btn_row.addWidget(self.btn_calcular)
        btn_row.addWidget(self.btn_limpiar)
        left_panel.addLayout(btn_row)

        # Info de ruta
        self.lbl_resumen = QtWidgets.QLabel("Ruta: —")
        self.lbl_resumen.setWordWrap(True)
        left_panel.addWidget(self.lbl_resumen)

        self.steps_list = QtWidgets.QListWidget()
        #self.steps_list.setMinimumWidth(320)
        left_panel.addWidget(self.steps_list) #, 1) #peso uno y el widget se expande.

        # Panel derecho (mapa)
        right_panel = QtWidgets.QVBoxLayout()
        main_layout.addLayout(right_panel, 1)

        self.map = MapView()
        right_panel.addWidget(self.map, 1)

        # Barra de estado
        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Listo • Carga datos para empezar")

    def _connect_signals(self):
        self.btn_cargar.clicked.connect(self.on_load_data)
        self.btn_calcular.clicked.connect(self.on_calculate)
        self.btn_limpiar.clicked.connect(self.on_clear)
        self.route_requested.connect(self._handle_route_requested)

    # ---------- Integración (hooks) ----------
    def set_data_loader(self, loader: Callable[[], Tuple[List[StationId], Dict[StationId, Point], List[Edge]]]):
        """Inyecta función que devuelve (stations_list, stations_xy, edges)."""
        self._data_loader = loader

    def set_route_finder(self, finder: Callable[[StationId, StationId], List[StationId]]):
        """Inyecta función A* que recibe (origen, destino) y devuelve lista de StationId."""
        self._route_finder = finder

    # ---------- Slots ----------
    @QtCore.Slot()
    def on_load_data(self):
        if not self._data_loader:
            QtWidgets.QMessageBox.warning(self, "Falta loader", "Conecta set_data_loader() desde tu módulo de API.")
            return
        try:
            stations, stations_xy, edges = self._data_loader()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error cargando datos", str(e))
            return

        self.stations_list = stations
        self.stations_xy = stations_xy
        self.edges = edges

        self.cmb_origen.clear()
        self.cmb_destino.clear()
        self.cmb_origen.addItems(self.stations_list)
        self.cmb_destino.addItems(self.stations_list)

        self.map.draw_network(self.stations_xy, self.edges)
        self.status.showMessage(f"Estaciones: {len(stations)} · Conexiones: {len(edges)}")

    @QtCore.Slot()
    def on_calculate(self):
        origen = self.cmb_origen.currentText().strip()
        destino = self.cmb_destino.currentText().strip()
        if not origen or not destino:
            QtWidgets.QMessageBox.information(self, "Faltan datos", "Selecciona origen y destino.")
            return
        if origen == destino:
            QtWidgets.QMessageBox.information(self, "Atención", "Origen y destino son iguales.")
            return
        self.route_requested.emit(origen, destino)

    @QtCore.Slot()
    def on_clear(self):
        self.steps_list.clear()
        self.lbl_resumen.setText("Ruta: —")
        self.map.draw_network(self.stations_xy, self.edges)
        self.status.showMessage("Limpio")

    @QtCore.Slot(str, str)
    def _handle_route_requested(self, origen: str, destino: str):
        if not self._route_finder:
            QtWidgets.QMessageBox.warning(self, "Falta A*", "Conecta set_route_finder() con tu implementación.")
            return
        try:
            path = self._route_finder(origen, destino)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error en ruta", str(e))
            return

        if not path:
            QtWidgets.QMessageBox.information(self, "Sin ruta", "No se encontró una ruta entre esas estaciones.")
            return

        # Mostrar pasos
        self.steps_list.clear()
        for stationid in path:
            self.steps_list.addItem(stationid)
        self.lbl_resumen.setText(f"Ruta: {len(path)-1} saltos · {path[0]} → {path[-1]}")

        # Pintar sobre el mapa
        self.map.draw_network(self.stations_xy, self.edges)
        self.map.draw_route(self.stations_xy, path)

    # ---------- Estética opcional ----------
    def _apply_fusion_dark_palette(self):
        QtWidgets.QApplication.setStyle("Fusion")
        palette = QtGui.QPalette()
        base = QtGui.QColor(40, 40, 40)
        alt = QtGui.QColor(53, 53, 53)
        text = QtGui.QColor(220, 220, 220)
        accent = QtGui.QColor(64, 128, 255)
        palette.setColor(QtGui.QPalette.Window, alt)
        palette.setColor(QtGui.QPalette.WindowText, text)
        palette.setColor(QtGui.QPalette.Base, base)
        palette.setColor(QtGui.QPalette.AlternateBase, alt)
        palette.setColor(QtGui.QPalette.ToolTipBase, text)
        palette.setColor(QtGui.QPalette.ToolTipText, text)
        palette.setColor(QtGui.QPalette.Text, text)
        palette.setColor(QtGui.QPalette.Button, alt)
        palette.setColor(QtGui.QPalette.ButtonText, text)
        palette.setColor(QtGui.QPalette.Highlight, accent)
        palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.white)
        self.setPalette(palette)


# --------- Ejemplo mínimo de integración ---------
# Quita esto y conecta tus módulos reales en main()

def dummy_loader() -> Tuple[List[StationId], Dict[StationId, Point], List[Edge]]:
    """Crea una mini red de juguete para ver la UI funcionando."""
    stations = ["A", "B", "C", "D", "E"]
    stations_xy = {
        "A": (0.0, 0.0),
        "B": (100.0, 0.0),
        "C": (200.0, 0.0),
        "D": (200.0, 100.0),
        "E": (100.0, 100.0),
    }
    edges = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "B")]
    return stations, stations_xy, edges


def dummy_route_finder(origen: StationId, destino: StationId) -> List[StationId]:
    # Ruta ficticia (en el proyecto real, inyecta tu A*)
    if origen == "A" and destino == "D":
        return ["A", "B", "C", "D"]
    return [origen, destino]


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()

    # Conectar "módulos" (sustituye por los reales de tu equipo)
    win.set_data_loader(dummy_loader)
    win.set_route_finder(dummy_route_finder)

    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
