// frontend/src/hooks/useRender.ts
import { useState, useCallback, useRef } from 'react';
import { renderMockup, exportMockup, RenderPayload } from '../api/renderApi';
import { Layer } from '../types';

export const useRender = () => {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isRendering, setIsRendering] = useState(false);
  const debounceRef = useRef<NodeJS.Timeout>();

  const render = useCallback(async (
    layers: Layer[],
    fuente: string,
    blur: number,
    opacidad: number,
    remera: string,
    width: number = 480,
    height: number = 500
  ) => {
    if (!fuente) return;
    
    // Limpiar timeout anterior
    if (debounceRef.current) clearTimeout(debounceRef.current);
    
    setIsRendering(true);
    
    debounceRef.current = setTimeout(async () => {
      try {
        const payload: RenderPayload = {
          remera_path: remera,
          capas: layers.filter(l => l.visible),
          fuente,
          blur,
          opacidad,
          width,
          height,
        };
        
        const data = await renderMockup(payload);
        const imageUrl = `data:image/png;base64,${data.image_base64}`;
        setPreviewUrl(imageUrl);
      } catch (error) {
        console.error('Render error:', error);
      } finally {
        setIsRendering(false);
      }
    }, 150); // 150ms debounce
  }, []);

  const exportImage = useCallback(async (
    layers: Layer[],
    fuente: string,
    blur: number,
    opacidad: number,
    remera: string
  ) => {
    try {
      const payload: RenderPayload = {
        remera_path: remera,
        capas: layers.filter(l => l.visible),
        fuente,
        blur,
        opacidad,
        width: 480,
        height: 500,
      };
      
      const data = await exportMockup(payload);
      const link = document.createElement('a');
      link.href = `data:image/png;base64,${data.image_base64}`;
      link.download = 'mockup.png';
      link.click();
    } catch (error) {
      console.error('Export error:', error);
    }
  }, []);

  return { previewUrl, isRendering, render, exportImage };
};