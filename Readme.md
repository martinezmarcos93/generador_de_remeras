# 🧢 Simulador de Estampado de Remeras — Branch `hybrid`

> **⚠️ Esta es la branch `hybrid` del proyecto.**  
> Aquí el simulador fue reescrito como aplicación híbrida: **React + TypeScript** en el frontend y **Python + FastAPI** en el backend. La versión original 100 % Python + PyQt6 vive en la branch `main`.

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + TS)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  React UI   │  │  Fabric.js  │  │  Estado de capas    │ │
│  │  (paneles)  │  │  (canvas)   │  │  (Hooks / Context)  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                           │                                  │
│                    HTTP (REST)                               │
│                           │                                  │
└───────────────────────────┼─────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                    BACKEND (Python)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  FastAPI    │  │  Pillow     │  │  Render engine      │ │
│  │  (API REST) │  │  (PIL)      │  │  (composición)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### ¿Por qué híbrido?

| Aspecto | React/TS | Python |
|---------|----------|--------|
| **Canvas interactivo** | ✅ Fabric.js nativo, 60 fps, multi-touch | ❌ PyQt6 más lento y pesado |
| **Hot reload / DX** | ✅ Instantáneo con Vite | ❌ Lento |
| **Deploy frontend** | ✅ Vercel / Netlify / estático | ❌ Requiere servidor |
| **Renderizado de imágenes** | ❌ Limitado (browser canvas 2D) | ✅ Pillow superior |
| **Fuentes tipográficas** | ❌ Web fonts limitadas | ✅ Cualquier `.ttf` / `.otf` |
| **Exportación alta calidad** | ❌ 96 DPI del navegador | ✅ 300 DPI con Pillow |
| **Blur, composición, filtros** | ❌ Básicos | ✅ Avanzados |

---

## 📦 Estructura del proyecto

```
tshirt-mockup-hybrid/          # ← branch hybrid
│
├── frontend/                  # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── Canvas/        # Fabric.js — canvas interactivo
│   │   │   ├── LayersPanel/   # Lista de capas (↑↓, 🗑, 👁)
│   │   │   ├── PropertiesPanel/  # Props de texto / imagen
│   │   │   └── RenderPanel/   # Blur, opacidad, exportar
│   │   ├── hooks/
│   │   │   ├── useLayers.ts   # Estado global de capas
│   │   │   └── useRender.ts   # Comunicación con API + debounce
│   │   ├── api/
│   │   │   └── renderApi.ts   # Cliente HTTP para FastAPI
│   │   └── types/
│   │       └── index.ts       # Interfaces TypeScript
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                   # Python + FastAPI
│   ├── app/
│   │   ├── main.py            # Endpoints /render y /export
│   │   ├── render.py          # Motor de renderizado Pillow
│   │   ├── models.py          # Pydantic models
│   │   └── fonts/             # Fuentes .ttf / .otf
│   ├── assets/
│   │   ├── remera_blanca.png
│   │   └── remera_negra.png
│   ├── requirements.txt
│   └── Dockerfile
│
└── README.md                  # ← este archivo
```

---

## 🚀 Requisitos

- **Node.js** 18+ (frontend)
- **Python** 3.10+ (backend)
- **npm** o **yarn**

---

## ▶️ Instalación y uso

### 1. Backend (Python)

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scriptsctivate         # Windows

# Instalar dependencias
pip install -r requirements.txt

# Copiar assets (remeras y fuentes)
mkdir -p app/fonts assets
cp /ruta/a/tus/fuentes/*.ttf app/fonts/
cp /ruta/a/remera_blanca.png assets/
cp /ruta/a/remera_negra.png assets/

# Levantar servidor
uvicorn app.main:app --reload --port 8000
```

El backend quedará disponible en `http://localhost:8000`.

### 2. Frontend (React)

```bash
cd frontend

# Instalar dependencias
npm install

# Levantar servidor de desarrollo
npm run dev
```

El frontend quedará disponible en `http://localhost:5173`.

---

## 🧠 API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/fonts` | Lista fuentes disponibles en `app/fonts/` |
| `POST` | `/render` | Renderiza preview (480×500 px) → devuelve `base64` |
| `POST` | `/export` | Exporta en alta resolución (4× = 1920×2000 px) → `base64` |

### Ejemplo de payload `/render`

```json
{
  "remera_path": "negra",
  "capas": [
    {
      "tipo": "texto",
      "visible": true,
      "texto": "Hola Mundo",
      "nx": 0.5,
      "ny": 0.45,
      "tamano": 60,
      "escala": 1.0,
      "rotacion": 0,
      "alineacion": "center",
      "estilos_token": {}
    }
  ],
  "fuente": "/abs/path/to/fuente.ttf",
  "blur": 0.4,
  "opacidad": 0.93,
  "width": 480,
  "height": 500
}
```

---

## 🎨 Flujo de trabajo

1. **Seleccioná una fuente** en el panel izquierdo.
2. **Creá capas** con `＋T` (texto) o `＋🖼` (imagen).
3. **Editá propiedades** en el panel central (tamaño, color, rotación, etc.).
4. **Mové, escalá y rotá** directamente en el canvas con el mouse (Fabric.js handles).
5. **Ajustá blur y opacidad** en el panel "Render".
6. **Exportá** con `💾 Exportar` — el backend genera la imagen final en alta resolución.

---

## 🔀 Diferencias con la branch `main` (PyQt6)

| Característica | `main` (PyQt6) | `hybrid` (React + FastAPI) |
|----------------|----------------|----------------------------|
| Framework UI | PyQt6 | React 18 + Fabric.js |
| Canvas | QPainter custom | Fabric.js (handles nativos) |
| Lenguaje | Python 100 % | TypeScript + Python |
| Estado | Clases Python | React Hooks (useState/useEffect) |
| Comunicación | Todo en proceso | HTTP REST entre procesos |
| Preview | QPixmap local | Base64 desde API |
| Exportación | File dialog nativo | Descarga desde navegador |
| Deploy | App de escritorio | Web app + API independiente |

---

## 🗺️ Roadmap de la branch `hybrid`

- [ ] **WebSocket** para renderizado en tiempo real (sin polling)
- [ ] **Caché de renders** (Redis / memoria) para capas sin cambios
- [ ] **Undo / redo** con historial de estado inmutable
- [ ] **Autenticación** (OAuth2) para guardar proyectos en cloud
- [ ] **Base de datos** (PostgreSQL) para proyectos y assets
- [ ] **Batch rendering** — múltiples colores de remera en paralelo
- [ ] **Warp de texto** (arco, curva) con Pillow
- [ ] **Displacement maps** y blend modes para realismo de estampado

---

## 🐛 Troubleshooting

### CORS errors
Asegurate de que el backend tenga `allow_origins` con la URL del frontend (`http://localhost:5173`).

### Fuentes no cargan
Verificá que las fuentes estén en `backend/app/fonts/` y que sean `.ttf` o `.otf`.

### El canvas no muestra la imagen renderizada
Revisá la consola del navegador — el backend debe estar corriendo en `:8000` y el payload debe incluir la ruta absoluta de la fuente.

---

## 📄 Licencia

MIT — Libre uso.

## 👤 Autor

Marcos
