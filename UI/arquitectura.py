from __future__ import annotations
import sys
import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPolygonF, QBrush, QColor, QPen, QPainter
from metro_data import cargar_datos, calcular_ruta
from aestrella import trayecto_optimo_distancia, convertir_distancia_a_tiempo, G_mexico

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

# clase de panel derecho
class WidgetItemLineaTiempo(QtWidgets.QWidget):
    """
    Widget para un nodo en la línea de tiempo vertical.
    Muestra:
      - Columna central: Línea vertical (arriba/abajo) y nodo central (círculo).
      - Columna derecha: Texto principal y secundario.
    """
    def __init__(self, color_nodo, color_linea_superior=None, estilo_linea_superior=Qt.SolidLine, color_linea_inferior=None, 
                 estilo_linea_inferior=Qt.SolidLine, texto_principal="", texto_secundario=None, texto_linea_inferior=None, 
                 es_transbordo=False, parent=None):
        super().__init__(parent)
        self.color_nodo = color_nodo
        self.color_linea_superior = color_linea_superior
        self.estilo_linea_superior = estilo_linea_superior
        self.color_linea_inferior = color_linea_inferior
        self.estilo_linea_inferior = estilo_linea_inferior
        self.texto_principal = texto_principal
        self.texto_secundario = texto_secundario
        self.texto_linea_inferior = texto_linea_inferior
        self.es_transbordo = es_transbordo
        
        # Altura fija para mostrar texto y conectar líneas
        self.setMinimumHeight(80)
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Dimensiones
        ancho_widget = self.width()
        centro_x = 40 # Margen fijo izquierdo para la línea
        
        ancho_linea = 6
        radio_nodo = 8
        if self.es_transbordo:
            radio_nodo = 6 
        
        centro_y = self.height() / 2
        
        # LÍNEAS VERTICALES
        # Línea desde arriba hasta el centro
        if self.color_linea_superior:
            pluma = QtGui.QPen(QtGui.QColor(self.color_linea_superior))
            pluma.setWidth(ancho_linea)
            pluma.setStyle(self.estilo_linea_superior)
            painter.setPen(pluma)
            painter.drawLine(centro_x, 0, centro_x, centro_y)
            
        # Línea desde el centro hasta abajo
        if self.color_linea_inferior:
            pluma = QtGui.QPen(QtGui.QColor(self.color_linea_inferior))
            pluma.setWidth(ancho_linea)
            pluma.setStyle(self.estilo_linea_inferior)
            painter.setPen(pluma)
            painter.drawLine(centro_x, centro_y, centro_x, self.height())
            
        # DIBUJAR NODO (estacion)
        painter.setPen(QtGui.QPen(Qt.white, 3))
        painter.setBrush(QtGui.QColor(self.color_nodo))
        painter.drawEllipse(QtCore.QPointF(centro_x, centro_y), radio_nodo, radio_nodo)
        
        #  TEXTO
        x_texto = centro_x + 25
        rect_texto = QtCore.QRect(x_texto, 0, ancho_widget - x_texto - 10, self.height())
        
        # texto Principal
        fuente_principal = QtGui.QFont("Segoe UI", 12, QtGui.QFont.Bold)
        painter.setFont(fuente_principal)
        painter.setPen(QtGui.QColor("#b06821"))
        
        fm_principal = QtGui.QFontMetrics(fuente_principal)
        alto_principal = fm_principal.height()
        
        # Calcular posición Y para texto (centrado en el nodo)
        if self.texto_secundario:
            fuente_secundaria = QtGui.QFont("Segoe UI", 10)
            fm_secundaria = QtGui.QFontMetrics(fuente_secundaria)
            alto_secundaria = fm_secundaria.height()
            
            alto_total_texto = alto_principal + alto_secundaria + 2
            y_inicio = centro_y - (alto_total_texto / 2) + fm_principal.ascent()
            
            painter.drawText(x_texto, y_inicio, self.texto_principal)
            
            painter.setFont(fuente_secundaria)
            painter.setPen(QtGui.QColor("#666666"))
            painter.drawText(x_texto, y_inicio + alto_secundaria + 2, self.texto_secundario)
        else:
            y_inicio = centro_y + (fm_principal.ascent() / 2) - 2
            painter.drawText(x_texto, y_inicio, self.texto_principal)

        #  TEXTO DE TRANSBORDO
        if self.texto_linea_inferior:
            y_centro_inferior = centro_y + (self.height() - centro_y) / 2
            
            fuente_inferior = QtGui.QFont("Segoe UI", 10)
            fuente_inferior.setItalic(True)
            painter.setFont(fuente_inferior)
            painter.setPen(QtGui.QColor("#666666"))
            
            fm_inferior = QtGui.QFontMetrics(fuente_inferior)
            y_texto_inf = y_centro_inferior + (fm_inferior.ascent() / 2)
            
            painter.drawText(x_texto, y_texto_inf, self.texto_linea_inferior)

# JORGE
# clase para definir el panel derecho de informacion
class InfoPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(400)
        self.layout_principal = QtWidgets.QVBoxLayout(self)
        self.layout_principal.setSpacing(10)
        self.layout_principal.setContentsMargins(20, 20, 20, 20)
        
        # TIEMPO TOTAL
        self.lbl_total = QtWidgets.QLabel()
        self.lbl_total.setStyleSheet("font-size: 20px; font-weight: 700; color: #b06821; margin-bottom: 10px;")
        self.lbl_total.setAlignment(Qt.AlignLeft)
        self.lbl_total.setWordWrap(True)
        self.layout_principal.addWidget(self.lbl_total)
        
        # RUTA EN LINEA
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setStyleSheet("background: transparent; background-color: transparent;")
        self.widget_contenido = QtWidgets.QWidget()
        self.widget_contenido.setAttribute(Qt.WA_StyledBackground, True)
        self.widget_contenido.setStyleSheet("background-color: #1b2a30; border-radius: 15px;")
        self.layout_scroll = QtWidgets.QVBoxLayout(self.widget_contenido)
        self.layout_scroll.setSpacing(0)
        self.layout_scroll.setContentsMargins(0, 0, 0, 0)
        self.scroll.setWidget(self.widget_contenido)
        self.layout_principal.addWidget(self.scroll)
        
        # Botón Cerrar
        self.btn_cerrar = QtWidgets.QPushButton("Cerrar")
        self.btn_cerrar.setCursor(Qt.PointingHandCursor)
        self.btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #511b18; 
                color:#AAAAAA ; 
                padding: 10px; 
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #305853;
            }
        """)
        self.btn_cerrar.clicked.connect(self.hide)
        self.layout_principal.addWidget(self.btn_cerrar)

    def update_info(self, origen, destino, resultado_ruta, tiempo_entrada, tiempo_salida):
        while self.layout_scroll.count():
            item = self.layout_scroll.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        # Actualizar Header
        tiempo_total = resultado_ruta["tiempo"]
        self.lbl_total.setText(f"    🌮    Tiempo total: {tiempo_total}")
        
        ruta = resultado_ruta["ruta"]
        ruta_cruda = resultado_ruta.get("ruta_cruda", [])
        if not ruta_cruda:
            ruta_cruda = ruta
            
        # CONSTRUCCIÓN DE LA LÍNEA DE TIEMPO
        
        # 1. NODO INICIAL: Boca de metro
        primer_nodo = ruta_cruda[0]
        codigo_primera_linea = self.obtener_codigo_linea(primer_nodo)
        color_primera_linea = colores_lineas.get(codigo_primera_linea, colores_lineas["Default"])
        
        item_entrada = WidgetItemLineaTiempo(
            color_nodo=colores_lineas["Entry"],
            color_linea_superior=None,
            color_linea_inferior=colores_lineas["Entry"],
            estilo_linea_inferior=Qt.DotLine,
            texto_principal=f"Boca de metro: {origen}",
            texto_secundario=f"Caminando al andén ({tiempo_entrada})"
        )
        self.layout_scroll.addWidget(item_entrada)
        
        color_salida_previo = colores_lineas["Entry"]
        estilo_salida_previo = Qt.DotLine
        
        for i, nodo_crudo in enumerate(ruta_cruda):
            nombre_nodo = ruta[i]
            codigo_linea = self.obtener_codigo_linea(nodo_crudo)
            color_linea = colores_lineas.get(codigo_linea, colores_lineas["Default"])
            
            color_salida = None
            estilo_salida = Qt.SolidLine
            texto_secundario = None
            texto_linea_inferior = None
            
            if i < len(ruta_cruda) - 1:
                siguiente_nodo_crudo = ruta_cruda[i+1]
                siguiente_nombre_nodo = ruta[i+1]
                
                if siguiente_nombre_nodo == nombre_nodo:
                    # ES UN TRANSBORDO (Inicio)
                    color_salida = colores_lineas["Transfer"] 
                    estilo_salida = Qt.DotLine
                    
                    # Calcular tiempo transbordo
                    try:
                        dist = G_mexico[nodo_crudo][siguiente_nodo_crudo]['weight']
                        tiempo = convertir_distancia_a_tiempo(dist)
                        # AQUI ESTA EL CAMBIO: Texto en la línea inferior
                        texto_linea_inferior = f"Transbordo a pie ({tiempo})"
                    except:
                        texto_linea_inferior = "Transbordo"
                        
                else:
                    # VIAJE NORMAL
                    color_salida = color_linea
                    estilo_salida = Qt.SolidLine
            else:
                # ÚLTIMO NODO DE METRO
                color_salida = colores_lineas["Entry"]
                estilo_salida = Qt.DotLine
            
            # Crear Widget
            item = WidgetItemLineaTiempo(
                color_nodo=color_linea,
                color_linea_superior=color_salida_previo,
                estilo_linea_superior=estilo_salida_previo,
                color_linea_inferior=color_salida,
                estilo_linea_inferior=estilo_salida,
                texto_principal=nombre_nodo,
                texto_secundario=texto_secundario,
                texto_linea_inferior=texto_linea_inferior, # Pasamos el texto centrado
                es_transbordo=(estilo_salida == Qt.DotLine and i < len(ruta_cruda) - 1) 
            )
            self.layout_scroll.addWidget(item)
            
            color_salida_previo = color_salida
            estilo_salida_previo = estilo_salida
            
        # --- NODO FINAL: Salida a la calle ---
        item_salida = WidgetItemLineaTiempo(
            color_nodo=colores_lineas["Entry"],
            color_linea_superior=colores_lineas["Entry"],
            estilo_linea_superior=Qt.DotLine,
            color_linea_inferior=None,
            texto_principal=f"Calle: {destino}",
            texto_secundario=f"Saliendo del metro ({tiempo_salida})"
        )
        self.layout_scroll.addWidget(item_salida)
        
        self.layout_scroll.addStretch()

    def obtener_codigo_linea(self, nombre_nodo):
        if "_L" in nombre_nodo:
            return "L" + nombre_nodo.split("_L")[1]
        return "Default"


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
        self.last_route_result = None
        
        # Data
        self.stations_list = []
        self.stations_xy = {}
        self.edges = []
        self.tiempos_entrada = {}

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

        # PANEL IZQUIERDO (controles)
        # Contenedor para darle color de fondo específico
        left_container = QtWidgets.QWidget()
        left_container.setObjectName("SidePanel")  # ID para CSS
        left_container.setFixedWidth(350)  # Ancho fijo

        left_layout = QtWidgets.QVBoxLayout(left_container)
        left_layout.setContentsMargins(20, 30, 20, 30)  # Margen para widgets
        left_layout.setSpacing(15) # espaciado entre widgets

        # LOGO (IMAGEN)
        # 1. Crear la etiqueta que contendrá la imagen
        lbl_logo = QtWidgets.QLabel()

        # 2. Cargar el archivo de imagen
        logo_path = directorio_root / "UI" / "assets" / "metro.png"
        pixmap_logo = QtGui.QPixmap(str(logo_path))

        # 4. Escalar la imagen.
        scaled_pixmap = pixmap_logo.scaledToHeight(100, Qt.SmoothTransformation) # el ancho se ajusta automaticamente
        lbl_logo.setPixmap(scaled_pixmap)

        # 5. Centramos la imagen en el panel izq.
        lbl_logo.setAlignment(Qt.AlignCenter)

         # 6. Añadimos la imagen al layout vertical
        left_layout.addWidget(lbl_logo)


        # TITULO y SUBTITULO
        title = QtWidgets.QLabel("METRO CDMX")
        title.setStyleSheet("font-size: 24px; font-weight: 900; color: #B06821; letter-spacing: 2px;")
        left_layout.addWidget(title)
        title.setAlignment(Qt.AlignCenter)

        subtitle = QtWidgets.QLabel("Planificador de Ruta 🇲🇽")
        subtitle.setStyleSheet("color: #305853; font-size: 14px; margin-bottom: 11px;")
        left_layout.addWidget(subtitle)
        subtitle.setAlignment(Qt.AlignCenter)

        # BUSCADORES DE ORIGEN Y DESTINO
        self.cmb_origen = QtWidgets.QComboBox()
        self.cmb_origen.setPlaceholderText("Selecciona Origen...")
        self.cmb_destino = QtWidgets.QComboBox()
        self.cmb_destino.setPlaceholderText("Selecciona Destino...")
        self.cmb_origen.setEditable(True)
        self.cmb_destino.setEditable(True)

        # icono de la flecha dorada para el dropdown
        flecha_path = directorio_root / "UI" / "assets" / "flecha_dorada.png"
        if flecha_path.exists():
            icon_flecha = QtGui.QIcon(str(flecha_path))
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

        # BOTON CALCULAR RUTA
        self.btn_calcular = QtWidgets.QPushButton("CALCULAR RUTA")
        self.btn_calcular.setCursor(Qt.PointingHandCursor)
        left_layout.addWidget(self.btn_calcular)

        # LINEA HORIZONTAL PARA SEPARAR 
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("color: #305853;")
        left_layout.addWidget(line)

        # RESULTADOS
        self.lbl_resumen = QtWidgets.QLabel("Esperando ruta...")
        self.lbl_resumen.setStyleSheet("font-size: 14px; font-style: italic; color: #305853;")
        self.lbl_resumen.setWordWrap(True)
        left_layout.addWidget(self.lbl_resumen)

        self.steps_list = QtWidgets.QListWidget()
        left_layout.addWidget(self.steps_list)

        # BOTONES LIMPIAR / INFO.
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_info = QtWidgets.QPushButton("Información")
        self.btn_info.setCursor(Qt.PointingHandCursor)
        self.btn_info.setStyleSheet("background-color: #305853; color: white;")
        self.btn_limpiar = QtWidgets.QPushButton("      Limpiar      ")
        self.btn_limpiar.setObjectName("btn_limpiar")  # ID para CSS
        self.btn_limpiar.setCursor(Qt.PointingHandCursor)

        # LOGO SOMBRERO
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

        # PANEL DERECHO (MAPA)
        # Crear un contenedor para el mapa
        map_container = QtWidgets.QWidget()
        map_layout = QtWidgets.QVBoxLayout(map_container)

        self.map = MapView()
        map_layout.addWidget(self.map, 1)

        # Añadir al layout principal
        main_layout.addWidget(left_container)
        main_layout.addWidget(map_container, 1)

        # Panel de información derecho, oculto inicialmente
        self.info_panel = InfoPanel(self)
        self.info_panel.setObjectName("InfoPanel")
        self.info_panel.setAttribute(Qt.WA_StyledBackground, True)
        self.info_panel.hide()
        main_layout.addWidget(self.info_panel)

        # status bar con precio
        self.status = QtWidgets.QStatusBar()
        self.status_label = QtWidgets.QLabel("Precio por billete: $5 pesos mexicanos")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #AAAAAA;")
        self.status.addWidget(self.status_label, 1)
        self.setStatusBar(self.status)

    def _connect_signals(self):
        self.btn_calcular.clicked.connect(self.on_calculate)
        self.btn_limpiar.clicked.connect(self.on_clear)
        self.route_requested.connect(self._handle_route_requested)
        self.btn_info.clicked.connect(self.on_toggle_info)

    @QtCore.Slot()
    def on_toggle_info(self):
        if self.info_panel.isVisible():
            self.info_panel.hide()
        else:
            self.info_panel.show()

    def set_data_loader(self, loader: Callable):
        self._data_loader = loader

    def set_route_finder(self, finder: Callable):
        self._route_finder = finder

    @QtCore.Slot()
    def on_load_data(self):
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
        except Exception as e:
            self.status.showMessage(f"Error: {str(e)}")

    def crear_icono_circulo(self, color_hex: str, tamano: int = 16) -> QtGui.QIcon:
        """
        Crea un icono circular de color_hex. Se usa para mostrar el color de la línea en la lista de pasos.
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
        self.route_requested.emit(origen, destino)

    @QtCore.Slot()
    def on_clear(self):
        self.steps_list.clear()
        self.lbl_resumen.setText("Esperando ruta...")
        self.last_route_result = None # Limpiar el resultado de la ruta
        self.map.draw_network(self.stations_xy, self.edges)  # Redibuja limpio
        self.cmb_origen.setCurrentIndex(-1) # borra caja de origen
        self.cmb_destino.setCurrentIndex(-1) # borra caja de destino
        self.info_panel.hide() # oculta ruta calculada


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
        num_transbordos=0
        
        for i, nombre_estacion in enumerate(ruta):
            # Si es la misma estación que la anterior, la saltamos visualmente (ya se mostró como transbordo)
            if i > 0 and ruta[i] == ruta[i-1]:
                continue

            # Determinar color por defecto
            color_hex = colores_lineas["Default"]

            # Obtener nodo crudo actual (con información de línea)
            nodo_crudo = ruta_cruda[i]

            # transbordo
            # Si la estación actual tiene el mismo nombre que la anterior o la siguiente, es un transbordo
            es_transbordo = False

            # comprobamos estación anterior y siguiente
            if (i>0 and ruta[i-1] == nombre_estacion) or (i < len(ruta) - 1 and ruta[i+1] == nombre_estacion):
                es_transbordo = True
                num_transbordos += 1

            if es_transbordo:
                # Si es transbordo, usamos el color definido en config
                color_hex = colores_lineas["Transfer"]
            else:
                # sacar línea del nodo_crudo (Observatorio_L1 -> L1)
                if "_L" in nodo_crudo:
                    partes = nodo_crudo.split("_L")
                    codigo_linea = "L" + partes[1]
                    color_hex = colores_lineas.get(codigo_linea, colores_lineas["Default"]) 

            # Creamos la lista
            icono = self.crear_icono_circulo(color_hex)
            texto_item = f"{contador_visual}. {nombre_estacion}"
            if es_transbordo:
                texto_item += " (Transbordo)"

            elemento = QtWidgets.QListWidgetItem(texto_item)
            elemento.setIcon(icono)
            self.steps_list.addItem(elemento)

            contador_visual += 1


        # Calcular número de estaciones (restamos nº de transbordos pq es la misma estacion)
        num_estaciones = len(ruta) - num_transbordos
        self.lbl_resumen.setText(f"🦅 Ruta calculada: {num_estaciones} estaciones")
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

# VARIABLES GLOBALES (para datos del metro, se cargarán al iniciar la aplicación)
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

    font = QtGui.QFont("Segoe UI", 10) # definimos fuente y tamaño
    app.setFont(font)

    win = MainWindow()

    #cargamos datos
    win.set_data_loader(load_metro_data) 
    win.set_route_finder(find_metro_route)
    win.on_load_data()

    win.show()

    sys.exit(app.exec())