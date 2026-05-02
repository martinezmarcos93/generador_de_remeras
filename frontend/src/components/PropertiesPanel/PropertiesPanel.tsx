// frontend/src/components/PropertiesPanel/PropertiesPanel.tsx
import React from 'react';
import { Layer, TextLayer, ImageLayer } from '../../types';

interface PropertiesPanelProps {
  layer: Layer | null;
  onUpdate: (id: number, updates: Partial<Layer>) => void;
}

export const PropertiesPanel: React.FC<PropertiesPanelProps> = ({ layer, onUpdate }) => {
  if (!layer) {
    return <div style={{ padding: '20px', color: '#666' }}>Seleccioná una capa</div>;
  }

  if (layer.tipo === 'texto') {
    const textLayer = layer as TextLayer;
    return (
      <div style={{ padding: '10px', color: '#ddd' }}>
        <h3 style={{ margin: '0 0 10px', fontSize: '14px' }}>Propiedades de Texto</h3>
        
        <div style={rowStyle}>
          <label>Texto:</label>
          <textarea
            value={textLayer.texto}
            onChange={(e) => onUpdate(layer.id, { texto: e.target.value })}
            style={{ width: '100%', height: '60px', background: '#252525', color: '#ddd', border: '1px solid #555' }}
          />
        </div>

        <div style={rowStyle}>
          <label>Tamaño:</label>
          <input
            type="number"
            value={textLayer.tamano}
            onChange={(e) => onUpdate(layer.id, { tamano: Number(e.target.value) })}
            style={inputStyle}
            min={6}
            max={400}
          />
        </div>

        <div style={rowStyle}>
          <label>Rotación:</label>
          <input
            type="number"
            value={textLayer.rotacion}
            onChange={(e) => onUpdate(layer.id, { rotacion: Number(e.target.value) })}
            style={inputStyle}
          />
        </div>

        <div style={rowStyle}>
          <label>Interlineado:</label>
          <input
            type="number"
            step={0.1}
            value={textLayer.interlineado}
            onChange={(e) => onUpdate(layer.id, { interlineado: Number(e.target.value) })}
            style={inputStyle}
          />
        </div>

        <div style={rowStyle}>
          <label>Alineación:</label>
          <div style={{ display: 'flex', gap: '5px' }}>
            {(['left', 'center', 'right'] as const).map(a => (
              <button
                key={a}
                onClick={() => onUpdate(layer.id, { alineacion: a })}
                style={{
                  ...btnStyle,
                  background: textLayer.alineacion === a ? '#0078d4' : '#2d2d2d',
                }}
              >
                {a === 'left' ? '←' : a === 'center' ? '≡' : '→'}
              </button>
            ))}
          </div>
        </div>

        <div style={rowStyle}>
          <label>Estilo:</label>
          <div style={{ display: 'flex', gap: '10px' }}>
            <label>
              <input
                type="checkbox"
                checked={textLayer.negrita}
                onChange={(e) => onUpdate(layer.id, { negrita: e.target.checked })}
              /> B
            </label>
            <label>
              <input
                type="checkbox"
                checked={textLayer.cursiva}
                onChange={(e) => onUpdate(layer.id, { cursiva: e.target.checked })}
              /> I
            </label>
            <label>
              <input
                type="checkbox"
                checked={textLayer.subrayado}
                onChange={(e) => onUpdate(layer.id, { subrayado: e.target.checked })}
              /> U
            </label>
          </div>
        </div>
      </div>
    );
  }

  // Capa de imagen
  const imgLayer = layer as ImageLayer;
  return (
    <div style={{ padding: '10px', color: '#ddd' }}>
      <h3 style={{ margin: '0 0 10px', fontSize: '14px' }}>Propiedades de Imagen</h3>
      <p style={{ color: '#888', fontSize: '12px' }}>{imgLayer.nombre}</p>
      
      <div style={rowStyle}>
        <label>Escala:</label>
        <input
          type="number"
          step={0.05}
          value={imgLayer.escala}
          onChange={(e) => onUpdate(layer.id, { escala: Number(e.target.value) })}
          style={inputStyle}
        />
      </div>

      <div style={rowStyle}>
        <label>Rotación:</label>
        <input
          type="number"
          value={imgLayer.rotacion}
          onChange={(e) => onUpdate(layer.id, { rotacion: Number(e.target.value) })}
          style={inputStyle}
        />
      </div>
    </div>
  );
};

const rowStyle: React.CSSProperties = { marginBottom: '10px' };
const inputStyle: React.CSSProperties = { 
  width: '80px', 
  background: '#252525', 
  color: '#ddd', 
  border: '1px solid #555',
  padding: '4px'
};
const btnStyle: React.CSSProperties = {
  padding: '4px 12px',
  border: '1px solid #555',
  borderRadius: '3px',
  color: '#ddd',
  cursor: 'pointer',
};