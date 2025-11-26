from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from config import colores_lineas
from aestrella import G_mexico, convertir_distancia_a_tiempo

class WidgetItemLineaTiempo(QtWidgets.QWidget):
    """
    Widget visual para un nodo en la línea de tiempo vertical.
    Muestra:
      - Columna central: Línea vertical (arriba/abajo) y nodo central (círculo).
      - Columna derecha: Texto principal y secundario.
    """
    def __init__(self, 
                 color_nodo, 
                 color_linea_superior=None, estilo_linea_superior=Qt.SolidLine,
                 color_linea_inferior=None, estilo_linea_inferior=Qt.SolidLine,
                 texto_principal="", texto_secundario=None, texto_linea_inferior=None,
                 es_transbordo=False,
                 parent=None):
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
        
        # Altura fija suficiente para mostrar texto y conectar líneas
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
        
        # --- DIBUJAR LÍNEAS VERTICALES ---
        
        # Línea Superior (desde arriba hasta el centro)
        if self.color_linea_superior:
            pluma = QtGui.QPen(QtGui.QColor(self.color_linea_superior))
            pluma.setWidth(ancho_linea)
            pluma.setStyle(self.estilo_linea_superior)
            painter.setPen(pluma)
            painter.drawLine(centro_x, 0, centro_x, centro_y)
            
        # Línea Inferior (desde el centro hasta abajo)
        if self.color_linea_inferior:
            pluma = QtGui.QPen(QtGui.QColor(self.color_linea_inferior))
            pluma.setWidth(ancho_linea)
            pluma.setStyle(self.estilo_linea_inferior)
            painter.setPen(pluma)
            painter.drawLine(centro_x, centro_y, centro_x, self.height())
            
        # --- DIBUJAR NODO CENTRAL ---
        # Círculo con borde blanco para separar de la línea
        painter.setPen(QtGui.QPen(Qt.white, 3))
        painter.setBrush(QtGui.QColor(self.color_nodo))
        painter.drawEllipse(QtCore.QPointF(centro_x, centro_y), radio_nodo, radio_nodo)
        
        # --- DIBUJAR TEXTO PRINCIPAL Y SECUNDARIO ---
        # El texto va a la derecha de la línea central
        x_texto = centro_x + 25
        rect_texto = QtCore.QRect(x_texto, 0, ancho_widget - x_texto - 10, self.height())
        
        # Fuente Principal
        fuente_principal = QtGui.QFont("Segoe UI", 12, QtGui.QFont.Bold)
        painter.setFont(fuente_principal)
        painter.setPen(QtGui.QColor("#305853"))
        
        fm_principal = QtGui.QFontMetrics(fuente_principal)
        alto_principal = fm_principal.height()
        
        # Calcular posición Y para texto principal/secundario (centrado en el nodo)
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
            # Solo texto principal
            y_inicio = centro_y + (fm_principal.ascent() / 2) - 2
            painter.drawText(x_texto, y_inicio, self.texto_principal)

        # --- DIBUJAR TEXTO DE LÍNEA INFERIOR (TRANSBORDO) ---
        if self.texto_linea_inferior:
            # Este texto se dibuja centrado verticalmente en la mitad inferior del widget
            # y a la derecha de la línea
            y_centro_inferior = centro_y + (self.height() - centro_y) / 2
            
            fuente_inferior = QtGui.QFont("Segoe UI", 10)
            fuente_inferior.setItalic(True)
            painter.setFont(fuente_inferior)
            painter.setPen(QtGui.QColor("#666666")) # Gris oscuro
            
            fm_inferior = QtGui.QFontMetrics(fuente_inferior)
            y_texto_inf = y_centro_inferior + (fm_inferior.ascent() / 2)
            
            painter.drawText(x_texto, y_texto_inf, self.texto_linea_inferior)


class InfoPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Estilo del panel lateral
        self.setStyleSheet("background-color: white; border-left: 1px solid #ccc;")
        self.setFixedWidth(400) # Ancho fijo para el panel lateral
        
        self.layout_principal = QtWidgets.QVBoxLayout(self)
        self.layout_principal.setSpacing(10)
        self.layout_principal.setContentsMargins(20, 20, 20, 20)
        
        # Header
        self.lbl_total = QtWidgets.QLabel()
        self.lbl_total.setStyleSheet("font-size: 20px; font-weight: 900; color: #305853; margin-bottom: 10px;")
        self.lbl_total.setAlignment(Qt.AlignCenter)
        self.lbl_total.setWordWrap(True)
        self.layout_principal.addWidget(self.lbl_total)
        
        # Scroll Area
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.widget_contenido = QtWidgets.QWidget()
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
                background-color: #305853; 
                color: white; 
                padding: 10px; 
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #406863;
            }
        """)
        self.btn_cerrar.clicked.connect(self.hide)
        self.layout_principal.addWidget(self.btn_cerrar)

    def update_info(self, origen, destino, resultado_ruta, tiempo_entrada, tiempo_salida):
        # Limpiar layout anterior
        while self.layout_scroll.count():
            item = self.layout_scroll.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        # Actualizar Header
        tiempo_total = resultado_ruta["tiempo"]
        self.lbl_total.setText(f"Tiempo total: {tiempo_total}")
        
        ruta = resultado_ruta["ruta"]
        ruta_cruda = resultado_ruta.get("ruta_cruda", [])
        if not ruta_cruda:
            ruta_cruda = ruta
            
        # --- CONSTRUCCIÓN DE LA LÍNEA DE TIEMPO ---
        
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
