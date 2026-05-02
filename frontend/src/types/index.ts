// frontend/src/types/index.ts
export interface TokenStyle {
  color?: [number, number, number, number];
  tamano?: number;
  negrita?: boolean;
  cursiva?: boolean;
  subrayado?: boolean;
}

export interface TextLayer {
  id: number;
  tipo: 'texto';
  nombre: string;
  visible: boolean;
  texto: string;
  nx: number;
  ny: number;
  tamano: number;
  escala: number;
  rotacion: number;
  color?: [number, number, number, number];
  negrita: boolean;
  cursiva: boolean;
  subrayado: boolean;
  interlineado: number;
  alineacion: 'left' | 'center' | 'right';
  estilos_token: Record<string, TokenStyle>;
}

export interface ImageLayer {
  id: number;
  tipo: 'imagen';
  nombre: string;
  visible: boolean;
  ruta: string; // URL o base64
  nx: number;
  ny: number;
  escala: number;
  rotacion: number;
}

export type Layer = TextLayer | ImageLayer;

export interface RenderSettings {
  blur: number;
  opacidad: number;
  remera: 'blanca' | 'negra';
}

export interface FontInfo {
  name: string;
  path: string;
}