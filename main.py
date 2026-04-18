"""
Simulador de Estampado — v5
────────────────────────────
Cambios respecto a v4:
  • Render en hilo separado (QThread) con debounce de 150 ms → nunca traba la UI
  • Canvas con handles visuales tipo Figma:
      - Arrastrar objeto  → mover
      - Arrastrar esquina → escalar
      - Ctrl + arrastrar esquina → rotar
      - Shift al escalar → mantener proporción (siempre activo para imágenes)
  • Imagen importada se fittea automáticamente al 30 % del canvas
  • UI simplificada: una sola barra lateral con los controles esenciales
  • Subrayado, negrita, cursiva, color y tamaño por palabra en tabla compacta
"""

import sys, os, re, math, time
from copy import deepcopy

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QListWidget,
    QVBoxLayout, QHBoxLayout, QTextEdit, QSpinBox, QDoubleSpinBox,
    QFileDialog, QColorDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame, QCheckBox,
    QGroupBox, QSizePolicy, QStackedWidget, QScrollArea
)
from PyQt6.QtGui  import (
    QPixmap, QImage, QFontDatabase, QFont, QColor,
    QPainter, QPen, QBrush, QPolygonF, QCursor
)
from PyQt6.QtCore import (
    Qt, QPoint, QPointF, QRectF, QSize, QThread, pyqtSignal, QTimer
)

# ═══════════════════════════════════════════════════════════════════════════════
CARPETA_FUENTES    = "fuentes"
CARPETA_RESULTADOS = "resultados"
REMERA_BLANCA      = "remera_blanca.png"
REMERA_NEGRA       = "remera_negra.png"

CANVAS_W = 480
CANVAS_H = 500

HANDLE_R  = 6     # radio de los handles en px (coordenadas canvas)
DARK = """
QWidget{background:#1e1e1e;color:#ddd;font-size:12px}
QPushButton{background:#2d2d2d;border:1px solid #555;padding:3px 8px;border-radius:3px}
QPushButton:hover{background:#3a3a3a} QPushButton:checked{background:#0078d4;color:#fff}
QSpinBox,QDoubleSpinBox{background:#252525;border:1px solid #555;padding:2px;color:#ddd}
QTextEdit,QListWidget,QTableWidget{background:#252525;border:1px solid #555;color:#ddd}
QHeaderView::section{background:#2d2d2d;border:1px solid #555;padding:2px}
QGroupBox{border:1px solid #444;border-radius:4px;margin-top:8px;padding-top:6px}
QGroupBox::title{subcontrol-origin:margin;left:8px;color:#888}
QScrollBar:vertical{width:8px;background:#1e1e1e}
QScrollBar::handle:vertical{background:#444;border-radius:4px}
QCheckBox::indicator{width:13px;height:13px}
"""

# ═══════════════════════════════════════════════════════════════════════════════
#  MODELOS
# ═══════════════════════════════════════════════════════════════════════════════

class TokenEstilo:
    def __init__(self):
        self.color = self.tamano = self.negrita = self.cursiva = self.subrayado = None


class CapaTexto:
    tipo = "texto"; _id = 0
    def __init__(self):
        CapaTexto._id += 1
        self.id = CapaTexto._id
        self.nombre   = f"Texto {self.id}"
        self.visible  = True
        self.texto    = "Texto"
        # posición normalizada centro [0..1]
        self.nx, self.ny = 0.5, 0.45
        # transformaciones
        self.tamano   = 60
        self.escala   = 1.0    # escala uniforme aplicada por handles
        self.rotacion = 0.0    # grados
        # estilo
        self.color    = None
        self.negrita  = False
        self.cursiva  = False
        self.subrayado= False
        self.interlineado = 1.3
        self.alineacion   = "center"
        self.estilos_token: dict = {}

    def estilo_de(self, tok):
        if tok not in self.estilos_token:
            self.estilos_token[tok] = TokenEstilo()
        return self.estilos_token[tok]


class CapaImagen:
    tipo = "imagen"; _id = 0
    def __init__(self, ruta, nx=0.5, ny=0.45, escala=1.0):
        CapaImagen._id += 1
        self.id      = CapaImagen._id
        self.nombre  = os.path.basename(ruta)
        self.visible = True
        self.ruta    = ruta
        self.nx, self.ny = nx, ny
        self.escala   = escala
        self.rotacion = 0.0
        self._pil     = None

    def imagen_pil(self):
        if self._pil is None:
            self._pil = Image.open(self.ruta).convert("RGBA")
        return self._pil


# ═══════════════════════════════════════════════════════════════════════════════
#  RENDER (funciones puras, se llaman desde el thread)
# ═══════════════════════════════════════════════════════════════════════════════

def _font(ruta, tam, neg, cur):
    stem = os.path.splitext(ruta)[0]
    cands = []
    if neg and cur: cands += [stem+"-BoldItalic.ttf", stem+"-BoldOblique.ttf"]
    elif neg:       cands += [stem+"-Bold.ttf"]
    elif cur:       cands += [stem+"-Italic.ttf", stem+"-Oblique.ttf"]
    cands.append(ruta)
    for c in cands:
        if os.path.exists(c):
            try: return ImageFont.truetype(c, tam)
            except: pass
    return ImageFont.truetype(ruta, tam)


def render_texto(capa: CapaTexto, W, H, ruta_fuente, color_auto, blur, opa):
    lineas = (capa.texto or "").split("\n")
    tmp_d  = ImageDraw.Draw(Image.new("RGBA",(1,1)))
    fb     = _font(ruta_fuente, max(6, int(capa.tamano * capa.escala)), capa.negrita, capa.cursiva)
    bb0    = tmp_d.textbbox((0,0),"Ag",font=fb)
    alto_l = int((bb0[3]-bb0[1]) * capa.interlineado)

    def tok_info(p):
        e   = capa.estilos_token.get(p, TokenEstilo())
        neg = e.negrita  if e.negrita  is not None else capa.negrita
        cur = e.cursiva  if e.cursiva  is not None else capa.cursiva
        tam = max(6, int((e.tamano or capa.tamano) * capa.escala))
        col = e.color or capa.color or color_auto
        sub = e.subrayado if e.subrayado is not None else capa.subrayado
        f   = _font(ruta_fuente, tam, neg, cur)
        return f, col, sub

    rows = []
    for linea in lineas:
        partes = re.split(r"(\s+)", linea)
        fila   = []
        for p in partes:
            if not p: continue
            if p.strip() == "":
                bb = tmp_d.textbbox((0,0),p,font=fb)
                fila.append((p, fb, color_auto, False, bb[2]-bb[0]))
            else:
                f, col, sub = tok_info(p)
                bb = tmp_d.textbbox((0,0),p,font=f)
                fila.append((p, f, col, sub, bb[2]-bb[0]))
        rows.append(fila)

    anchos    = [sum(t[4] for t in r) for r in rows]
    ancho_max = max(anchos) if anchos else 0
    alto_tot  = alto_l * len(rows)

    pad = max(W, H) * 2
    ci  = Image.new("RGBA",(ancho_max+pad, alto_tot+pad),(0,0,0,0))
    d   = ImageDraw.Draw(ci)
    ox, oy = pad//2, pad//2

    for i, fila in enumerate(rows):
        bw = anchos[i]
        if   capa.alineacion == "left":  x = ox
        elif capa.alineacion == "right": x = ox + ancho_max - bw
        else:                            x = ox + (ancho_max - bw)//2
        y = oy + i * alto_l
        for (tok, f, col, sub, tw) in fila:
            d.text((x,y), tok, font=f, fill=col)
            if sub:
                bb  = d.textbbox((x,y),tok,font=f)
                uy  = bb[3]+1
                d.line([(x,uy),(x+tw,uy)], fill=col, width=max(1,capa.tamano//20))
            x += tw

    if capa.rotacion:
        ci = ci.rotate(-capa.rotacion, expand=True, resample=Image.BICUBIC)
    if blur > 0:
        ci = ci.filter(ImageFilter.GaussianBlur(blur))
    if opa < 1.0:
        a = ci.split()[3].point(lambda p: int(p*opa)); ci.putalpha(a)

    cx = int(capa.nx*W) - ci.width//2
    cy = int(capa.ny*H) - ci.height//2
    out = Image.new("RGBA",(W,H),(0,0,0,0))
    out.paste(ci,(cx,cy),ci)
    return out


def render_imagen(capa: CapaImagen, W, H, blur, opa):
    src = capa.imagen_pil().copy()
    nw  = max(1, int(src.width  * capa.escala))
    nh  = max(1, int(src.height * capa.escala))
    src = src.resize((nw,nh), Image.LANCZOS)
    if capa.rotacion:
        src = src.rotate(-capa.rotacion, expand=True, resample=Image.BICUBIC)
    if blur > 0:
        src = src.filter(ImageFilter.GaussianBlur(blur))
    if opa < 1.0:
        a = src.split()[3].point(lambda p: int(p*opa)); src.putalpha(a)
    cx = int(capa.nx*W) - src.width//2
    cy = int(capa.ny*H) - src.height//2
    out = Image.new("RGBA",(W,H),(0,0,0,0))
    out.paste(src,(cx,cy),src)
    return out


def renderizar_todo(remera_path, capas, ruta_fuente, blur, opa):
    base = Image.open(remera_path).convert("RGBA")
    W, H = base.size
    color_auto = (0,0,0,255) if "blanca" in remera_path else (255,255,255,255)
    res  = base.copy()
    for c in capas:
        if not c.visible: continue
        if c.tipo == "texto":
            ov = render_texto(c, W, H, ruta_fuente, color_auto, blur, opa)
        else:
            ov = render_imagen(c, W, H, blur, opa)
        res = Image.alpha_composite(res, ov)
    return res


# ═══════════════════════════════════════════════════════════════════════════════
#  THREAD DE RENDER
# ═══════════════════════════════════════════════════════════════════════════════

class RenderThread(QThread):
    done = pyqtSignal(object)   # emite PIL Image

    def __init__(self):
        super().__init__()
        self._args = None

    def solicitar(self, args: tuple):
        self._args = args
        if not self.isRunning():
            self.start()

    def run(self):
        while True:
            args = self._args
            if args is None: break
            self._args = None          # consumir
            try:
                img = renderizar_todo(*args)
                if self._args is None: # no llegó nueva solicitud
                    self.done.emit(img)
                    break
            except Exception as e:
                print("Render error:", e)
                break


# ═══════════════════════════════════════════════════════════════════════════════
#  CANVAS CON HANDLES
# ═══════════════════════════════════════════════════════════════════════════════

class Handle:
    """Posición normalizada de un handle + tipo."""
    MOVE   = "move"
    SCALE  = "scale"
    ROTATE = "rotate"   # Ctrl + esquina

    def __init__(self, nx, ny, kind=SCALE):
        self.nx, self.ny = nx, ny
        self.kind = kind


def _bbox_capa(capa, W, H, ruta_fuente):
    """Devuelve (cx, cy, w, h) en píxeles canvas de la capa, aproximado."""
    if capa.tipo == "imagen":
        src = capa.imagen_pil()
        rad = math.radians(capa.rotacion)
        nw  = int(src.width  * capa.escala)
        nh  = int(src.height * capa.escala)
        # bounding box rotado
        cos, sin_ = abs(math.cos(rad)), abs(math.sin(rad))
        bw = int(nw*cos + nh*sin_)
        bh = int(nw*sin_ + nh*cos)
    else:
        tam = max(6, int(capa.tamano * capa.escala))
        try:
            fb  = _font(ruta_fuente, tam, capa.negrita, capa.cursiva)
            tmp = ImageDraw.Draw(Image.new("RGBA",(1,1)))
            lineas = (capa.texto or "").split("\n")
            bb0 = tmp.textbbox((0,0),"Ag",font=fb)
            alto_l = int((bb0[3]-bb0[1]) * capa.interlineado)
            anchos = []
            for l in lineas:
                partes = re.split(r"\s+", l)
                w = sum(tmp.textbbox((0,0),p or " ",font=fb)[2]-
                        tmp.textbbox((0,0),p or " ",font=fb)[0] for p in partes)
                anchos.append(w)
            nw_raw = max(anchos) if anchos else tam*4
            nh_raw = alto_l * len(lineas)
        except:
            nw_raw, nh_raw = tam*4, tam
        rad = math.radians(capa.rotacion)
        cos, sin_ = abs(math.cos(rad)), abs(math.sin(rad))
        bw = int(nw_raw*cos + nh_raw*sin_) + 20
        bh = int(nw_raw*sin_ + nh_raw*cos) + 10

    cx = int(capa.nx * W)
    cy = int(capa.ny * H)
    return cx, cy, max(bw, 20), max(bh, 20)


class CanvasWidget(QWidget):
    changed = pyqtSignal()   # pide re-render

    def __init__(self, w, h):
        super().__init__()
        self.setFixedSize(w, h)
        self.W, self.H = w, h
        self._pix          = None
        self._capas        = []
        self._capa_activa  = None
        self._ruta_fuente  = None

        # estado drag
        self._drag_tipo    = None   # "move" | "scale" | "rotate"
        self._drag_start   = QPointF()
        self._drag_cx0     = 0.0
        self._drag_cy0     = 0.0
        self._drag_escala0 = 1.0
        self._drag_rot0    = 0.0
        self._drag_bw0     = 1
        self._drag_bh0     = 1

        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def set_state(self, capas, capa_activa, ruta_fuente):
        self._capas       = capas
        self._capa_activa = capa_activa
        self._ruta_fuente = ruta_fuente

    def set_pixmap(self, pix: QPixmap):
        self._pix = pix
        self.update()

    # ── handles ────────────────────────────────────────────────────────────────
    def _handles(self):
        """Devuelve lista de (QPointF, tipo) para la capa activa."""
        if not self._capa_activa or not self._ruta_fuente:
            return []
        cx, cy, bw, bh = _bbox_capa(self._capa_activa, self.W, self.H, self._ruta_fuente)
        hw, hh = bw//2, bh//2
        corners = [
            QPointF(cx-hw, cy-hh), QPointF(cx+hw, cy-hh),
            QPointF(cx+hw, cy+hh), QPointF(cx-hw, cy+hh),
        ]
        edges = [
            QPointF(cx,    cy-hh), QPointF(cx+hw, cy),
            QPointF(cx,    cy+hh), QPointF(cx-hw, cy),
        ]
        return [(p, "scale") for p in corners] + [(p, "edge") for p in edges]

    def _hit_handle(self, pos: QPointF):
        for (hp, kind) in self._handles():
            if (pos - hp).manhattanLength() < HANDLE_R * 2 + 4:
                return hp, kind
        return None, None

    # ── paint ──────────────────────────────────────────────────────────────────
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # fondo
        p.fillRect(self.rect(), QColor("#111"))

        # imagen renderizada
        if self._pix:
            # centrar si la pix es más pequeña
            px = (self.W - self._pix.width())  // 2
            py = (self.H - self._pix.height()) // 2
            p.drawPixmap(px, py, self._pix)

        # handles de la capa activa
        if self._capa_activa:
            cx, cy, bw, bh = _bbox_capa(
                self._capa_activa, self.W, self.H, self._ruta_fuente or ""
            )
            hw, hh = bw//2, bh//2

            # bounding box
            pen = QPen(QColor("#0078d4"), 1, Qt.PenStyle.DashLine)
            p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(cx-hw, cy-hh, bw, bh)

            # handles
            for (hp, kind) in self._handles():
                if kind == "scale":
                    p.setPen(QPen(QColor("#0078d4"), 1))
                    p.setBrush(QBrush(QColor("#fff")))
                    p.drawEllipse(hp, HANDLE_R, HANDLE_R)
                else:
                    p.setPen(QPen(QColor("#0078d4"), 1))
                    p.setBrush(QBrush(QColor("#0078d4")))
                    p.drawRect(int(hp.x()-3), int(hp.y()-3), 6, 6)

    # ── mouse ──────────────────────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton: return
        pos = e.position()
        hp, kind = self._hit_handle(pos)

        if hp is not None:
            ctrl = bool(e.modifiers() & Qt.KeyboardModifier.ControlModifier)
            if ctrl and kind == "scale":
                self._drag_tipo  = "rotate"
                self._drag_rot0  = self._capa_activa.rotacion
            else:
                self._drag_tipo  = "scale"
                _, _, bw, bh = _bbox_capa(self._capa_activa, self.W, self.H,
                                           self._ruta_fuente or "")
                self._drag_bw0   = max(bw, 1)
                self._drag_bh0   = max(bh, 1)
                self._drag_escala0 = self._capa_activa.escala
            self._drag_start = pos
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif self._capa_activa:
            # ¿click sobre el objeto?
            cx, cy, bw, bh = _bbox_capa(self._capa_activa, self.W, self.H,
                                          self._ruta_fuente or "")
            r = QRectF(cx-bw//2, cy-bh//2, bw, bh)
            if r.contains(pos):
                self._drag_tipo  = "move"
                self._drag_start = pos
                self._drag_cx0   = self._capa_activa.nx
                self._drag_cy0   = self._capa_activa.ny
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            else:
                self._drag_tipo = None
        else:
            self._drag_tipo = None

    def mouseMoveEvent(self, e):
        pos = e.position()

        # cursor hint
        hp, kind = self._hit_handle(pos)
        if hp is not None:
            ctrl = bool(e.modifiers() & Qt.KeyboardModifier.ControlModifier)
            self.setCursor(Qt.CursorShape.CrossCursor if ctrl
                           else Qt.CursorShape.SizeFDiagCursor)
        elif self._drag_tipo is None:
            self.setCursor(Qt.CursorShape.OpenHandCursor)

        if not self._drag_tipo or not self._capa_activa: return

        dx = pos.x() - self._drag_start.x()
        dy = pos.y() - self._drag_start.y()

        if self._drag_tipo == "move":
            self._capa_activa.nx = max(0.0, min(1.0, self._drag_cx0 + dx/self.W))
            self._capa_activa.ny = max(0.0, min(1.0, self._drag_cy0 + dy/self.H))

        elif self._drag_tipo == "scale":
            dist_orig = math.hypot(self._drag_bw0/2, self._drag_bh0/2)
            cx = self._capa_activa.nx * self.W
            cy = self._capa_activa.ny * self.H
            dist_now = math.hypot(pos.x()-cx, pos.y()-cy)
            if dist_orig > 0:
                factor = dist_now / dist_orig
                self._capa_activa.escala = max(0.05, self._drag_escala0 * factor)

        elif self._drag_tipo == "rotate":
            cx = self._capa_activa.nx * self.W
            cy = self._capa_activa.ny * self.H
            ang_start = math.degrees(math.atan2(
                self._drag_start.y()-cy, self._drag_start.x()-cx))
            ang_now   = math.degrees(math.atan2(pos.y()-cy, pos.x()-cx))
            self._capa_activa.rotacion = (self._drag_rot0 + ang_now - ang_start) % 360

        self.update()
        self.changed.emit()

    def mouseReleaseEvent(self, e):
        self._drag_tipo = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)


# ═══════════════════════════════════════════════════════════════════════════════
#  PANEL PROPIEDADES — TEXTO
# ═══════════════════════════════════════════════════════════════════════════════

class PanelTexto(QWidget):
    def __init__(self, on_change):
        super().__init__()
        self._on_change = on_change
        self._capa: CapaTexto = None
        self._bloq = False
        self._build()

    def _lbl(self, t):
        l = QLabel(t); l.setStyleSheet("color:#888;font-size:10px;"); return l

    def _wrap(self, w):
        c = QWidget(); l = QHBoxLayout(c); l.addWidget(w)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter); l.setContentsMargins(0,0,0,0)
        return c

    def _build(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget(); v = QVBoxLayout(inner); v.setSpacing(5)
        v.setContentsMargins(4,4,4,4)

        # Texto
        v.addWidget(self._lbl("Texto"))
        self.txt = QTextEdit(); self.txt.setFixedHeight(60)
        self.txt.textChanged.connect(self._texto_cambio)
        v.addWidget(self.txt)

        # Tamaño + rotación
        r1 = QHBoxLayout()
        r1.addWidget(self._lbl("Tamaño"))
        self.sp_tam = QSpinBox(); self.sp_tam.setRange(6,400); self.sp_tam.setValue(60)
        self.sp_tam.valueChanged.connect(self._gc)
        r1.addWidget(self.sp_tam)
        v.addLayout(r1)

        r_rot = QHBoxLayout()
        r_rot.addWidget(self._lbl("Rotación °"))
        self.sp_rot = QSpinBox(); self.sp_rot.setRange(-360,360); self.sp_rot.setValue(0)
        self.sp_rot.valueChanged.connect(self._gc)
        r_rot.addWidget(self.sp_rot)
        v.addWidget(self._lbl("(o Ctrl+arrastrar esquina en canvas)"))
        v.addLayout(r_rot)

        # Color global
        rc = QHBoxLayout()
        self.btn_col = QPushButton("Color: auto")
        self.btn_col.clicked.connect(self._elegir_col)
        rc.addWidget(self.btn_col)
        btn_x = QPushButton("×"); btn_x.setFixedWidth(22)
        btn_x.clicked.connect(self._reset_col)
        rc.addWidget(btn_x)
        v.addLayout(rc)

        # Negrita / cursiva / subrayado
        re_ = QHBoxLayout()
        self.chk_neg = QCheckBox("B"); self.chk_neg.setStyleSheet("font-weight:bold")
        self.chk_cur = QCheckBox("I"); self.chk_cur.setStyleSheet("font-style:italic")
        self.chk_sub = QCheckBox("U"); self.chk_sub.setStyleSheet("text-decoration:underline")
        for c in (self.chk_neg, self.chk_cur, self.chk_sub):
            c.stateChanged.connect(self._gc); re_.addWidget(c)
        v.addLayout(re_)

        # Alineación
        ra = QHBoxLayout()
        self.btn_alin = {}
        for sym, key in [("←","left"),("≡","center"),("→","right")]:
            b = QPushButton(sym); b.setCheckable(True); b.setFixedWidth(34)
            b.clicked.connect(lambda _, k=key: self._alin(k))
            ra.addWidget(b); self.btn_alin[key] = b
        self.btn_alin["center"].setChecked(True)
        v.addLayout(ra)

        # Interlineado
        ri = QHBoxLayout(); ri.addWidget(self._lbl("Interlineado"))
        self.sp_int = QDoubleSpinBox(); self.sp_int.setRange(0.5,5)
        self.sp_int.setSingleStep(0.05); self.sp_int.setValue(1.3)
        self.sp_int.valueChanged.connect(self._gc)
        ri.addWidget(self.sp_int); v.addLayout(ri)

        # Tabla por-token
        v.addWidget(self._lbl("Por palabra: color / tamaño / B / I"))
        self.tabla = QTableWidget(0,5)
        self.tabla.setHorizontalHeaderLabels(["Palabra","Color","Tam","B","I"])
        h = self.tabla.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col,w in [(1,60),(2,44),(3,26),(4,26)]:
            h.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self.tabla.setColumnWidth(col,w)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setDefaultSectionSize(22)
        self.tabla.setFixedHeight(160)
        v.addWidget(self.tabla)

        b_lim = QPushButton("Limpiar estilo de seleccionados")
        b_lim.clicked.connect(self._limpiar)
        v.addWidget(b_lim)
        v.addStretch()

        scroll.setWidget(inner)
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0)
        root.addWidget(scroll)

    def cargar(self, capa: CapaTexto):
        self._capa = capa; self._bloq = True
        self.txt.setPlainText(capa.texto)
        self.sp_tam.setValue(capa.tamano)
        self.sp_rot.setValue(int(capa.rotacion))
        self.sp_int.setValue(capa.interlineado)
        self.chk_neg.setChecked(capa.negrita)
        self.chk_cur.setChecked(capa.cursiva)
        self.chk_sub.setChecked(capa.subrayado)
        for k,b in self.btn_alin.items(): b.setChecked(k==capa.alineacion)
        self._pintar_btn_col(capa.color)
        self._reload_tabla()
        self._bloq = False

    def _reload_tabla(self):
        if not self._capa: return
        self._bloq = True
        self.tabla.setRowCount(0)
        palabras = sorted(set(
            p for l in self._capa.texto.split("\n")
            for p in re.split(r"\s+",l) if p
        ))
        for palabra in palabras:
            est = self._capa.estilo_de(palabra)
            f = self.tabla.rowCount(); self.tabla.insertRow(f)
            self.tabla.setItem(f,0,QTableWidgetItem(palabra))

            btn = QPushButton(); btn.setFixedHeight(18)
            self._pintar_btn(btn, est.color)
            btn.clicked.connect(lambda _, p=palabra, b=btn: self._tok_col(p,b))
            self.tabla.setCellWidget(f,1,btn)

            sp = QSpinBox(); sp.setRange(0,400); sp.setSpecialValueText("auto")
            sp.setValue(est.tamano or 0)
            sp.valueChanged.connect(lambda v,p=palabra: self._tok_tam(p,v))
            self.tabla.setCellWidget(f,2,sp)

            cb = QCheckBox(); cb.setTristate(True); cb.setCheckState(self._tri(est.negrita))
            cb.stateChanged.connect(lambda s,p=palabra: self._tok_neg(p,s))
            self.tabla.setCellWidget(f,3,self._wrap(cb))

            ci = QCheckBox(); ci.setTristate(True); ci.setCheckState(self._tri(est.cursiva))
            ci.stateChanged.connect(lambda s,p=palabra: self._tok_cur(p,s))
            self.tabla.setCellWidget(f,4,self._wrap(ci))
        self._bloq = False

    def _tri(self, v):
        if v is None: return Qt.CheckState.PartiallyChecked
        return Qt.CheckState.Checked if v else Qt.CheckState.Unchecked
    def _tri_v(self, s):
        if s == Qt.CheckState.PartiallyChecked: return None
        return s == Qt.CheckState.Checked

    def _pintar_btn_col(self, color):
        if color:
            r,g,b,_ = color; h=f"#{r:02x}{g:02x}{b:02x}"
            lum = 0.299*r+0.587*g+0.114*b
            self.btn_col.setStyleSheet(f"background:{h};color:{'black' if lum>128 else 'white'};")
            self.btn_col.setText(f"Color: {h}")
        else:
            self.btn_col.setStyleSheet(""); self.btn_col.setText("Color: auto")

    def _pintar_btn(self, btn, color):
        if color:
            r,g,b,_ = color; h=f"#{r:02x}{g:02x}{b:02x}"
            lum = 0.299*r+0.587*g+0.114*b
            btn.setStyleSheet(f"background:{h};color:{'black' if lum>128 else 'white'};font-size:9px;")
            btn.setText(h)
        else:
            btn.setStyleSheet("font-size:9px;color:#888;"); btn.setText("auto")

    def _gc(self):
        if self._bloq or not self._capa: return
        self._capa.tamano      = self.sp_tam.value()
        self._capa.rotacion    = float(self.sp_rot.value())
        self._capa.negrita     = self.chk_neg.isChecked()
        self._capa.cursiva     = self.chk_cur.isChecked()
        self._capa.subrayado   = self.chk_sub.isChecked()
        self._capa.interlineado= self.sp_int.value()
        self._on_change()

    def _texto_cambio(self):
        if self._bloq or not self._capa: return
        self._capa.texto = self.txt.toPlainText()
        self._reload_tabla(); self._on_change()

    def _alin(self, a):
        if not self._capa: return
        self._capa.alineacion = a
        for k,b in self.btn_alin.items(): b.setChecked(k==a)
        self._on_change()

    def _elegir_col(self):
        if not self._capa: return
        init = QColor(*self._capa.color[:3]) if self._capa.color else QColor(255,255,255)
        c = QColorDialog.getColor(init, self)
        if c.isValid():
            self._capa.color = (c.red(),c.green(),c.blue(),255)
            self._pintar_btn_col(self._capa.color); self._on_change()

    def _reset_col(self):
        if not self._capa: return
        self._capa.color = None; self._pintar_btn_col(None); self._on_change()

    def _tok_col(self, p, btn):
        if not self._capa: return
        est = self._capa.estilo_de(p)
        init = QColor(*est.color[:3]) if est.color else QColor(255,255,255)
        c = QColorDialog.getColor(init, self, f'Color para "{p}"')
        if c.isValid():
            est.color = (c.red(),c.green(),c.blue(),255)
            self._pintar_btn(btn, est.color); self._on_change()

    def _tok_tam(self, p, v):
        if self._bloq or not self._capa: return
        self._capa.estilo_de(p).tamano = v if v>0 else None; self._on_change()

    def _tok_neg(self, p, s):
        if self._bloq or not self._capa: return
        self._capa.estilo_de(p).negrita = self._tri_v(s); self._on_change()

    def _tok_cur(self, p, s):
        if self._bloq or not self._capa: return
        self._capa.estilo_de(p).cursiva = self._tri_v(s); self._on_change()

    def _limpiar(self):
        if not self._capa: return
        filas = sorted(set(i.row() for i in self.tabla.selectedIndexes()))
        palabras = sorted(set(
            p for l in self._capa.texto.split("\n")
            for p in re.split(r"\s+",l) if p
        ))
        for f in filas:
            if f < len(palabras):
                self._capa.estilos_token.pop(palabras[f], None)
        self._reload_tabla(); self._on_change()


# ═══════════════════════════════════════════════════════════════════════════════
#  PANEL PROPIEDADES — IMAGEN
# ═══════════════════════════════════════════════════════════════════════════════

class PanelImagen(QWidget):
    def __init__(self, on_change):
        super().__init__()
        self._on_change = on_change
        self._capa: CapaImagen = None
        self._bloq = False
        self._build()

    def _build(self):
        v = QVBoxLayout(self); v.setSpacing(6); v.setContentsMargins(4,4,4,4)
        self.lbl = QLabel("—"); self.lbl.setStyleSheet("color:#aaa;font-size:11px;")
        v.addWidget(self.lbl)

        h1 = QHBoxLayout(); h1.addWidget(QLabel("Escala"))
        self.sp_esc = QDoubleSpinBox(); self.sp_esc.setRange(0.02,20)
        self.sp_esc.setSingleStep(0.05); self.sp_esc.setValue(1.0)
        self.sp_esc.valueChanged.connect(self._cambio)
        h1.addWidget(self.sp_esc); v.addLayout(h1)

        h2 = QHBoxLayout(); h2.addWidget(QLabel("Rotación °"))
        self.sp_rot = QSpinBox(); self.sp_rot.setRange(-360,360); self.sp_rot.setValue(0)
        self.sp_rot.valueChanged.connect(self._cambio)
        h2.addWidget(self.sp_rot); v.addLayout(h2)

        hint = QLabel("💡 Arrastrá para mover\nCtrl+arrastrar esquina → rotar\nArrastrar esquina → escalar")
        hint.setStyleSheet("color:#555;font-size:10px;")
        v.addWidget(hint)
        v.addStretch()

    def cargar(self, capa: CapaImagen):
        self._capa = capa; self._bloq = True
        self.lbl.setText(capa.nombre)
        self.sp_esc.setValue(capa.escala)
        self.sp_rot.setValue(int(capa.rotacion))
        self._bloq = False

    def _cambio(self):
        if self._bloq or not self._capa: return
        self._capa.escala   = self.sp_esc.value()
        self._capa.rotacion = float(self.sp_rot.value())
        self._on_change()


# ═══════════════════════════════════════════════════════════════════════════════
#  APP
# ═══════════════════════════════════════════════════════════════════════════════

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Estampado v5")
        self.setStyleSheet(DARK)
        os.makedirs(CARPETA_RESULTADOS, exist_ok=True)

        self.ruta_remera = REMERA_NEGRA
        self.ruta_fuente = None
        self.capas: list = []
        self.capa_activa = None

        # debounce timer
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(150)    # ms de espera antes de renderizar
        self._timer.timeout.connect(self._lanzar_render)

        # thread de render
        self._render_thread = RenderThread()
        self._render_thread.done.connect(self._render_done)

        self._init_ui()
        self._cargar_fuentes()
        self._nueva_capa_texto()

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _sep(self):
        s = QFrame(); s.setFrameShape(QFrame.Shape.HLine)
        s.setStyleSheet("color:#333;"); return s

    def _init_ui(self):
        root = QHBoxLayout(self); root.setSpacing(6)

        # ── Izquierda: capas + fuentes + render global ─────────────────────────
        izq = QVBoxLayout(); izq.setSpacing(4)

        gb_c = QGroupBox("Capas"); vc = QVBoxLayout(gb_c); vc.setSpacing(3)
        self.lista_capas = QListWidget(); self.lista_capas.setFixedHeight(95)
        self.lista_capas.currentRowChanged.connect(self._sel_capa)
        vc.addWidget(self.lista_capas)
        rc = QHBoxLayout()
        for label, slot in [("＋T", self._nueva_capa_texto),
                             ("＋🖼", self._nueva_capa_img),
                             ("🗑",  self._del_capa),
                             ("↑",   self._up_capa),
                             ("↓",   self._dn_capa)]:
            b = QPushButton(label); b.clicked.connect(slot); rc.addWidget(b)
        vc.addLayout(rc); izq.addWidget(gb_c)

        gb_f = QGroupBox("Fuente"); vf = QVBoxLayout(gb_f); vf.setSpacing(3)
        self.lista_fuentes = QListWidget(); self.lista_fuentes.setFixedHeight(95)
        self.lista_fuentes.currentRowChanged.connect(self._sel_fuente)
        vf.addWidget(self.lista_fuentes); izq.addWidget(gb_f)

        gb_r = QGroupBox("Render"); vr = QVBoxLayout(gb_r); vr.setSpacing(3)
        rb = QHBoxLayout(); rb.addWidget(QLabel("Blur"))
        self.sp_blur = QDoubleSpinBox(); self.sp_blur.setRange(0,8)
        self.sp_blur.setSingleStep(0.1); self.sp_blur.setValue(0.4)
        self.sp_blur.valueChanged.connect(self.solicitar_render)
        rb.addWidget(self.sp_blur); vr.addLayout(rb)
        ro = QHBoxLayout(); ro.addWidget(QLabel("Opacidad"))
        self.sp_opa = QDoubleSpinBox(); self.sp_opa.setRange(0.05,1.0)
        self.sp_opa.setSingleStep(0.05); self.sp_opa.setValue(0.93)
        self.sp_opa.valueChanged.connect(self.solicitar_render)
        ro.addWidget(self.sp_opa); vr.addLayout(ro)
        izq.addWidget(gb_r)

        gb_rm = QGroupBox("Remera"); vrm = QVBoxLayout(gb_rm); vrm.setSpacing(3)
        b_bl = QPushButton("🤍 Blanca"); b_bl.clicked.connect(lambda: self._set_remera(REMERA_BLANCA))
        b_ng = QPushButton("🖤 Negra");  b_ng.clicked.connect(lambda: self._set_remera(REMERA_NEGRA))
        vrm.addWidget(b_bl); vrm.addWidget(b_ng); izq.addWidget(gb_rm)

        b_exp = QPushButton("💾 Exportar"); b_exp.clicked.connect(self._exportar)
        izq.addWidget(b_exp)
        izq.addStretch()

        # ── Centro: propiedades de capa ────────────────────────────────────────
        self.panel_txt   = PanelTexto(self.solicitar_render)
        self.panel_img   = PanelImagen(self.solicitar_render)
        self.panel_vacio = QWidget()
        self.stack = QStackedWidget()
        self.stack.addWidget(self.panel_vacio)   # 0
        self.stack.addWidget(self.panel_txt)     # 1
        self.stack.addWidget(self.panel_img)     # 2
        self.stack.setMinimumWidth(270)

        # ── Derecha: canvas ────────────────────────────────────────────────────
        self.canvas = CanvasWidget(CANVAS_W, CANVAS_H)
        self.canvas.changed.connect(self.solicitar_render)

        root.addLayout(izq, 2)
        root.addWidget(self.stack, 3)
        root.addWidget(self.canvas, 4)

    # ── Fuentes ────────────────────────────────────────────────────────────────

    def _cargar_fuentes(self):
        self.fuentes = []
        if not os.path.isdir(CARPETA_FUENTES): return
        for arch in sorted(os.listdir(CARPETA_FUENTES)):
            if arch.lower().endswith((".ttf",".otf")):
                path = os.path.join(CARPETA_FUENTES, arch)
                fid  = QFontDatabase.addApplicationFont(path)
                if fid != -1:
                    fams = QFontDatabase.applicationFontFamilies(fid)
                    if fams:
                        self.fuentes.append((path, fams[0]))
                        self.lista_fuentes.addItem("Elegir esta fuente")
                        item = self.lista_fuentes.item(self.lista_fuentes.count()-1)
                        item.setFont(QFont(fams[0], 12))

    def _sel_fuente(self, idx):
        if idx >= 0:
            self.ruta_fuente = self.fuentes[idx][0]
            self.canvas.set_state(self.capas, self.capa_activa, self.ruta_fuente)
            self.solicitar_render()

    # ── Capas ──────────────────────────────────────────────────────────────────

    def _nueva_capa_texto(self):
        c = CapaTexto(); self.capas.append(c)
        self._refresh_lista(); self.lista_capas.setCurrentRow(len(self.capas)-1)

    def _nueva_capa_img(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar imagen", "",
            "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not path: return
        # calcular escala inicial: fitear al 35% del canvas
        try:
            pil = Image.open(path)
            max_dim = max(pil.width, pil.height)
            target  = min(CANVAS_W, CANVAS_H) * 0.35
            escala  = target / max_dim if max_dim > 0 else 1.0
        except:
            escala = 1.0
        c = CapaImagen(path, escala=escala)
        self.capas.append(c)
        self._refresh_lista(); self.lista_capas.setCurrentRow(len(self.capas)-1)

    def _del_capa(self):
        idx = self.lista_capas.currentRow()
        if 0 <= idx < len(self.capas):
            self.capas.pop(idx)
            self._refresh_lista()
            nuevo = min(idx, len(self.capas)-1)
            if nuevo >= 0: self.lista_capas.setCurrentRow(nuevo)
            else:
                self.capa_activa = None
                self.canvas.set_state(self.capas, None, self.ruta_fuente)
                self.stack.setCurrentIndex(0)
                self.solicitar_render()

    def _up_capa(self):
        idx = self.lista_capas.currentRow()
        if idx > 0:
            self.capas[idx], self.capas[idx-1] = self.capas[idx-1], self.capas[idx]
            self._refresh_lista(); self.lista_capas.setCurrentRow(idx-1)

    def _dn_capa(self):
        idx = self.lista_capas.currentRow()
        if idx < len(self.capas)-1:
            self.capas[idx], self.capas[idx+1] = self.capas[idx+1], self.capas[idx]
            self._refresh_lista(); self.lista_capas.setCurrentRow(idx+1)

    def _refresh_lista(self):
        self.lista_capas.blockSignals(True); self.lista_capas.clear()
        for c in self.capas:
            self.lista_capas.addItem(f"{'T' if c.tipo=='texto' else '🖼'}  {c.nombre}")
        self.lista_capas.blockSignals(False)

    def _sel_capa(self, idx):
        if 0 <= idx < len(self.capas):
            self.capa_activa = self.capas[idx]
            self.canvas.set_state(self.capas, self.capa_activa, self.ruta_fuente)
            if self.capa_activa.tipo == "texto":
                self.panel_txt.cargar(self.capa_activa); self.stack.setCurrentIndex(1)
            else:
                self.panel_img.cargar(self.capa_activa); self.stack.setCurrentIndex(2)
        else:
            self.capa_activa = None
            self.canvas.set_state(self.capas, None, self.ruta_fuente)
            self.stack.setCurrentIndex(0)
        self.canvas.update()
        self.solicitar_render()

    # ── Remera ─────────────────────────────────────────────────────────────────

    def _set_remera(self, ruta):
        self.ruta_remera = ruta; self.solicitar_render()

    # ── Render con debounce ────────────────────────────────────────────────────

    def solicitar_render(self):
        """Reinicia el timer. El render real arranca 150 ms después del último cambio."""
        self._timer.start()

    def actualizar_preview(self):
        """Alias para compatibilidad con los paneles."""
        self.solicitar_render()

    def _lanzar_render(self):
        if not self.ruta_fuente or not os.path.exists(self.ruta_remera):
            return
        args = (
            self.ruta_remera,
            list(self.capas),       # copia superficial (suficiente, no mutamos durante render)
            self.ruta_fuente,
            self.sp_blur.value(),
            self.sp_opa.value(),
        )
        self._render_thread.solicitar(args)

    def _render_done(self, img):
        data = img.tobytes("raw","RGBA")
        qi   = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
        pix  = QPixmap.fromImage(qi).scaled(
            CANVAS_W, CANVAS_H,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.canvas.set_pixmap(pix)

    # ── Exportar ───────────────────────────────────────────────────────────────

    def _exportar(self):
        if not self.ruta_fuente: return
        img = renderizar_todo(
            self.ruta_remera, self.capas, self.ruta_fuente,
            self.sp_blur.value(), self.sp_opa.value()
        )
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar imagen",
            os.path.join(CARPETA_RESULTADOS, "resultado.png"),
            "PNG (*.png);;JPEG (*.jpg *.jpeg)"
        )
        if path: img.save(path); print("Guardado en:", path)


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    v   = App()
    v.resize(1200, 640)
    v.show()
    sys.exit(app.exec())
