from __future__ import annotations
import sys
import os
import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple, Optional
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPolygonF, QBrush, QColor, QPen, QPainter
from metro_data import cargar_datos, calcular_ruta
from aestrella import trayecto_optimo_distancia, convertir_distancia_a_tiempo, G_mexico
from informacion import InfoPanel

# Obtener el directorio raíz del proyecto
directorio_root = Path(__file__).parent.parent.resolve()


#  FUNCIÓN PARA CARGAR ESTILOS CSS jorge


def cargar_estilos():
    """Carga los estilos CSS desde el archivo externo estilos.css"""
    css_path = directorio_root / "UI" / "estilos.css"
    if css_path.exists():
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        print(f"Advertencia: No se encontró el archivo CSS en {css_path}")
        return ""

# Tipos simples
StationId = str
Point = Tuple[float, float]
Edge = Tuple[StationId, StationId]

from config import colores_lineas


class StationItem(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, x, y, radius, name, pen, brush):
        # Dibujamos el círculo centrado en el (0,0) local
        # creamos un círculo cuyo centro es el origen.
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)

        # Ahora movemos el item a su posición en el mapa
        self.setPos(x, y)
        self.setPen(pen)
        self.setBrush(brush)
        self.radius = radius

        #Para que aparezca el nombre de la estación al poner el cursor encima de cada nodo:
        self.setAcceptHoverEvents(True)
        self.text_item = QtWidgets.QGraphicsTextItem(name, self)
        self.text_item.setDefaultTextColor(QColor("#AAAAAA"))

        #Usamos html para hacerlo de forma más directa
        self.text_item.setHtml(
            f"<div style='background-color: #511b18; padding: 8px; border-radius: 8px;'>{name}</div>")

        font = QtGui.QFont("Segoe UI", 14)
        self.text_item.setFont(font)

        # Esto hace que el texto siempre se vea del mismo tamaño, independientemente del zoom
        self.text_item.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations)

        # Ocultar inicialmente etiquetas de nombre
        self.text_item.setVisible(False)

    # funcion para que al poner el cursor sobre un boton cambie a un dedito y se vea el texto
    def hoverEnterEvent(self, event):
        self.setCursor(Qt.PointingHandCursor)
        self.text_item.setVisible(True)
        #super().hoverEnterEvent(event)

    # funcion para lo contrario que la anterior, al quitar el cursor vuelva a lo original
    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        self.text_item.setVisible(False)
        #super().hoverLeaveEvent(event)

# clase para el lado derecho de la interfaz (parte del mapa)
class MapView(QtWidgets.QGraphicsView):

    def __init__(self, parent=None):
        super().__init__(parent)
        #color fondo del mapa
        self.setScene(QtWidgets.QGraphicsScene(self))
        self.setBackgroundBrush(QBrush(QColor("#1B2A30")))

        # CALIDAD GRÁFICA: para que no se vea pixelado
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)

        # Navegación
        # que se pueda 'arrastrar' el mapa
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        # que el zoom no sea al centro sino a donde esta el raton
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        # que al redimensionar la ventana, lo que está debajo del raton siga ahi
        # nota: podemos probar a ver como se ve quitando esto pq no entiendo muy biwn quw hace
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

        # Quitamos los bordes blancos, que no haya margen
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    # funcion para hacer y deshacer zoom
    def wheelEvent(self, event):
        zoom_in_factor = 1.1
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() < 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def draw_network(
            self,
            stations_xy: Dict[StationId, Point],
            edges: List[Edge],
            station_radius: float = 18.0,  # Estaciones un poco más grandes
    ) -> None:
        scene = self.scene()
        scene.clear()

        # 1. Dibujar aristas
        pen_edge = QPen(QColor("#B06821"))
        pen_edge.setWidthF(10.0)  # Líneas más gruesas
        pen_edge.setCapStyle(Qt.RoundCap)  # Bordes de línea redondeados

        for a, b in edges:
            if a in stations_xy and b in stations_xy:
                xa, ya = stations_xy[a]
                xb, yb = stations_xy[b]
                scene.addLine(xa, ya, xb, yb, pen_edge)

        # 2. Dibujar estaciones
        brush_station = QBrush(QColor("#E0FFFF"))
        pen_station = QPen(QColor("#511B18"))
        pen_station.setWidthF(10.0)

        for stationid, (x, y) in stations_xy.items():
            # En lugar de dibujar un circulito, instanciamos clase la clase Stationitem pa que aparezca el nombre
            station_item = StationItem(x, y, station_radius, stationid, pen_station, brush_station)
            scene.addItem(station_item)

        self.fitInView(scene.itemsBoundingRect().marginsAdded(QtCore.QMarginsF(50, 50, 50, 50)), Qt.KeepAspectRatio)

    # funcion para dibujar la ruta calculada
    def draw_route(self, stations_xy: Dict[StationId, Point], path: List[StationId]) -> None:
        if not path:
            return
        scene = self.scene()

        # Usamos un azul clarito para que resalte
        route_color = QColor("#ADD8E6")

        # una línea gruesa debajo mas fuerte para que destaque mas
        pen_glow = QPen(route_color)
        pen_glow.setWidthF(12.0)
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

                # Dibujar linea gruesa
                scene.addLine(xa, ya, xb, yb, pen_glow)
                # Dibujar línea central
                scene.addLine(xa, ya, xb, yb, pen_route)

                # Flecha de direccion
                dx = xb - xa
                dy = yb - ya
                angle = math.atan2(dy, dx)

                # Posicionamos la flecha a mitad de camino
                mid_x = (xa + xb) / 2
                mid_y = (ya + yb) / 2

                arrow_size = 8
                p1 = QPointF(mid_x + arrow_size * math.cos(angle), mid_y + arrow_size * math.sin(angle))
                p2 = QPointF(mid_x + arrow_size * math.cos(angle + 2.6), mid_y + arrow_size * math.sin(angle + 2.6))
                p3 = QPointF(mid_x + arrow_size * math.cos(angle - 2.6), mid_y + arrow_size * math.sin(angle - 2.6))

                arrow_head = QtWidgets.QGraphicsPolygonItem(QPolygonF([p1, p2, p3]))
                arrow_head.setBrush(QBrush(QColor("#E0FFFF")))
                arrow_head.setPen(Qt.NoPen)
                scene.addItem(arrow_head)

# clase para definir la ventana en general
class MainWindow(QtWidgets.QMainWindow):
    route_requested = QtCore.Signal(str, str)

    # definimos titulo
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Metro CDMX")
        self.resize(1280, 800)

        # Hooks
        self._data_loader = None
        self._route_finder = None

        # Data
        self.stations_list = []
        self.stations_xy = {}
        self.edges = []
        self.tiempos_entrada = {} # Nuevo: Tiempos de entrada a estaciones

        # Estado
        self.last_route_result = None # Para guardar el resultado de la última ruta calculada

        self._build_ui()
        self._connect_signals()

        # aplicamos el CSS GLOBAL
        self.setStyleSheet(cargar_estilos())

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

        # --- NUEVO BLOQUE PARA EL LOGO (IMAGEN) ---
        # 1. Crear la etiqueta que contendrá la imagen
        lbl_logo = QtWidgets.QLabel()

        # 2. Cargar el archivo de imagen desde la ruta absoluta
        logo_path = directorio_root / "UI" / "assets" / "metro.png"
        pixmap_logo = QtGui.QPixmap(str(logo_path))

        # 3. Verificar si la imagen cargó correctamente
            # 4. Escalar la imagen.
            # "scaledToHeight(100)" hace que tenga 100px de alto y el ancho se ajuste automático.
            # Ajusta ese '100' si la quieres más grande o más pequeña.
        scaled_pixmap = pixmap_logo.scaledToHeight(100, Qt.SmoothTransformation)
        lbl_logo.setPixmap(scaled_pixmap)

            # 5. (Opcional) Centrar la imagen en el panel lateral
        lbl_logo.setAlignment(Qt.AlignCenter)

            # 6. Añadir la imagen al layout vertical PRIMERO
        left_layout.addWidget(lbl_logo)




        # Título
        title = QtWidgets.QLabel("METRO CDMX")
        title.setStyleSheet("font-size: 24px; font-weight: 900; color: #B06821; letter-spacing: 2px;")
        left_layout.addWidget(title)
        title.setAlignment(Qt.AlignCenter)

        subtitle = QtWidgets.QLabel("Planificador de Ruta 🇲🇽")
        subtitle.setStyleSheet("color: #305853; font-size: 14px; margin-bottom: 11px;")
        left_layout.addWidget(subtitle)
        subtitle.setAlignment(Qt.AlignCenter)

        # Inputs
        self.cmb_origen = QtWidgets.QComboBox()
        self.cmb_origen.setPlaceholderText("Selecciona Origen...")
        self.cmb_destino = QtWidgets.QComboBox()
        self.cmb_destino.setPlaceholderText("Selecciona Destino...")
        self.cmb_origen.setEditable(True)
        self.cmb_destino.setEditable(True)

        # Configurar el icono de la flecha dorada para los ComboBox
        flecha_path = directorio_root / "UI" / "assets" / "flecha_dorada.png"
        if flecha_path.exists():
            icon_flecha = QtGui.QIcon(str(flecha_path))
            # Aplicar el estilo CSS con la imagen de la flecha
            combo_style = f"""
                QComboBox::down-arrow {{
                    image: url({str(flecha_path)});
                    width: 12px;
                    height: 12px;
                }}
            """
            self.cmb_origen.setStyleSheet(self.cmb_origen.styleSheet() + combo_style)
            self.cmb_destino.setStyleSheet(self.cmb_destino.styleSheet() + combo_style)

        lbl_orig = QtWidgets.QLabel("ORIGEN")
        lbl_orig.setStyleSheet("font-size: 12px; font-weight: bold; color: #305853;")
        left_layout.addWidget(lbl_orig)
        left_layout.addWidget(self.cmb_origen)

        lbl_dest = QtWidgets.QLabel("DESTINO")
        lbl_dest.setStyleSheet("font-size: 12px; font-weight: bold; color: #305853;")
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
        self.btn_info = QtWidgets.QPushButton("Información")
        self.btn_info.setCursor(Qt.PointingHandCursor)
        self.btn_info.setStyleSheet("background-color: #305853; color: white;")
        self.btn_limpiar = QtWidgets.QPushButton("      Limpiar      ")
        self.btn_limpiar.setObjectName("btn_limpiar")  # ID para CSS rojo
        self.btn_limpiar.setCursor(Qt.PointingHandCursor)

        sombrero = QtWidgets.QLabel()
        sombrero_path = directorio_root / "UI" / "assets" / "sombrero.png"
        logo_sombrero = QtGui.QPixmap(str(sombrero_path))
        scaled_sombrero = logo_sombrero.scaledToHeight(30, Qt.SmoothTransformation)
        sombrero.setPixmap(scaled_sombrero)
        sombrero.setAlignment(Qt.AlignCenter)




        btn_row.addWidget(self.btn_info)
        btn_row.addWidget(sombrero)
        btn_row.addWidget(self.btn_limpiar)
        left_layout.addLayout(btn_row)

        # --- FIN PANEL IZQUIERDO ---
        # --- PANEL DERECHO (MAPA) ---
        # Crear un contenedor para el mapa con overlay
        map_container = QtWidgets.QWidget()
        map_layout = QtWidgets.QVBoxLayout(map_container)
        map_layout.setContentsMargins(0, 0, 0, 0)
        map_layout.setSpacing(0)


        self.map = MapView()

        # Añadir widgets al contenedor del mapa
        map_layout.addWidget(self.map, 1)

        # Añadir al layout principal
        main_layout.addWidget(left_container)
        main_layout.addWidget(map_container, 1)  # 1 = estirar mapa todo lo posible

        # Panel de información (derecha, oculto inicialmente)
        self.info_panel = InfoPanel(self)
        self.info_panel.hide()
        main_layout.addWidget(self.info_panel)

        # Barra de estado minimalista
        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)

    def _connect_signals(self):
        self.btn_calcular.clicked.connect(self.on_calculate)
        self.btn_limpiar.clicked.connect(self.on_clear)
        self.btn_info.clicked.connect(self.on_show_info)
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
            stations, stations_xy, edges, _, _, _, _, tiempos_entrada = self._data_loader()
            self.stations_list = stations
            self.stations_xy = stations_xy
            self.edges = edges
            self.tiempos_entrada = tiempos_entrada

            self.cmb_origen.clear()
            self.cmb_destino.clear()
            self.cmb_origen.addItems(self.stations_list)
            self.cmb_destino.addItems(self.stations_list)

            self.map.draw_network(self.stations_xy, self.edges)
            self.status.showMessage(f"Sistema en línea • {len(stations)} estaciones operativas")
        except Exception as e:
            self.status.showMessage(f"Error: {str(e)}")

    def crear_icono_circulo(self, color_hex: str, tamano: int = 16) -> QtGui.QIcon:
        """
        Crea un icono circular del color especificado.
        Se usa para mostrar el color de la línea en la lista de pasos.
        """
        pixmap = QtGui.QPixmap(tamano, tamano)
        pixmap.fill(Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Dibujar círculo
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(color_hex))
        painter.drawEllipse(0, 0, tamano, tamano)

        painter.end()
        return QtGui.QIcon(pixmap)

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
        self.last_route_result = None # Limpiar el resultado de la ruta
        self.map.draw_network(self.stations_xy, self.edges)  # Redibuja limpio

    @QtCore.Slot(str, str)
    def _handle_route_requested(self, origen: str, destino: str):
        if not self._route_finder:
            return
        result = self._route_finder(origen, destino)
        if not result:
            self.lbl_resumen.setText("⚠ No hay ruta disponible.")
            self.last_route_result = None
            return

        # result es ahora un diccionario con 'ruta', 'distancia', y 'tiempo'
        self.last_route_result = result # Guardamos el resultado
        ruta = result["ruta"]
        ruta_cruda = result.get("ruta_cruda", []) # Obtener ruta con sufijos _L (ej: Observatorio_L1)
        tiempo = result["tiempo"]


        self.steps_list.clear()

        # Si no tenemos ruta_cruda (por compatibilidad), usamos ruta normal pero sin colores específicos
        if not ruta_cruda:
            ruta_cruda = ruta

        contador_visual = 1
        for i, nombre_estacion in enumerate(ruta):
            # Si es la misma estación que la anterior, la saltamos visualmente (ya se mostró como transbordo)
            if i > 0 and ruta[i] == ruta[i-1]:
                continue

            # Determinar color por defecto
            color_hex = colores_lineas["Default"]

            # Obtener nodo crudo actual (con información de línea)
            nodo_crudo = ruta_cruda[i]

            # Lógica para detectar transbordo:
            # Si la estación actual tiene el mismo nombre simple que la anterior o la siguiente, es un transbordo
            es_transbordo = False

            # Chequear estación anterior
            if i > 0:
                nombre_previo = ruta[i-1]
                if nombre_previo == nombre_estacion:
                    es_transbordo = True

            # Chequear estación siguiente
            if i < len(ruta) - 1:
                nombre_siguiente = ruta[i+1]
                if nombre_siguiente == nombre_estacion:
                    es_transbordo = True

            if es_transbordo:
                # Si es transbordo, usamos el color naranja
                color_hex = colores_lineas["Transfer"]
            else:
                # Extraer línea del nodo_crudo (ej: Observatorio_L1 -> L1)
                if "_L" in nodo_crudo:
                    partes = nodo_crudo.split("_L")
                    if len(partes) > 1:
                        codigo_linea = "L" + partes[1]
                        # Obtener el color correspondiente a la línea
                        color_hex = colores_lineas.get(codigo_linea, colores_lineas["Default"])

            # Crear icono con el color determinado
            icono = self.crear_icono_circulo(color_hex)

            # Crear item de la lista
            texto_item = f"{contador_visual}. {nombre_estacion}"
            if es_transbordo:
                texto_item += " (Transbordo)"

            elemento = QtWidgets.QListWidgetItem(texto_item)
            elemento.setIcon(icono)
            self.steps_list.addItem(elemento)

            contador_visual += 1

        # Calcular número de estaciones (restamos 1 porque n estaciones son n-1 tramos)
        num_estaciones = len(ruta) - 1
        self.lbl_resumen.setText(f"✔ Ruta calculada: {num_estaciones} estaciones")
        self.map.draw_network(self.stations_xy, self.edges)
        self.map.draw_route(self.stations_xy, ruta)

        # Mostrar panel de información automáticamente
        tiempo_entrada = self.tiempos_entrada.get(origen, "Desconocido")
        if isinstance(tiempo_entrada, (int, float)):
            tiempo_entrada_str = f"{tiempo_entrada} min"
        else:
            tiempo_entrada_str = str(tiempo_entrada)

        tiempo_salida = self.tiempos_entrada.get(destino, "Desconocido")
        if isinstance(tiempo_salida, (int, float)):
            tiempo_salida_str = f"{tiempo_salida} min"
        else:
            tiempo_salida_str = str(tiempo_salida)

        self.info_panel.update_info(origen, destino, self.last_route_result, tiempo_entrada_str, tiempo_salida_str)
        self.info_panel.show()

    @QtCore.Slot()
    def on_show_info(self):
        if not self.last_route_result:
            QtWidgets.QMessageBox.warning(self, "Información", "Primero debes calcular una ruta.")
            return

        origen = self.cmb_origen.currentText()
        destino = self.cmb_destino.currentText()

        # Obtener tiempo de entrada
        tiempo_entrada = self.tiempos_entrada.get(origen, "Desconocido")
        if isinstance(tiempo_entrada, (int, float)):
            tiempo_entrada_str = f"{tiempo_entrada} min"
        else:
            tiempo_entrada_str = str(tiempo_entrada)

        # Obtener tiempo de salida (usamos la misma tabla que entrada)
        tiempo_salida = self.tiempos_entrada.get(destino, "Desconocido")
        if isinstance(tiempo_salida, (int, float)):
            tiempo_salida_str = f"{tiempo_salida} min"
        else:
            tiempo_salida_str = str(tiempo_salida)

        self.info_panel.update_info(origen, destino, self.last_route_result, tiempo_entrada_str, tiempo_salida_str)
        self.info_panel.show()


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
    
    stations_list, stations_xy, edges_list, graph, heuristics_df, station_mapping, reverse_mapping, tiempos_entrada = cargar_datos()
    
    return stations_list, stations_xy, edges_list, graph, heuristics_df, station_mapping, reverse_mapping, tiempos_entrada


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