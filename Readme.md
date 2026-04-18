# 🧢 Simulador de Estampado de Remeras (Python + PyQt6)

Aplicación de escritorio para generar mockups de remeras con texto e imágenes personalizadas. Soporta múltiples capas, transformaciones interactivas con el mouse y renderizado en tiempo real sin trabar la interfaz.

---

## 🚀 Características

### Sistema de capas
- Múltiples capas de texto e imagen apilables
- Reordenar capas (↑↓), eliminar y alternar visibilidad
- Cada capa tiene posición, escala y rotación independientes

### Canvas interactivo (tipo Figma)
- **Arrastrar** el objeto → mover
- **Arrastrar esquina** (handle blanco) → escalar proporcionalmente
- **Ctrl + arrastrar esquina** → rotar libremente
- Bounding box visual con 8 handles sobre la capa activa

### Capas de texto
- Texto multi-línea
- Tamaño, color, negrita, cursiva y subrayado **globales por capa**
- Override de color, tamaño, negrita y cursiva **por palabra individual**
- Alineación izquierda / centro / derecha
- Interlineado ajustable
- Rotación desde panel o con Ctrl+mouse

### Capas de imagen
- Importar PNG, JPG, WEBP, BMP
- PNG con transparencia soportado nativamente
- Escala y rotación desde panel o directamente en canvas
- Al importar, la imagen se fittea automáticamente al ~35% del canvas

### Render
- **Hilo separado (QThread)** con debounce de 150 ms → la UI nunca se congela
- Blur gaussiano ajustable (0 = texto nítido)
- Opacidad ajustable
- Composición con `Image.alpha_composite` (Pillow)
- Soporte para remera blanca y negra (color de texto automático o personalizado)

### Exportación
- File dialog para elegir nombre y ubicación
- Formatos: PNG y JPEG
- Resolución original de la imagen de remera

---

## 📦 Requisitos

- Python 3.10+
- PyQt6
- Pillow

```bash
pip install PyQt6 pillow
```

---

## 📁 Estructura del proyecto

```
proyecto/
│
├── main.py
├── remera_blanca.png
├── remera_negra.png
│
├── fuentes/
│   ├── fuente1.ttf        # .ttf y .otf soportados
│   ├── fuente1-Bold.ttf   # variantes opcionales (negrita/cursiva)
│   └── fuente2.ttf
│
└── resultados/
    └── resultado.png
```

> Las variantes de fuente (`-Bold`, `-Italic`, `-BoldItalic`) son opcionales. Si no existen, se usa la fuente base.

---

## ▶️ Uso

```bash
python main.py
```

**Flujo básico:**

1. Seleccioná una fuente en el panel central
2. Creá una capa de texto (botón `＋T`) o de imagen (`＋🖼`)
3. Editá el contenido y estilo en el panel de propiedades
4. Mové, escalá y rotá directamente en el canvas con el mouse
5. Ajustá blur y opacidad en "Render"
6. Exportá con `💾 Exportar`

---

## 🧠 Notas técnicas

- El render corre en `RenderThread` (QThread) para no bloquear la UI
- El debounce de 150 ms evita renders innecesarios mientras se escribe o arrastra
- Las transformaciones (escala, rotación) se aplican en tiempo de render sobre una capa temporal con padding, evitando recortes
- El bounding box del canvas es una aproximación visual; el render final es pixel-perfect

---

## 🗺️ Roadmap (guardado para después)

- **Realismo de estampado**: displacement maps, blend modes (multiply/overlay), textura de serigrafía
- **Historial / undo-redo**
- **Warp de texto** (arco, curva)
- **Exportación en alta resolución** (300 DPI)
- **Batch rendering** (múltiples colores de remera)
- **API local** (Flask/FastAPI: POST texto → mockup)
- **Versión web** (Fabric.js / Konva + backend Python)

---

## 📄 Licencia

Libre uso — MIT recomendado.

## 👤 Autor

Marcos
