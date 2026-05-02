// frontend/src/App.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { Canvas } from './components/Canvas/Canvas';
import { LayersPanel } from './components/LayersPanel/LayersPanel';
import { PropertiesPanel } from './components/PropertiesPanel/PropertiesPanel';
import { RenderPanel } from './components/RenderPanel/RenderPanel';
import { useLayers } from './hooks/useLayers';
import { useRender } from './hooks/useRender';
import { listFonts } from './api/renderApi';

const CANVAS_W = 480;
const CANVAS_H = 500;

const App: React.FC = () => {
  const {
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
  } = useLayers();

  const { previewUrl, isRendering, render, exportImage } = useRender();
  
  const [fonts, setFonts] = useState<{ name: string; path: string }[]>([]);
  const [selectedFont, setSelectedFont] = useState<string>('');
  const [blur, setBlur] = useState(0.4);
  const [opacidad, setOpacidad] = useState(0.93);
  const [remera, setRemera] = useState<'blanca' | 'negra'>('negra');

  // Cargar fuentes
  useEffect(() => {
    listFonts().then(f => {
      setFonts(f);
      if (f.length > 0) setSelectedFont(f[0].path);
    });
  }, []);

  // Render automático cuando cambian las capas o settings
  useEffect(() => {
    render(layers, selectedFont, blur, opacidad, remera, CANVAS_W, CANVAS_H);
  }, [layers, selectedFont, blur, opacidad, remera]);

  const handleExport = useCallback(() => {
    exportImage(layers, selectedFont, blur, opacidad, remera);
  }, [layers, selectedFont, blur, opacidad, remera]);

  return (
    <div style={{ 
      display: 'flex', 
      height: '100vh', 
      background: '#1e1e1e',
      fontFamily: 'system-ui, sans-serif',
      fontSize: '12px',
    }}>
      {/* Panel izquierdo */}
      <div style={{ 
        width: '220px', 
        borderRight: '1px solid #333',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        overflowY: 'auto',
      }}>
        <LayersPanel
          layers={layers}
          activeLayerId={activeLayerId}
          onSelectLayer={setActiveLayerId}
          onAddText={addTextLayer}
          onAddImage={addImageLayer}
          onDeleteLayer={deleteLayer}
          onMoveLayer={moveLayer}
          onToggleVisibility={toggleVisibility}
        />

        <div style={{ padding: '10px', borderTop: '1px solid #333' }}>
          <h3 style={{ margin: '0 0 8px', fontSize: '14px', color: '#ddd' }}>Fuente</h3>
          <select
            value={selectedFont}
            onChange={(e) => setSelectedFont(e.target.value)}
            style={{ 
              width: '100%', 
              background: '#252525', 
              color: '#ddd',
              border: '1px solid #555',
              padding: '4px',
            }}
          >
            {fonts.map(f => (
              <option key={f.path} value={f.path}>{f.name}</option>
            ))}
          </select>
        </div>

        <RenderPanel
          blur={blur}
          opacidad={opacidad}
          remera={remera}
          onBlurChange={setBlur}
          onOpacidadChange={setOpacidad}
          onRemeraChange={setRemera}
          onExport={handleExport}
          isRendering={isRendering}
        />
      </div>

      {/* Panel central - Propiedades */}
      <div style={{ 
        width: '280px', 
        borderRight: '1px solid #333',
        background: '#1e1e1e',
      }}>
        <PropertiesPanel
          layer={activeLayer}
          onUpdate={updateLayer}
        />
      </div>

      {/* Panel derecho - Canvas */}
      <div style={{ 
        flex: 1, 
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#111',
      }}>
        <Canvas
          width={CANVAS_W}
          height={CANVAS_H}
          layers={layers}
          activeLayerId={activeLayerId}
          previewUrl={previewUrl}
          onLayerUpdate={updateLayer}
          onSelectLayer={setActiveLayerId}
        />
      </div>
    </div>
  );
};

export default App;