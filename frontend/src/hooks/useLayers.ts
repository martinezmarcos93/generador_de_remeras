// frontend/src/hooks/useLayers.ts
import { useState, useCallback } from 'react';
import { Layer, TextLayer, ImageLayer } from '../types';

let idCounter = 0;

export const useLayers = () => {
  const [layers, setLayers] = useState<Layer[]>([]);
  const [activeLayerId, setActiveLayerId] = useState<number | null>(null);

  const activeLayer = layers.find(l => l.id === activeLayerId) || null;

  const addTextLayer = useCallback(() => {
    idCounter++;
    const newLayer: TextLayer = {
      id: idCounter,
      tipo: 'texto',
      nombre: `Texto ${idCounter}`,
      visible: true,
      texto: 'Texto',
      nx: 0.5,
      ny: 0.45,
      tamano: 60,
      escala: 1,
      rotacion: 0,
      negrita: false,
      cursiva: false,
      subrayado: false,
      interlineado: 1.3,
      alineacion: 'center',
      estilos_token: {},
    };
    setLayers(prev => [...prev, newLayer]);
    setActiveLayerId(newLayer.id);
  }, []);

  const addImageLayer = useCallback((file: File) => {
    const url = URL.createObjectURL(file);
    idCounter++;
    const newLayer: ImageLayer = {
      id: idCounter,
      tipo: 'imagen',
      nombre: file.name,
      visible: true,
      ruta: url,
      nx: 0.5,
      ny: 0.45,
      escala: 1,
      rotacion: 0,
    };
    setLayers(prev => [...prev, newLayer]);
    setActiveLayerId(newLayer.id);
  }, []);

  const updateLayer = useCallback((id: number, updates: Partial<Layer>) => {
    setLayers(prev => prev.map(l => 
      l.id === id ? { ...l, ...updates } as Layer : l
    ));
  }, []);

  const deleteLayer = useCallback((id: number) => {
    setLayers(prev => {
      const filtered = prev.filter(l => l.id !== id);
      if (activeLayerId === id) {
        setActiveLayerId(filtered.length > 0 ? filtered[0].id : null);
      }
      return filtered;
    });
  }, [activeLayerId]);

  const moveLayer = useCallback((id: number, direction: 'up' | 'down') => {
    setLayers(prev => {
      const idx = prev.findIndex(l => l.id === id);
      if (idx === -1) return prev;
      const newIdx = direction === 'up' ? idx - 1 : idx + 1;
      if (newIdx < 0 || newIdx >= prev.length) return prev;
      const result = [...prev];
      [result[idx], result[newIdx]] = [result[newIdx], result[idx]];
      return result;
    });
  }, []);

  const toggleVisibility = useCallback((id: number) => {
    setLayers(prev => prev.map(l => 
      l.id === id ? { ...l, visible: !l.visible } : l
    ));
  }, []);

  return {
    layers,
    activeLayer,
    activeLayerId,
    setActiveLayerId,
    addTextLayer,
    addImageLayer,
    updateLayer,
    deleteLayer,
    moveLayer,
    toggleVisibility,
  };
};