🧢 Simulador de Estampado de Remeras (Python + PyQt6)

Aplicación de escritorio para generar mockups de remeras con texto personalizado. Permite seleccionar tipografías visualmente, configurar el contenido y ver el resultado en tiempo real antes de exportar la imagen final.

🚀 Características
Renderizado en tiempo real del estampado
Selector visual de fuentes (cada fuente se muestra aplicada)
Soporte para múltiples tipografías .ttf
Cambio dinámico entre remera blanca y negra
Ajuste de tamaño de texto
Exportación directa del resultado
Simulación básica de estampado (blur + opacidad)
📦 Requisitos
Python 3.10+
Librerías:
PyQt6
Pillow

Instalación:

pip install PyQt6 pillow
📁 Estructura del proyecto
proyecto/
│
├── main.py
├── remera_blanca.png
├── remera_negra.png
│
├── fuentes/
│   ├── fuente1.ttf
│   ├── fuente2.ttf
│
└── resultados/
    └── resultado.png
▶️ Uso

Ejecutar la aplicación:

python main.py
Flujo:
Escribí el texto que querés estampar
Seleccioná el tamaño
Elegí tipo de remera
Seleccioná una fuente (preview en vivo)
Visualizá el resultado en el panel derecho
Exportá la imagen
🧠 Notas técnicas
Las fuentes se cargan dinámicamente desde la carpeta fuentes/
El render del estampado usa:
Capa separada
Desenfoque gaussiano
Reducción de opacidad
La composición se realiza con Image.alpha_composite (Pillow)
PyQt6 se utiliza para la interfaz y render en tiempo real
⚠️ Limitaciones actuales
No hay posicionamiento manual del texto
No soporta múltiples líneas complejas (alineación avanzada)
Simulación de estampado básica (no usa displacement maps)
Sin soporte para colores personalizados (solo blanco/negro automático)
🛠 Posibles mejoras
Drag & drop para posicionar texto
Soporte multi-línea y alineación (izq/centro/der)
Selector de color
Mockups más realistas (mapas de desplazamiento)
Exportación en distintos formatos
Interfaz web (Flask o frontend dedicado)
📌 Objetivo del proyecto

Este proyecto funciona como base para:

Generadores de mockups de ropa
Herramientas de diseño rápido
Sistemas de personalización para e-commerce
Experimentos con renderizado de texto sobre superficies
📄 Licencia

Libre uso. Ajustar según necesidad (MIT recomendado).

👤 Autor

Marcos