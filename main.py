import sys
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QListWidget,
    QVBoxLayout, QHBoxLayout, QLineEdit, QSpinBox, QFileDialog
)
from PyQt6.QtGui import QPixmap, QImage, QFontDatabase, QFont
from PyQt6.QtCore import Qt

# Rutas
CARPETA_FUENTES = "fuentes"
CARPETA_RESULTADOS = "resultados"
REMERA_BLANCA = "remera_blanca.png"
REMERA_NEGRA = "remera_negra.png"


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Estampado")

        os.makedirs(CARPETA_RESULTADOS, exist_ok=True)

        self.texto = "Texto de ejemplo"
        self.tamano = 50
        self.ruta_remera = REMERA_NEGRA
        self.ruta_fuente = None

        self.init_ui()
        self.cargar_fuentes()

    def init_ui(self):
        layout = QHBoxLayout()

        # -------- Panel izquierdo --------
        panel_izq = QVBoxLayout()

        self.input_texto = QLineEdit(self.texto)
        self.input_texto.textChanged.connect(self.actualizar_preview)

        self.spin_size = QSpinBox()
        self.spin_size.setValue(self.tamano)
        self.spin_size.valueChanged.connect(self.actualizar_preview)

        btn_blanca = QPushButton("Remera Blanca")
        btn_blanca.clicked.connect(lambda: self.set_remera(REMERA_BLANCA))

        btn_negra = QPushButton("Remera Negra")
        btn_negra.clicked.connect(lambda: self.set_remera(REMERA_NEGRA))

        btn_export = QPushButton("Exportar")
        btn_export.clicked.connect(self.exportar)

        panel_izq.addWidget(QLabel("Texto"))
        panel_izq.addWidget(self.input_texto)
        panel_izq.addWidget(QLabel("Tamaño"))
        panel_izq.addWidget(self.spin_size)
        panel_izq.addWidget(btn_blanca)
        panel_izq.addWidget(btn_negra)
        panel_izq.addWidget(btn_export)

        # -------- Lista de fuentes --------
        self.lista_fuentes = QListWidget()
        self.lista_fuentes.currentRowChanged.connect(self.seleccionar_fuente)

        # -------- Preview --------
        self.label_preview = QLabel()
        self.label_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Layout general
        layout.addLayout(panel_izq, 1)
        layout.addWidget(self.lista_fuentes, 2)
        layout.addWidget(self.label_preview, 3)

        self.setLayout(layout)

    def cargar_fuentes(self):
        self.fuentes = []

        for archivo in os.listdir(CARPETA_FUENTES):
            if archivo.endswith(".ttf"):
                path = os.path.join(CARPETA_FUENTES, archivo)

                font_id = QFontDatabase.addApplicationFont(path)

                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)

                    if families:
                        family = families[0]
                        self.fuentes.append((path, family))

                        item_text = "Elegir esta fuente"
                        self.lista_fuentes.addItem(item_text)

                        item = self.lista_fuentes.item(self.lista_fuentes.count() - 1)
                        font = QFont(family, 14)
                        item.setFont(font)

    def seleccionar_fuente(self, index):
        if index >= 0:
            self.ruta_fuente = self.fuentes[index][0]
            self.actualizar_preview()

    def set_remera(self, ruta):
        self.ruta_remera = ruta
        self.actualizar_preview()

    def actualizar_preview(self):
        if not self.ruta_fuente:
            return

        texto = self.input_texto.text()
        tamaño = self.spin_size.value()

        img = self.generar_imagen(texto, tamaño)
        qt_img = self.pil_a_qt(img)

        self.label_preview.setPixmap(qt_img.scaled(
            400, 400, Qt.AspectRatioMode.KeepAspectRatio))

    def generar_imagen(self, texto, tamaño):
        base = Image.open(self.ruta_remera).convert("RGBA")

        font = ImageFont.truetype(self.ruta_fuente, tamaño)

        draw = ImageDraw.Draw(base)
        bbox = draw.textbbox((0, 0), texto, font=font)

        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        W, H = base.size
        x = (W - w) // 2
        y = (H - h) // 2

        capa = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw_capa = ImageDraw.Draw(capa)

        color = (0, 0, 0, 255) if "blanca" in self.ruta_remera else (255, 255, 255, 255)

        draw_capa.text((x, y), texto, font=font, fill=color)

        capa = capa.filter(ImageFilter.GaussianBlur(1.2))

        alpha = capa.split()[3].point(lambda p: int(p * 0.7))
        capa.putalpha(alpha)

        return Image.alpha_composite(base, capa)

    def pil_a_qt(self, img):
        data = img.tobytes("raw", "RGBA")
        qimg = QImage(data, img.size[0], img.size[1], QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimg)

    def exportar(self):
        texto = self.input_texto.text()
        tamaño = self.spin_size.value()

        img = self.generar_imagen(texto, tamaño)
        path = os.path.join(CARPETA_RESULTADOS, "resultado.png")
        img.save(path)

        print("Guardado en:", path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = App()
    ventana.resize(1000, 500)
    ventana.show()
    sys.exit(app.exec())