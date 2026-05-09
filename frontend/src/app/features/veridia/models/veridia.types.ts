/**
 * Modelos de Veridia - capa de inteligencia anticorrupción.
 *
 * El frontend espera del backend un payload con elementos compatibles
 * con Cytoscape.js (nodos + aristas) más metadata específica del dominio.
 */

export type NodeType = 'persona' | 'empresa' | 'entidad' | 'contrato' | 'sancion';

export type EdgeRelation =
  | 'cargo'        // persona ocupó cargo en entidad
  | 'control'      // persona es rep. legal / accionista de empresa
  | 'contrato'     // empresa firmó contrato con entidad
  | 'sancion'      // persona/empresa fue sancionada
  | 'comparte_rl'  // dos empresas comparten representante legal
  | 'comparte_dir' // dos empresas comparten dirección física
  | 'familiar';    // vínculo familiar entre personas

export type AlertType =
  | 'sancionado_activo'
  | 'puerta_giratoria'
  | 'redes_ocultas';

export type LayoutKind = 'cose-bilkent' | 'dagre' | 'concentric' | 'circle';

/** Datos intrínsecos de un nodo (siguen el formato Cytoscape.data) */
export interface NodeData {
  id: string;
  label: string;
  type: NodeType;
  /** ID externo: cédula para personas, NIT para empresas/entidades */
  identificacion?: string;
  /** Subtítulo opcional (cargo, sector, etc.) */
  subtitle?: string;
  /** Marca al nodo como bandera roja → estilo distinto */
  flagged?: boolean;
  /** Cluster al que pertenece (para redes ocultas) */
  cluster?: string;
  /** Métricas adicionales para el panel de detalle */
  metrics?: Record<string, string | number>;
  /** Bandera específica que activó el flagged */
  alertType?: AlertType;
}

/** Datos intrínsecos de una arista */
export interface EdgeData {
  id: string;
  source: string;
  target: string;
  label?: string;
  relacion: EdgeRelation;
  /** Valor monetario asociado (para contratos) */
  valor?: number;
  /** Periodo / fecha relevante */
  periodo?: string;
  /** Flag para resaltar la arista (ej. contrato sospechoso) */
  flagged?: boolean;
}

/** Elementos en formato Cytoscape (cy.add()) */
export interface CytoscapeElement {
  data: NodeData | EdgeData;
  classes?: string;
}

/** Payload completo de una investigación */
export interface InvestigationGraph {
  /** Identificador del caso */
  id: string;
  /** Título legible */
  title: string;
  /** Tipo de alerta principal del grafo */
  alert_type: AlertType;
  /** Layout sugerido por el agente */
  layout: LayoutKind;
  /** Resumen narrativo de la investigación */
  summary: string;
  /** Hallazgos clave (bullets) */
  findings: string[];
  /** Elementos del grafo para Cytoscape */
  elements: CytoscapeElement[];
  /** Confianza de los hallazgos (0-100) */
  confidence: number;
  /** Timestamp de generación */
  generated_at: string;
}

/** Resumen de una alerta para el sidebar */
export interface AlertSummary {
  type: AlertType;
  label: string;
  description: string;
  count: number;
  color: string;
}
