/**
 * Modelos de Veridia · alineados con el backend real (ver VERIDIA_FRONTEND.md).
 */

// ── Alertas ──────────────────────────────────────────────────────────────────

export type AlertType = 'sancionados' | 'multados' | 'puerta_giratoria';

export interface AlertaResumen {
  total_personas?: number;
  total_contratistas?: number;
  total_contratos: number;
  valor_total_cop: number;
  interpretacion?: string;
  nota?: string;
}

export interface Dashboard {
  sancionados_activos: AlertaResumen;
  multados_activos: AlertaResumen;
  puerta_giratoria: AlertaResumen;
  disponibilidad_datasets: Record<string, boolean>;
}

export interface Hallazgo {
  documento: string;
  nombre_sancionado?: string;
  nombre_contratista?: string;
  nombre_declarante?: string;
  sanciones?: string;
  valor_sancion?: number;
  fecha_inicio_sancion?: string;
  fecha_fin_sancion?: string;
  url_evidencia?: string;
  id_contrato: string;
  fecha_de_firma: string;
  valor_contrato: number;
  nombre_entidad: string;
  nit_entidad: string;
  confianza: 'alta' | 'media';
}

export interface ListaHallazgos {
  hallazgos: Hallazgo[];
  limit: number;
  offset: number;
  total_pagina: number;
}

export interface Perfil {
  documento: string;
  nivel_alerta: 'rojo' | 'naranja' | 'amarillo' | 'verde';
  secop?: {
    total_contratos: number;
    valor_total_cop: number;
    contratos: any[];
  };
  siri: any[];
  multas: any[];
  patrimonio: any[];
}

// ── Grafo (formato vis-network del backend) ──────────────────────────────────

export type NodeGroup =
  | 'entidad'
  | 'contratista'
  | 'sancionado'
  | 'multado'
  | 'alto_riesgo';

export interface GrafoNode {
  id: string;
  label: string;
  group: NodeGroup;
  /** tamaño relativo: número de contratos */
  value: number;
  /** HTML para tooltip */
  title: string;
}

export interface GrafoEdge {
  from: string;
  to: string;
  value: number;
  title: string;
}

export interface GrafoResponse {
  nodes: GrafoNode[];
  edges: GrafoEdge[];
  meta: {
    entidad: string;
    nit: string;
    total_contratistas: number;
    alertas_rojo: number;
    alertas_naranja: number;
  };
}

// ── Chat / SSE ───────────────────────────────────────────────────────────────

export interface ChatRequest {
  message: string;
  conversation_id: string | null;
}

export type SseEventType =
  | 'init'
  | 'thinking'
  | 'tool_call'
  | 'tool_result'
  | 'chart'
  | 'answer'
  | 'done'
  | 'error';

export interface ChartItem {
  id: string;
  title: string;
  chart_js_spec: any;
}

export interface SseEvent {
  type: SseEventType;
  conversation_id?: string;
  iteration?: number;
  tool?: string;
  args?: Record<string, any>;
  summary?: string;
  chart?: ChartItem;
  text?: string;
  usage?: { input_tokens: number; output_tokens: number };
  latency_ms?: number;
  detail?: string;
}

// ── UI helpers ───────────────────────────────────────────────────────────────

export interface AlertSummary {
  type: AlertType;
  label: string;
  description: string;
  count: number;
  color: string;
}
