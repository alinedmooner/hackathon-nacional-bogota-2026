/**
 * Datos pre-grabados del caso "Alcaldía de Soacha" para el tour de onboarding.
 * Garantizan timing y narrativa consistentes en demo en vivo.
 */
import { GrafoResponse, SseEvent } from '../models/veridia.types';

/**
 * Secuencia de eventos SSE simulados con su delay (ms) entre cada uno.
 * El total suma ~5s — alineado con la narrativa del tour.
 */
export interface TimedSseEvent {
  delay: number; // ms desde el evento anterior
  event: SseEvent;
}

export const SOACHA_STREAM: TimedSseEvent[] = [
  { delay: 200, event: { type: 'init', conversation_id: 'demo-soacha' } },
  { delay: 350, event: { type: 'thinking', iteration: 1 } },
  {
    delay: 600,
    event: {
      type: 'tool_call',
      tool: 'query_secop',
      args: { entidad: 'Alcaldía de Soacha' },
    },
  },
  {
    delay: 850,
    event: {
      type: 'tool_result',
      tool: 'query_secop',
      summary: '47 cédulas únicas en 184 contratos vigentes',
    },
  },
  { delay: 250, event: { type: 'thinking', iteration: 2 } },
  {
    delay: 500,
    event: {
      type: 'tool_call',
      tool: 'check_active_sanctions',
      args: { entity_name: 'Alcaldía de Soacha' },
    },
  },
  {
    delay: 700,
    event: {
      type: 'tool_result',
      tool: 'check_active_sanctions',
      summary: '3 coincidencias en SIRI · Procuraduría',
    },
  },
  { delay: 250, event: { type: 'thinking', iteration: 3 } },
  {
    delay: 450,
    event: {
      type: 'tool_call',
      tool: 'get_person_profile',
      args: { documento: '79834221' },
    },
  },
  {
    delay: 650,
    event: {
      type: 'tool_result',
      tool: 'get_person_profile',
      summary: 'ALERTA_ROJA · 2 sanciones vigentes al firmar',
    },
  },
  {
    delay: 600,
    event: {
      type: 'answer',
      text:
        'Encontré 2 personas con sanción disciplinaria activa que firmaron contratos con la Alcaldía de Soacha:\n\n' +
        '1. Cédula 79.834.221 — inhabilidad Procuraduría 2023–2028. Firmó contrato por $1.840M COP en septiembre 2024.\n\n' +
        '2. Cédula 52.481.302 — inhabilidad activa desde 2022. Firmó contrato por $920M COP en marzo 2024.\n\n' +
        'Ambos casos son verificables en SECOP y en el portal SIRI de la Procuraduría.',
    },
  },
  {
    delay: 200,
    event: {
      type: 'done',
      conversation_id: 'demo-soacha',
      usage: { input_tokens: 1240, output_tokens: 380 },
      latency_ms: 5100,
    },
  },
];

/**
 * Grafo resultante: Alcaldía de Soacha rodeada de 8 contratistas, de los
 * cuales 2 son sancionados (rojo parpadeante).
 */
export const SOACHA_GRAFO: GrafoResponse = {
  nodes: [
    {
      id: 'e_800094391',
      label: 'Alcaldía de Soacha',
      group: 'entidad',
      value: 100,
      title:
        '<b>Alcaldía Municipal de Soacha</b><br/>' +
        'NIT 800.094.391-8<br/>' +
        'Cundinamarca · Territorial',
    },
    {
      id: 'p_79834221',
      label: 'Persona A · sancionada',
      group: 'sancionado',
      value: 32,
      title:
        '<b>Cédula 79.834.221</b><br/>' +
        'Inhabilidad Procuraduría 2023–2028<br/>' +
        '<span style="color:#fb7185">Contrato firmado en sanción vigente</span>',
    },
    {
      id: 'p_52481302',
      label: 'Persona B · sancionada',
      group: 'sancionado',
      value: 24,
      title:
        '<b>Cédula 52.481.302</b><br/>' +
        'Inhabilidad activa desde 2022<br/>' +
        '<span style="color:#fb7185">Contrato firmado en sanción vigente</span>',
    },
    {
      id: 'p_44521096',
      label: 'Persona C · multada',
      group: 'multado',
      value: 18,
      title:
        '<b>Cédula 44.521.096</b><br/>' +
        'Multa SECOP I · 2022<br/>' +
        '$15M COP',
    },
    {
      id: 'emp_900245118',
      label: 'Constructora Andina SAS',
      group: 'contratista',
      value: 28,
      title: '<b>NIT 900.245.118-3</b><br/>5 contratos · $4.2MM',
    },
    {
      id: 'emp_901582044',
      label: 'Servicios Globales SAS',
      group: 'contratista',
      value: 22,
      title: '<b>NIT 901.582.044-7</b><br/>4 contratos · $2.1MM',
    },
    {
      id: 'emp_900814221',
      label: 'Logística Andina SAS',
      group: 'contratista',
      value: 19,
      title: '<b>NIT 900.814.221-9</b><br/>3 contratos · $1.5MM',
    },
    {
      id: 'emp_901102554',
      label: 'Suministros Bolívar SAS',
      group: 'contratista',
      value: 16,
      title: '<b>NIT 901.102.554-1</b><br/>3 contratos · $980M',
    },
  ],
  edges: [
    { from: 'e_800094391', to: 'p_79834221',     value: 4, title: '<b>Contratos:</b> 1 · $1.840M (en sanción)' },
    { from: 'e_800094391', to: 'p_52481302',     value: 3, title: '<b>Contratos:</b> 1 · $920M (en sanción)' },
    { from: 'e_800094391', to: 'p_44521096',     value: 2, title: '<b>Contratos:</b> 2 · $440M' },
    { from: 'e_800094391', to: 'emp_900245118',  value: 8, title: '<b>Contratos:</b> 5 · $4.2MM' },
    { from: 'e_800094391', to: 'emp_901582044',  value: 6, title: '<b>Contratos:</b> 4 · $2.1MM' },
    { from: 'e_800094391', to: 'emp_900814221',  value: 5, title: '<b>Contratos:</b> 3 · $1.5MM' },
    { from: 'e_800094391', to: 'emp_901102554',  value: 4, title: '<b>Contratos:</b> 3 · $980M' },
  ],
  meta: {
    entidad: 'Alcaldía de Soacha',
    nit: '800094391',
    total_contratistas: 7,
    alertas_rojo: 2,
    alertas_naranja: 1,
  },
};

/** ID del nodo a destacar cuando la narrativa pide "ver evidencia". */
export const SOACHA_FOCUS_NODE_ID = 'p_79834221';
