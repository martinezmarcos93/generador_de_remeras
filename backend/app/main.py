# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os

from .render import renderizar_todo, image_to_base64
from .models import RenderRequest, RenderResponse

app = FastAPI(title="T-Shirt Mockup API")

_cors_env = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
CORS_ORIGINS = [o.strip() for o in _cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FONTS_DIR = os.path.join(BASE_DIR, "app", "fonts")
REMERAS = {
    "blanca": os.path.join(BASE_DIR, "assets", "remera_blanca.png"),
    "negra": os.path.join(BASE_DIR, "assets", "remera_negra.png"),
}

@app.get("/fonts")
async def list_fonts():
    """Lista las fuentes disponibles."""
    fonts = []
    if os.path.exists(FONTS_DIR):
        for f in os.listdir(FONTS_DIR):
            if f.lower().endswith((".ttf", ".otf")):
                fonts.append({"name": f, "path": os.path.join(FONTS_DIR, f)})
    return {"fonts": fonts}

@app.post("/render", response_model=RenderResponse)
async def render(request: RenderRequest):
    """Renderiza el mockup y devuelve imagen base64."""
    try:
        remera_path = REMERAS.get(request.remera_path, request.remera_path)
        if not os.path.exists(remera_path):
            raise HTTPException(status_code=404, detail=f"Remera no encontrada: {remera_path}")
        
        if not os.path.exists(request.fuente):
            raise HTTPException(status_code=404, detail=f"Fuente no encontrada: {request.fuente}")
        
        img = renderizar_todo(
            remera_path=remera_path,
            capas=request.capas,
            ruta_fuente=request.fuente,
            blur=request.blur,
            opa=request.opacidad,
            W=request.width,
            H=request.height
        )
        
        return RenderResponse(
            image_base64=image_to_base64(img),
            width=img.width,
            height=img.height
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export")
async def export(request: RenderRequest):
    """Exporta en alta resolución (300 DPI)."""
    try:
        remera_path = REMERAS.get(request.remera_path, request.remera_path)
        if not os.path.exists(remera_path):
            raise HTTPException(status_code=404, detail=f"Remera no encontrada: {remera_path}")

        if not os.path.exists(request.fuente):
            raise HTTPException(status_code=404, detail=f"Fuente no encontrada: {request.fuente}")

        # Para exportación, usamos resolución 4x
        img = renderizar_todo(
            remera_path=remera_path,
            capas=request.capas,
            ruta_fuente=request.fuente,
            blur=request.blur,
            opa=request.opacidad,
            W=request.width * 4,
            H=request.height * 4
        )
        return RenderResponse(
            image_base64=image_to_base64(img, "PNG"),
            width=img.width,
            height=img.height
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)