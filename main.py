"""
Simulador de Estampado — v3
Mejoras sobre v2:
  - Color por palabra/token individual
  - Negrita e itálica por token
  - Espaciado entre líneas ajustable
  - Blur y opacidad ajustables (valores bajos = texto más nítido)
  - Editor de tokens con tabla visual
"""

import sys
import os
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QListWidget,
    QVBoxLayout, QHBoxLayout, QTextEdit, QSpinBox, QDoubleSpinBox,
    QFileDialog, QColorDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame, QCheckBox
)
from PyQt6.QtGui import QPixmap, QImage, QFontDatabase, QFont, QColor
from PyQt6.QtCore import Qt, QPoint

# ── Rutas ──────────────────────────────────────────────────────────────────────
CARPETA_FUENTES    = "fuentes"
CARPETA_RESULTADOS = "resultados"
REMERA_BLANCA      = "remera_blanca.png"
REMERA_NEGRA       = "remera_negra.png"
PREVIEW_SIZE       = 420


# ── Token ──────────────────────────────────────────────────────────────────────
class Token:
    def __init__(self, texto: str, color=None, negrita=False, italica=False):
        self.texto   = texto
        self.color   = color    # None => usar color global
        self.negrita  = negrita
        self.italica  = italica


def parsear_tokens(texto: str) -> list:
    tokens = []
    for linea in texto.split("\n"):
        partes = re.split(r"(\s+)", linea)
        for p in partes:
            if p:
                tokens.append(Token(p))
        tokens.append(Token("\n"))
    if tokens and tokens[-1].texto == "\n":
        tokens.pop()
    return tokens


# ── Preview con drag ───────────────────────────────────────────────────────────
class PreviewLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(PREVIEW_SIZE, PREVIEW_SIZE)
        self.setStyleSheet("border: 1px solid #444; background: #111;")
        self._drag   = False
        self._pos    = QPoint(PREVIEW_SIZE // 2, int(PREVIEW_SIZE * 0.45))
        self._offset = QPoint(0, 0)
        self.on_drag = None

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag   = True
            self._offset = e.pos() - self._pos
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        if self._drag:
            p = e.pos() - self._offset
            p.setX(max(0, min(PREVIEW_SIZE, p.x())))
            p.setY(max(0, min(PREVIEW_SIZE, p.y())))
            self._pos = p
            if self.on_drag:
                self.on_drag(p.x() / PREVIEW_SIZE, p.y() / PREVIEW_SIZE)

    def mouseReleaseEvent(self, e):
        self._drag = False
        self.setCursor(Qt.CursorShape.OpenHandCursor)


# ── Tabla de tokens ────────────────────────────────────────────────────────────
class TablaTokens(QTableWidget):
    COL_TEXTO   = 0
    COL_COLOR   = 1
    COL_NEGRITA = 2
    COL_ITALICA = 3

    def __init__(self, on_change):
        super().__init__(0, 4)
        self.on_change = on_change
        self._tokens_vis: list = []   # solo los visibles (sin espacios/saltos)
        self._bloq = False

        self.setHorizontalHeaderLabels(["Palabra", "Color", "B", "I"])
        h = self.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(1, 70)
        self.setColumnWidth(2, 28)
        self.setColumnWidth(3, 28)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setDefaultSectionSize(22)

    def cargar(self, tokens: list):
        self._bloq = True
        self._tokens_vis = [t for t in tokens if t.texto not in (" ", "\n")]
        self.setRowCount(0)

        for tok in self._tokens_vis:
            fila = self.rowCount()
            self.insertRow(fila)
            self.setItem(fila, self.COL_TEXTO, QTableWidgetItem(tok.texto))

            btn = QPushButton()
            btn.setFixedHeight(18)
            self._pintar_boton(btn, tok.color)
            btn.clicked.connect(lambda _, t=tok, b=btn: self._elegir_color(t, b))
            self.setCellWidget(fila, self.COL_COLOR, btn)

            chk_b = QCheckBox()
            chk_b.setChecked(tok.negrita)
            chk_b.stateChanged.connect(lambda s, t=tok: self._set_negrita(t, s))
            self.setCellWidget(fila, self.COL_NEGRITA, self._wrap(chk_b))

            chk_i = QCheckBox()
            chk_i.setChecked(tok.italica)
            chk_i.stateChanged.connect(lambda s, t=tok: self._set_italica(t, s))
            self.setCellWidget(fila, self.COL_ITALICA, self._wrap(chk_i))

        self._bloq = False

    def _wrap(self, w):
        c = QWidget(); l = QHBoxLayout(c)
        l.addWidget(w); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.setContentsMargins(0, 0, 0, 0)
        return c

    def _pintar_boton(self, btn, color):
        if color:
            r, g, b, _ = color
            h = f"#{r:02x}{g:02x}{b:02x}"
            lum = 0.299*r + 0.587*g + 0.114*b
            fg  = "black" if lum > 128 else "white"
            btn.setStyleSheet(f"background:{h}; color:{fg}; font-size:9px;")
            btn.setText(h)
        else:
            btn.setStyleSheet("font-size:9px; color:#aaa;")
            btn.setText("auto")

    def _elegir_color(self, tok: Token, btn: QPushButton):
        init = QColor(*tok.color[:3]) if tok.color else QColor(255, 255, 255)
        c = QColorDialog.getColor(init, self, f'Color para "{tok.texto}"')
        if c.isValid():
            tok.color = (c.red(), c.green(), c.blue(), 255)
            self._pintar_boton(btn, tok.color)
            self.on_change()

    def limpiar_seleccionados(self):
        filas = set(idx.row() for idx in self.selectedIndexes())
        for f in filas:
            if f < len(self._tokens_vis):
                self._tokens_vis[f].color = None
                btn = self.cellWidget(f, self.COL_COLOR)
                if isinstance(btn, QPushButton):
                    self._pintar_boton(btn, None)
        self.on_change()

    def _set_negrita(self, tok, state):
        if not self._bloq:
            tok.negrita = bool(state)
            self.on_change()

    def _set_italica(self, tok, state):
        if not self._bloq:
            tok.italica = bool(state)
            self.on_change()


# ── App principal ──────────────────────────────────────────────────────────────
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Estampado v3")
        self.setStyleSheet("""
            QWidget        { background:#1e1e1e; color:#e0e0e0; font-size:12px; }
            QPushButton    { background:#333; border:1px solid #555; padding:3px 7px; border-radius:3px; }
            QPushButton:hover    { background:#444; }
            QPushButton:checked  { background:#0078d4; color:white; }
            QSpinBox, QDoubleSpinBox { background:#2a2a2a; border:1px solid #555; padding:2px; color:#e0e0e0; }
            QTextEdit      { background:#2a2a2a; border:1px solid #555; color:#e0e0e0; }
            QListWidget    { background:#2a2a2a; border:1px solid #555; }
            QTableWidget   { background:#2a2a2a; border:1px solid #555; gridline-color:#3a3a3a; }
            QHeaderView::section { background:#2f2f2f; border:1px solid #555; padding:2px; }
            QCheckBox::indicator { width:14px; height:14px; }
        """)

        os.makedirs(CARPETA_RESULTADOS, exist_ok=True)

        self.tokens: list       = parsear_tokens("Texto de ejemplo")
        self.ruta_remera        = REMERA_NEGRA
        self.ruta_fuente        = None
        self.color_global       = None
        self.alineacion         = "center"
        self.pos_x_norm         = 0.5
        self.pos_y_norm         = 0.45
        self._sync_texto        = False

        self.init_ui()
        self.cargar_fuentes()

    # ── construcción UI ────────────────────────────────────────────────────────

    def _lbl(self, txt):
        l = QLabel(txt); l.setStyleSheet("color:#999; font-size:10px;")
        return l

    def _sep(self):
        s = QFrame(); s.setFrameShape(QFrame.Shape.HLine)
        s.setStyleSheet("color:#3a3a3a;"); return s

    def init_ui(self):
        root = QHBoxLayout(self); root.setSpacing(8)

        # ── Izquierda ──────────────────────────────────────────────────────────
        izq = QVBoxLayout(); izq.setSpacing(4)

        izq.addWidget(self._lbl("Texto (multi-línea)"))
        self.input_texto = QTextEdit()
        self.input_texto.setPlainText("Texto de ejemplo")
        self.input_texto.setFixedHeight(72)
        self.input_texto.textChanged.connect(self._texto_cambiado)
        izq.addWidget(self.input_texto)

        # Tamaño
        r1 = QHBoxLayout()
        r1.addWidget(self._lbl("Tamaño px"))
        self.spin_size = QSpinBox(); self.spin_size.setRange(8, 300); self.spin_size.setValue(50)
        self.spin_size.valueChanged.connect(self.actualizar_preview)
        r1.addWidget(self.spin_size); izq.addLayout(r1)

        # Interlineado
        r2 = QHBoxLayout()
        r2.addWidget(self._lbl("Interlineado"))
        self.spin_inter = QDoubleSpinBox(); self.spin_inter.setRange(0.5, 4.0)
        self.spin_inter.setSingleStep(0.1); self.spin_inter.setValue(1.25)
        self.spin_inter.valueChanged.connect(self.actualizar_preview)
        r2.addWidget(self.spin_inter); izq.addLayout(r2)

        # Blur
        r3 = QHBoxLayout()
        r3.addWidget(self._lbl("Blur"))
        self.spin_blur = QDoubleSpinBox(); self.spin_blur.setRange(0.0, 10.0)
        self.spin_blur.setSingleStep(0.1); self.spin_blur.setValue(0.6)
        self.spin_blur.valueChanged.connect(self.actualizar_preview)
        r3.addWidget(self.spin_blur); izq.addLayout(r3)

        # Opacidad
        r4 = QHBoxLayout()
        r4.addWidget(self._lbl("Opacidad"))
        self.spin_opa = QDoubleSpinBox(); self.spin_opa.setRange(0.05, 1.0)
        self.spin_opa.setSingleStep(0.05); self.spin_opa.setValue(0.92)
        self.spin_opa.valueChanged.connect(self.actualizar_preview)
        r4.addWidget(self.spin_opa); izq.addLayout(r4)

        # Alineación
        izq.addWidget(self._lbl("Alineación"))
        ar = QHBoxLayout(); self.btn_alin = {}
        for sym, key in [("←", "left"), ("≡", "center"), ("→", "right")]:
            b = QPushButton(sym); b.setCheckable(True); b.setFixedWidth(38)
            b.clicked.connect(lambda _, k=key: self.set_alineacion(k))
            ar.addWidget(b); self.btn_alin[key] = b
        self.btn_alin["center"].setChecked(True)
        izq.addLayout(ar)

        # Color global
        izq.addWidget(self._sep())
        self.btn_cg = QPushButton("Color global: auto")
        self.btn_cg.clicked.connect(self.elegir_color_global)
        izq.addWidget(self.btn_cg)
        b_rcg = QPushButton("Resetear color global")
        b_rcg.clicked.connect(self.resetear_color_global)
        izq.addWidget(b_rcg)

        # Remeras
        izq.addWidget(self._sep())
        b_bl = QPushButton("🤍  Remera Blanca")
        b_bl.clicked.connect(lambda: self.set_remera(REMERA_BLANCA))
        izq.addWidget(b_bl)
        b_ng = QPushButton("🖤  Remera Negra")
        b_ng.clicked.connect(lambda: self.set_remera(REMERA_NEGRA))
        izq.addWidget(b_ng)

        hint = QLabel("💡 Arrastrá el texto en la preview")
        hint.setStyleSheet("color:#555; font-size:10px;")
        izq.addWidget(hint)

        izq.addWidget(self._sep())
        b_exp = QPushButton("💾  Exportar imagen")
        b_exp.clicked.connect(self.exportar)
        izq.addWidget(b_exp)
        izq.addStretch()

        # ── Centro ─────────────────────────────────────────────────────────────
        centro = QVBoxLayout(); centro.setSpacing(4)

        centro.addWidget(self._lbl("Fuentes (.ttf / .otf)"))
        self.lista_fuentes = QListWidget()
        self.lista_fuentes.currentRowChanged.connect(self.seleccionar_fuente)
        centro.addWidget(self.lista_fuentes, 2)

        centro.addWidget(self._sep())
        centro.addWidget(self._lbl("Color / estilo por palabra"))
        self.tabla = TablaTokens(self.actualizar_preview)
        self.tabla.cargar(self.tokens)
        centro.addWidget(self.tabla, 3)

        b_lim = QPushButton("Limpiar color de filas seleccionadas")
        b_lim.clicked.connect(self.tabla.limpiar_seleccionados)
        centro.addWidget(b_lim)

        # ── Preview ────────────────────────────────────────────────────────────
        self.preview = PreviewLabel()
        self.preview.on_drag = self._on_drag
        self.preview.setCursor(Qt.CursorShape.OpenHandCursor)

        root.addLayout(izq, 2)
        root.addLayout(centro, 3)
        root.addWidget(self.preview, 3)

    # ── Fuentes ────────────────────────────────────────────────────────────────

    def cargar_fuentes(self):
        self.fuentes = []
        if not os.path.isdir(CARPETA_FUENTES):
            return
        for arch in sorted(os.listdir(CARPETA_FUENTES)):
            if arch.lower().endswith((".ttf", ".otf")):
                path = os.path.join(CARPETA_FUENTES, arch)
                fid  = QFontDatabase.addApplicationFont(path)
                if fid != -1:
                    fams = QFontDatabase.applicationFontFamilies(fid)
                    if fams:
                        self.fuentes.append((path, fams[0]))
                        self.lista_fuentes.addItem("Elegir esta fuente")
                        item = self.lista_fuentes.item(self.lista_fuentes.count() - 1)
                        item.setFont(QFont(fams[0], 13))

    def seleccionar_fuente(self, idx):
        if idx >= 0:
            self.ruta_fuente = self.fuentes[idx][0]
            self.actualizar_preview()

    # ── Controles ──────────────────────────────────────────────────────────────

    def set_remera(self, ruta):
        self.ruta_remera = ruta
        self.actualizar_preview()

    def set_alineacion(self, alin):
        self.alineacion = alin
        for k, b in self.btn_alin.items():
            b.setChecked(k == alin)
        self.actualizar_preview()

    def elegir_color_global(self):
        init = QColor(*self.color_global[:3]) if self.color_global else QColor(255, 255, 255)
        c = QColorDialog.getColor(init, self, "Color global del texto")
        if c.isValid():
            self.color_global = (c.red(), c.green(), c.blue(), 255)
            lum = 0.299*c.red() + 0.587*c.green() + 0.114*c.blue()
            fg  = "black" if lum > 128 else "white"
            self.btn_cg.setStyleSheet(f"background:{c.name()}; color:{fg};")
            self.btn_cg.setText(f"Color global: {c.name()}")
            self.actualizar_preview()

    def resetear_color_global(self):
        self.color_global = None
        self.btn_cg.setStyleSheet("")
        self.btn_cg.setText("Color global: auto")
        self.actualizar_preview()

    def _on_drag(self, nx, ny):
        self.pos_x_norm = nx
        self.pos_y_norm = ny
        self.actualizar_preview()

    def _texto_cambiado(self):
        if self._sync_texto:
            return
        self.tokens = parsear_tokens(self.input_texto.toPlainText())
        self.tabla.cargar(self.tokens)
        self.actualizar_preview()

    # ── Render ─────────────────────────────────────────────────────────────────

    def _color_default(self):
        if self.color_global:
            return self.color_global
        return (0, 0, 0, 255) if "blanca" in self.ruta_remera else (255, 255, 255, 255)

    def _font_para(self, tok: Token):
        base = self.ruta_fuente
        size = self.spin_size.value()
        stem = os.path.splitext(base)[0]
        if tok.negrita and tok.italica:
            cands = [stem+"-BoldItalic.ttf", stem+"-BoldOblique.ttf"]
        elif tok.negrita:
            cands = [stem+"-Bold.ttf"]
        elif tok.italica:
            cands = [stem+"-Italic.ttf", stem+"-Oblique.ttf"]
        else:
            cands = []
        for c in cands:
            if os.path.exists(c):
                try:
                    return ImageFont.truetype(c, size)
                except Exception:
                    pass
        return ImageFont.truetype(base, size)

    def generar_imagen(self):
        if not self.ruta_fuente:
            return None

        base_img = Image.open(self.ruta_remera).convert("RGBA")
        W, H     = base_img.size

        inter    = self.spin_inter.value()
        blur_v   = self.spin_blur.value()
        opa      = self.spin_opa.value()

        font_base = ImageFont.truetype(self.ruta_fuente, self.spin_size.value())
        tmp_draw  = ImageDraw.Draw(Image.new("RGBA", (1, 1)))

        # Altura de línea base
        bb0       = tmp_draw.textbbox((0, 0), "Ag", font=font_base)
        alto_base = bb0[3] - bb0[1]
        alto_lin  = int(alto_base * inter)

        # Dividir tokens en líneas
        lineas: list = [[]]
        for tok in self.tokens:
            if tok.texto == "\n":
                lineas.append([])
            else:
                lineas[-1].append(tok)

        # Medir ancho de cada línea
        def medir_linea(toks):
            w = 0
            for t in toks:
                f  = self._font_para(t)
                bb = tmp_draw.textbbox((0, 0), t.texto, font=f)
                w += bb[2] - bb[0]
            return w

        anchos    = [medir_linea(l) for l in lineas]
        ancho_max = max(anchos) if anchos else 0
        alto_tot  = alto_lin * len(lineas)

        cx = int(self.pos_x_norm * W)
        cy = int(self.pos_y_norm * H)

        capa = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(capa)

        for i, linea in enumerate(lineas):
            bw = anchos[i]
            if self.alineacion == "left":
                x = cx - ancho_max // 2
            elif self.alineacion == "right":
                x = cx + ancho_max // 2 - bw
            else:
                x = cx - bw // 2
            y = cy - alto_tot // 2 + i * alto_lin

            for tok in linea:
                f     = self._font_para(tok)
                color = tok.color if tok.color else self._color_default()
                draw.text((x, y), tok.texto, font=f, fill=color)
                bb = draw.textbbox((x, y), tok.texto, font=f)
                x += bb[2] - bb[0]

        if blur_v > 0:
            capa = capa.filter(ImageFilter.GaussianBlur(blur_v))
        alpha = capa.split()[3].point(lambda p: int(p * opa))
        capa.putalpha(alpha)

        return Image.alpha_composite(base_img, capa)

    def actualizar_preview(self):
        img = self.generar_imagen()
        if img is None:
            return
        data  = img.tobytes("raw", "RGBA")
        qimg  = QImage(data, img.size[0], img.size[1], QImage.Format.Format_RGBA8888)
        pix   = QPixmap.fromImage(qimg)
        self.preview.setPixmap(
            pix.scaled(PREVIEW_SIZE, PREVIEW_SIZE,
                       Qt.AspectRatioMode.KeepAspectRatio,
                       Qt.TransformationMode.SmoothTransformation)
        )

    # ── Exportar ───────────────────────────────────────────────────────────────

    def exportar(self):
        img = self.generar_imagen()
        if img is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar imagen",
            os.path.join(CARPETA_RESULTADOS, "resultado.png"),
            "PNG (*.png);;JPEG (*.jpg *.jpeg)"
        )
        if path:
            img.save(path)
            print("Guardado en:", path)


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    v = App()
    v.resize(1280, 620)
    v.show()
    sys.exit(app.exec())
