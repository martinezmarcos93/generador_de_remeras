// frontend/src/components/LayersPanel/LayersPanel.tsx
import React from 'react';
import { Layer } from '../../types';

interface LayersPanelProps {
  layers: Layer[];
  activeLayerId: number | null;
  onSelectLayer: (id: number) => void;
  onAddText: () => void;
  onAddImage: (file: File) => void;
  onDeleteLayer: (id: number) => void;
  onMoveLayer: (id: number, direction: 'up' | 'down') => void;
  onToggleVisibility: (id: number) => void;
}

export const LayersPanel: React.FC<LayersPanelProps> = ({
  layers,
  activeLayerId,
  onSelectLayer,
  onAddText,
  onAddImage,
  onDeleteLayer,
  onMoveLayer,
  onToggleVisibility,
}) => {
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onAddImage(file);
  };

  return (
    <div style={{ padding: '10px', background: '#1e1e1e', color: '#ddd' }}>
      <h3 style={{ margin: '0 0 10px', fontSize: '14px' }}>Capas</h3>
      
      <div style={{ marginBottom: '10px', display: 'flex', gap: '5px' }}>
        <button onClick={onAddText} style={btnStyle}>＋T</button>
        <button onClick={() => fileInputRef.current?.click()} style={btnStyle}>＋🖼</button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          style={{ display: 'none' }}
        />
      </div>

      <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
        {layers.map((layer, index) => (
          <div
            key={layer.id}
            onClick={() => onSelectLayer(layer.id)}
            style={{
              padding: '6px 8px',
              cursor: 'pointer',
              background: layer.id === activeLayerId ? '#0078d4' : 'transparent',
              borderRadius: '3px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '2px',
            }}
          >
            <span onClick={(e) => { e.stopPropagation(); onToggleVisibility(layer.id); }}>
              {layer.visible ? '👁' : '🚫'}
            </span>
            <span style={{ flex: 1, fontSize: '12px' }}>
              {layer.tipo === 'texto' ? 'T' : '🖼'} {layer.nombre}
            </span>
            <button onClick={(e) => { e.stopPropagation(); onMoveLayer(layer.id, 'up'); }} 
                    disabled={index === 0} style={smallBtn}>↑</button>
            <button onClick={(e) => { e.stopPropagation(); onMoveLayer(layer.id, 'down'); }} 
                    disabled={index === layers.length - 1} style={smallBtn}>↓</button>
            <button onClick={(e) => { e.stopPropagation(); onDeleteLayer(layer.id); }} 
                    style={smallBtn}>🗑</button>
          </div>
        ))}
      </div>
    </div>
  );
};

const btnStyle: React.CSSProperties = {
  background: '#2d2d2d',
  border: '1px solid #555',
  color: '#ddd',
  padding: '4px 10px',
  borderRadius: '3px',
  cursor: 'pointer',
};

const smallBtn: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  color: '#888',
  cursor: 'pointer',
  padding: '2px 4px',
};