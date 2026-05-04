# backend/app/models.py
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Tuple
from enum import Enum

MAX_DIMENSION = 1920

class LayerType(str, Enum):
    TEXT = "texto"
    IMAGE = "imagen"

class TextStyle(BaseModel):
    color: Optional[Tuple[int, int, int, int]] = None
    tamano: Optional[int] = None
    negrita: Optional[bool] = None
    cursiva: Optional[bool] = None
    subrayado: Optional[bool] = None

class TextLayer(BaseModel):
    id: int
    tipo: LayerType = LayerType.TEXT
    nombre: str
    visible: bool = True
    texto: str
    nx: float = 0.5  # posición normalizada 0-1
    ny: float = 0.45
    tamano: int = 60
    escala: float = 1.0
    rotacion: float = 0.0
    color: Optional[Tuple[int, int, int, int]] = None
    negrita: bool = False
    cursiva: bool = False
    subrayado: bool = False
    interlineado: float = 1.3
    alineacion: str = "center"
    estilos_token: Dict[str, TextStyle] = {}

class ImageLayer(BaseModel):
    id: int
    tipo: LayerType = LayerType.IMAGE
    nombre: str
    visible: bool = True
    ruta: str  # URL o base64 en producción
    nx: float = 0.5
    ny: float = 0.45
    escala: float = 1.0
    rotacion: float = 0.0

class RenderRequest(BaseModel):
    remera_path: str  # "blanca" o "negra" o ruta completa
    capas: List[dict]  # Se validan en runtime
    fuente: str
    blur: float = 0.0
    opacidad: float = 1.0
    width: int = 480
    height: int = 500

    @field_validator("width", "height")
    @classmethod
    def limitar_dimensiones(cls, v: int) -> int:
        if v < 1 or v > MAX_DIMENSION:
            raise ValueError(f"La dimensión debe estar entre 1 y {MAX_DIMENSION} px")
        return v

class RenderResponse(BaseModel):
    image_base64: str
    width: int
    height: int