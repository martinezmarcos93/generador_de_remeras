// frontend/src/components/Canvas/Canvas.tsx
import React, { useEffect, useRef, useCallback } from 'react';
import { fabric } from 'fabric';
import { Layer, TextLayer, ImageLayer } from '../../types';

interface CanvasProps {
  width: number;
  height: number;
  layers: Layer[];
  activeLayerId: number | null;
  previewUrl: string | null;
  onLayerUpdate: (id: number, updates: Partial<Layer>) => void;
  onSelectLayer: (id: number) => void;
}

export const Canvas: React.FC<CanvasProps> = ({
  width,
  height,
  layers,
  activeLayerId,
  previewUrl,
  onLayerUpdate,
  onSelectLayer,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricRef = useRef<fabric.Canvas | null>(null);
  const isUpdating = useRef(false);

  // Inicializar Fabric.js
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const canvas = new fabric.Canvas(canvasRef.current, {
      width,
      height,
      backgroundColor: '#111',
      selection: false,
    });
    
    fabricRef.current = canvas;

    // Eventos de modificación
    canvas.on('object:modified', (e) => {
      if (isUpdating.current) return;
      const obj = e.target;
      if (!obj) return;
      
      const layerId = obj.data?.layerId;
      if (!layerId) return;

      const updates: Partial<Layer> = {
        nx: (obj.left! + obj.width! / 2) / width,
        ny: (obj.top! + obj.height! / 2) / height,
        escala: obj.scaleX!,
        rotacion: obj.angle!,
      };
      
      onLayerUpdate(layerId, updates);
    });

    canvas.on('selection:created', (e) => {
      const obj = e.selected?.[0];
      if (obj?.data?.layerId) {
        onSelectLayer(obj.data.layerId);
      }
    });

    canvas.on('selection:updated', (e) => {
      const obj = e.selected?.[0];
      if (obj?.data?.layerId) {
        onSelectLayer(obj.data.layerId);
      }
    });

    return () => {
      canvas.dispose();
      fabricRef.current = null;
    };
  }, [width, height]);

  // Actualizar objetos cuando cambian las capas
  useEffect(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;

    isUpdating.current = true;

    // Limpiar objetos que no corresponden a capas existentes
    const existingIds = new Set(layers.map(l => l.id));
    canvas.getObjects().forEach(obj => {
      if (obj.data?.layerId && !existingIds.has(obj.data.layerId)) {
        canvas.remove(obj);
      }
    });

    layers.forEach(layer => {
      if (!layer.visible) {
        // Ocultar objeto si existe
        const existing = canvas.getObjects().find(
          obj => obj.data?.layerId === layer.id
        );
        if (existing) {
          existing.visible = false;
        }
        return;
      }

      let obj = canvas.getObjects().find(
        o => o.data?.layerId === layer.id
      ) as fabric.Object | undefined;

      const isActive = layer.id === activeLayerId;

      if (layer.tipo === 'texto') {
        const textLayer = layer as TextLayer;
        if (!obj) {
          obj = new fabric.Textbox(textLayer.texto, {
            left: textLayer.nx * width - 100,
            top: textLayer.ny * height - 20,
            width: 200,
            fontSize: textLayer.tamano,
            fill: textLayer.color ? 
              `rgba(${textLayer.color[0]},${textLayer.color[1]},${textLayer.color[2]},${textLayer.color[3]/255})` 
              : '#fff',
            fontWeight: textLayer.negrita ? 'bold' : 'normal',
            fontStyle: textLayer.cursiva ? 'italic' : 'normal',
            textAlign: textLayer.alineacion,
            selectable: true,
            hasControls: isActive,
            hasBorders: isActive,
            cornerColor: '#0078d4',
            cornerStrokeColor: '#fff',
            cornerSize: 8,
            transparentCorners: false,
          });
          obj.data = { layerId: layer.id };
          canvas.add(obj);
        } else {
          // Actualizar propiedades
          (obj as fabric.Textbox).set({
            text: textLayer.texto,
            fontSize: textLayer.tamano,
            fill: textLayer.color ? 
              `rgba(${textLayer.color[0]},${textLayer.color[1]},${textLayer.color[2]},${textLayer.color[3]/255})` 
              : '#fff',
            fontWeight: textLayer.negrita ? 'bold' : 'normal',
            fontStyle: textLayer.cursiva ? 'italic' : 'normal',
            left: textLayer.nx * width - (obj.width || 200) / 2,
            top: textLayer.ny * height - (obj.height || 40) / 2,
            scaleX: textLayer.escala,
            scaleY: textLayer.escala,
            angle: textLayer.rotacion,
            hasControls: isActive,
            hasBorders: isActive,
            visible: true,
          });
        }
      } else {
        const imgLayer = layer as ImageLayer;
        if (!obj) {
          fabric.Image.fromURL(imgLayer.ruta, (img) => {
            img.set({
              left: imgLayer.nx * width - img.width! / 2,
              top: imgLayer.ny * height - img.height! / 2,
              scaleX: imgLayer.escala,
              scaleY: imgLayer.escala,
              angle: imgLayer.rotacion,
              selectable: true,
              hasControls: isActive,
              hasBorders: isActive,
              cornerColor: '#0078d4',
              cornerStrokeColor: '#fff',
              cornerSize: 8,
              transparentCorners: false,
            });
            img.data = { layerId: layer.id };
            canvas.add(img);
            canvas.renderAll();
          });
        } else {
          obj.set({
            left: imgLayer.nx * width - (obj.width || 100) / 2,
            top: imgLayer.ny * height - (obj.height || 100) / 2,
            scaleX: imgLayer.escala,
            scaleY: imgLayer.escala,
            angle: imgLayer.rotacion,
            hasControls: isActive,
            hasBorders: isActive,
            visible: true,
          });
        }
      }
    });

    canvas.renderAll();
    isUpdating.current = false;
  }, [layers, activeLayerId, width, height]);

  // Mostrar preview del render
  useEffect(() => {
    const canvas = fabricRef.current;
    if (!canvas || !previewUrl) return;

    // El preview se muestra como imagen de fondo o en un overlay
    // Por simplicidad, lo mostramos en un div superpuesto
  }, [previewUrl]);

  return (
    <div style={{ position: 'relative', width, height }}>
      <canvas ref={canvasRef} />
      {previewUrl && (
        <img
          src={previewUrl}
          alt="Preview"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width,
            height,
            pointerEvents: 'none',
            opacity: 0.9,
          }}
        />
      )}
    </div>
  );
};