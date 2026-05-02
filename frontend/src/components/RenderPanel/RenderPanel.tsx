// frontend/src/components/RenderPanel/RenderPanel.tsx
import React from 'react';

interface RenderPanelProps {
  blur: number;
  opacidad: number;
  remera: 'blanca' | 'negra';
  onBlurChange: (v: number) => void;
  onOpacidadChange: (v: number) => void;
  onRemeraChange: (v: 'blanca' | 'negra') => void;
  onExport: () => void;
  isRendering: boolean;
}

export const RenderPanel: React.FC<RenderPanelProps> = ({
  blur,
  opacidad,
  remera,
  onBlurChange,
  onOpacidadChange,
  onRemeraChange,
  onExport,
  isRendering,
}) => {
  return (
    <div style={{ padding: '10px', color: '#ddd' }}>
      <h3 style={{ margin: '0 0 10px', fontSize: '14px' }}>Render</h3>
      
      <div style={rowStyle}>
        <label>Blur: {blur}</label>
        <input
          type="range"
          min={0}
          max={8}
          step={0.1}
          value={blur}
          onChange={(e) => onBlurChange(Number(e.target.value))}
          style={{ width: '100%' }}
        />
      </div>

      <div style={rowStyle}>
        <label>Opacidad: {opacidad}</label>
        <input
          type="range"
          min={0.05}
          max={1}
          step={0.05}
          value={opacidad}
          onChange={(e) => onOpacidadChange(Number(e.target.value))}
          style={{ width: '100%' }}
        />
      </div>

      <div style={rowStyle}>
        <label>Remera:</label>
        <div style={{ display: 'flex', gap: '5px', marginTop: '5px' }}>
          <button
            onClick={() => onRemeraChange('blanca')}
            style={{
              ...btnStyle,
              background: remera === 'blanca' ? '#0078d4' : '#2d2d2d',
            }}
          >
            🤍 Blanca
          </button>
          <button
            onClick={() => onRemeraChange('negra')}
            style={{
              ...btnStyle,
              background: remera === 'negra' ? '#0078d4' : '#2d2d2d',
            }}
          >
            🖤 Negra
          </button>
        </div>
      </div>

      <button
        onClick={onExport}
        disabled={isRendering}
        style={{
          ...btnStyle,
          width: '100%',
          marginTop: '10px',
          background: isRendering ? '#444' : '#2d8a3e',
        }}
      >
        {isRendering ? 'Renderizando...' : '💾 Exportar'}
      </button>
    </div>
  );
};

const rowStyle: React.CSSProperties = { marginBottom: '12px' };
const btnStyle: React.CSSProperties = {
  padding: '8px 16px',
  border: '1px solid #555',
  borderRadius: '3px',
  color: '#fff',
  cursor: 'pointer',
};