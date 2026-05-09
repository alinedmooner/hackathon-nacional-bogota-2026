import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';

import {
  AlertSummary,
  AlertType,
  CytoscapeElement,
  EdgeData,
  InvestigationGraph,
  NodeData,
} from '../models/veridia.types';

/**
 * Datos sintéticos para los 3 tipos de alertas Veridia.
 * Reemplazar por llamadas reales al backend cuando esté listo.
 *
 * IMPORTANTE: nombres y NITs son ficticios. Cualquier coincidencia con
 * personas/empresas reales es accidental. NO usar en producción.
 */
@Injectable({ providedIn: 'root' })
export class VeridiaMockService {

  // ────────────────────────────────────────────────────────────
  // Resumen de alertas (para el sidebar)
  // ────────────────────────────────────────────────────────────
  getAlertSummaries(): Observable<AlertSummary[]> {
    return of([
      {
        type: 'sancionado_activo',
        label: 'Sancionado activo',
        description: 'Personas/empresas con sanción vigente y contratos en curso',
        count: 47,
        color: '#ef4444',
      },
      {
        type: 'puerta_giratoria',
        label: 'Puerta giratoria',
        description: 'Ex-funcionarios contratistas de su antigua entidad',
        count: 23,
        color: '#f59e0b',
      },
      {
        type: 'redes_ocultas',
        label: 'Redes ocultas',
        description: 'Clusters de empresas con vínculos compartidos',
        count: 12,
        color: '#a855f7',
      },
    ] as AlertSummary[]).pipe(delay(150));
  }

  // ────────────────────────────────────────────────────────────
  // Investigación según el tipo de alerta
  // ────────────────────────────────────────────────────────────
  getInvestigation(alertType: AlertType): Observable<InvestigationGraph> {
    const map: Record<AlertType, () => InvestigationGraph> = {
      sancionado_activo: () => this.buildSancionadoActivo(),
      puerta_giratoria: () => this.buildPuertaGiratoria(),
      redes_ocultas: () => this.buildRedesOcultas(),
    };
    return of(map[alertType]()).pipe(delay(250));
  }

  // ────────────────────────────────────────────────────────────
  // Escenario 1 · Sancionado Activo
  // ────────────────────────────────────────────────────────────
  private buildSancionadoActivo(): InvestigationGraph {
    const nodes: NodeData[] = [
      {
        id: 'p1', type: 'persona', label: 'Pedro M. Ramírez',
        identificacion: '79.834.221', subtitle: 'Representante Legal · Sancionado',
        flagged: true, alertType: 'sancionado_activo',
        metrics: { 'Sanciones activas': 1, Periodo: '2023-2028' },
      },
      {
        id: 'emp1', type: 'empresa', label: 'Constructora Ramírez & Cía. SAS',
        identificacion: 'NIT 900.245.118-3', subtitle: '12 años · construcción',
        flagged: true, alertType: 'sancionado_activo',
        metrics: { Empleados: 47, Capital: '$ 850M COP' },
      },
      {
        id: 'ent1', type: 'entidad', label: 'INVÍAS Cundinamarca',
        identificacion: 'NIT 800.215.807-2', subtitle: 'Entidad pública territorial',
      },
      {
        id: 'ent2', type: 'entidad', label: 'Alcaldía de Soacha',
        identificacion: 'NIT 800.094.391-8', subtitle: 'Municipio Cundinamarca',
      },
      {
        id: 'c1', type: 'contrato', label: 'Vía rural Sibaté',
        subtitle: 'CO1.PCCNTR.7421809',
        metrics: { Valor: '$ 1,840,000,000', Estado: 'En ejecución' },
      },
      {
        id: 'c2', type: 'contrato', label: 'Pavimentación K-4',
        subtitle: 'CO1.PCCNTR.7503112',
        metrics: { Valor: '$ 920,000,000', Estado: 'En ejecución' },
      },
      {
        id: 'c3', type: 'contrato', label: 'Mantenimiento puente',
        subtitle: 'CO1.PCCNTR.7611044',
        metrics: { Valor: '$ 410,000,000', Estado: 'Modificado' },
      },
      {
        id: 's1', type: 'sancion', label: 'Sanción Procuraduría',
        subtitle: 'Inhabilidad 2023-2028',
        metrics: { Falta: 'Gravísima', Resolución: 'PRO-2023-7821' },
      },
    ];

    const edges: EdgeData[] = [
      { id: 'e1', source: 'p1', target: 'emp1', relacion: 'control', label: 'Rep. Legal' },
      { id: 'e2', source: 'p1', target: 's1', relacion: 'sancion', label: 'Sancionado', flagged: true },
      { id: 'e3', source: 'emp1', target: 'c1', relacion: 'contrato', valor: 1_840_000_000 },
      { id: 'e4', source: 'emp1', target: 'c2', relacion: 'contrato', valor: 920_000_000 },
      { id: 'e5', source: 'emp1', target: 'c3', relacion: 'contrato', valor: 410_000_000 },
      { id: 'e6', source: 'c1', target: 'ent1', relacion: 'contrato' },
      { id: 'e7', source: 'c2', target: 'ent1', relacion: 'contrato' },
      { id: 'e8', source: 'c3', target: 'ent2', relacion: 'contrato' },
    ];

    return {
      id: 'inv-sa-001',
      title: 'Sancionado con contratos vigentes',
      alert_type: 'sancionado_activo',
      layout: 'cose-bilkent',
      summary:
        'El representante legal de Constructora Ramírez & Cía. SAS tiene una sanción disciplinaria activa de la Procuraduría (inhabilidad 2023-2028), pero la empresa sigue ejecutando 3 contratos vigentes con entidades públicas por $3,170 millones COP.',
      findings: [
        'Sanción disciplinaria vigente: inhabilidad por 5 años (2023-2028)',
        'Contratos en ejecución posteriores a la sanción',
        '$ 3,170 M COP comprometidos en 3 contratos activos',
        'Coincidencia confirmada por NIT y cédula',
      ],
      confidence: 96,
      generated_at: new Date().toISOString(),
      elements: this.toElements(nodes, edges),
    };
  }

  // ────────────────────────────────────────────────────────────
  // Escenario 2 · Puerta Giratoria
  // ────────────────────────────────────────────────────────────
  private buildPuertaGiratoria(): InvestigationGraph {
    const nodes: NodeData[] = [
      {
        id: 'p1', type: 'persona', label: 'María L. Gómez',
        identificacion: '52.481.302', subtitle: 'Ex-Subdirectora DPS · 2018-2022',
        flagged: true, alertType: 'puerta_giratoria',
        metrics: { 'Salida cargo': '2022-08', 'Empresa creada': '2022-10' },
      },
      {
        id: 'ent1', type: 'entidad', label: 'Departamento Prosperidad Social (DPS)',
        identificacion: 'NIT 900.477.897-1', subtitle: 'Entidad nacional',
      },
      {
        id: 'emp1', type: 'empresa', label: 'Consultoría Social SAS',
        identificacion: 'NIT 901.582.044-7', subtitle: 'Constituida oct/2022',
        flagged: true, alertType: 'puerta_giratoria',
        metrics: { 'Edad': '< 4 años', Capital: '$ 100M COP' },
      },
      {
        id: 'c1', type: 'contrato', label: 'Estudios pobreza rural',
        subtitle: 'Mod. directa · 2023',
        metrics: { Valor: '$ 380,000,000' },
      },
      {
        id: 'c2', type: 'contrato', label: 'Diagnóstico programas',
        subtitle: 'Mod. directa · 2023',
        metrics: { Valor: '$ 295,000,000' },
      },
      {
        id: 'c3', type: 'contrato', label: 'Asesoría política social',
        subtitle: 'Mod. directa · 2024',
        metrics: { Valor: '$ 510,000,000' },
      },
      {
        id: 'c4', type: 'contrato', label: 'Consultoría territorial',
        subtitle: 'Mod. directa · 2024',
        metrics: { Valor: '$ 247,000,000' },
      },
      {
        id: 'c5', type: 'contrato', label: 'Eval. impacto SISBEN',
        subtitle: 'Mod. directa · 2025',
        metrics: { Valor: '$ 615,000,000' },
      },
    ];

    const edges: EdgeData[] = [
      { id: 'e1', source: 'p1', target: 'ent1', relacion: 'cargo', label: 'Subdirectora 2018-2022', flagged: true },
      { id: 'e2', source: 'p1', target: 'emp1', relacion: 'control', label: 'Rep. Legal · constituyó' },
      { id: 'e3', source: 'emp1', target: 'c1', relacion: 'contrato', valor: 380_000_000 },
      { id: 'e4', source: 'emp1', target: 'c2', relacion: 'contrato', valor: 295_000_000 },
      { id: 'e5', source: 'emp1', target: 'c3', relacion: 'contrato', valor: 510_000_000 },
      { id: 'e6', source: 'emp1', target: 'c4', relacion: 'contrato', valor: 247_000_000 },
      { id: 'e7', source: 'emp1', target: 'c5', relacion: 'contrato', valor: 615_000_000 },
      { id: 'e8', source: 'c1', target: 'ent1', relacion: 'contrato', flagged: true },
      { id: 'e9', source: 'c2', target: 'ent1', relacion: 'contrato', flagged: true },
      { id: 'e10', source: 'c3', target: 'ent1', relacion: 'contrato', flagged: true },
      { id: 'e11', source: 'c4', target: 'ent1', relacion: 'contrato', flagged: true },
      { id: 'e12', source: 'c5', target: 'ent1', relacion: 'contrato', flagged: true },
    ];

    return {
      id: 'inv-pg-001',
      title: 'Ex-funcionaria contrata con su antigua entidad',
      alert_type: 'puerta_giratoria',
      layout: 'dagre',
      summary:
        'María L. Gómez fue Subdirectora del DPS hasta agosto 2022. En octubre del mismo año constituyó "Consultoría Social SAS", que desde 2023 ha firmado 5 contratos directos con su antigua entidad por un total de $2,047 millones COP.',
      findings: [
        'Salida del cargo público: agosto 2022',
        'Constitución empresa propia: 2 meses después',
        '5 contratos directos con la antigua entidad',
        'Modalidad: contratación directa (sin licitación pública)',
        'Total: $ 2,047 M COP en 24 meses',
      ],
      confidence: 89,
      generated_at: new Date().toISOString(),
      elements: this.toElements(nodes, edges),
    };
  }

  // ────────────────────────────────────────────────────────────
  // Escenario 3 · Redes Ocultas (cluster)
  // ────────────────────────────────────────────────────────────
  private buildRedesOcultas(): InvestigationGraph {
    const empresas = [
      'Servicios Globales SAS', 'Construcciones Andinas LTDA', 'Logística Bolívar SAS',
      'Suministros del Caribe SAS', 'Ingeniería Atlántico SAS', 'Inversiones Pacífico SA',
      'Distribuidora Tropical SAS', 'Consultora del Sur SAS',
    ];
    const entidades = [
      'Alcaldía de Riohacha', 'Gobernación de La Guajira',
      'ESE Hospital de Maicao', 'Secretaría Educación Guajira',
    ];

    const nodes: NodeData[] = [];

    // Persona compartida (contador)
    nodes.push({
      id: 'pc1', type: 'persona', label: 'Carlos A. Suárez',
      identificacion: '17.244.881', subtitle: 'Contador · 8 empresas',
      flagged: true, alertType: 'redes_ocultas', cluster: 'red-1',
      metrics: { 'Empresas vinculadas': 8 },
    });

    // 8 empresas en clúster
    empresas.forEach((nom, i) => {
      nodes.push({
        id: `emp${i + 1}`, type: 'empresa', label: nom,
        identificacion: `NIT 901.${(800 + i).toString()}.${(100 + i).toString()}-${i % 10}`,
        subtitle: 'Cra 7 # 25-32, Bogotá', cluster: 'red-1',
        flagged: true, alertType: 'redes_ocultas',
      });
    });

    // 4 entidades públicas
    entidades.forEach((nom, i) => {
      nodes.push({
        id: `ent${i + 1}`, type: 'entidad', label: nom,
        subtitle: 'Entidad territorial',
      });
    });

    const edges: EdgeData[] = [];

    // Conectar contador con cada empresa
    empresas.forEach((_, i) => {
      edges.push({
        id: `e-c${i}`, source: 'pc1', target: `emp${i + 1}`,
        relacion: 'comparte_rl', label: 'Contador', flagged: true,
      });
    });

    // Comparten dirección física (cliques entre empresas)
    for (let i = 0; i < empresas.length - 1; i++) {
      edges.push({
        id: `e-d${i}`, source: `emp${i + 1}`, target: `emp${i + 2}`,
        relacion: 'comparte_dir', label: 'Misma dirección',
      });
    }

    // Contratos rotativos: cada empresa firma con varias entidades
    let contratosCount = 0;
    empresas.forEach((_, i) => {
      const ents = [(i % 4) + 1, ((i + 1) % 4) + 1];
      ents.forEach((entIdx) => {
        contratosCount++;
        edges.push({
          id: `e-k${contratosCount}`,
          source: `emp${i + 1}`,
          target: `ent${entIdx}`,
          relacion: 'contrato',
          valor: 200_000_000 + Math.floor(Math.random() * 500_000_000),
          label: `Contrato $${(200 + Math.floor(Math.random() * 500))}M`,
        });
      });
    });

    return {
      id: 'inv-ro-001',
      title: 'Cluster de empresas con vínculos compartidos',
      alert_type: 'redes_ocultas',
      layout: 'cose-bilkent',
      summary:
        '8 empresas aparentemente independientes comparten contador, dirección física y rotan contratos entre 4 entidades públicas de La Guajira. Total: 16 contratos por aproximadamente $5,200 millones COP en 18 meses.',
      findings: [
        '8 empresas con mismo contador (Carlos A. Suárez)',
        '8 empresas con dirección registrada idéntica',
        'Contratan con 4 entidades en patrón rotativo',
        '16 contratos cruzados en 18 meses',
        '~$5,200 M COP total comprometido',
        'Patrón consistente con organización contractual coordinada',
      ],
      confidence: 84,
      generated_at: new Date().toISOString(),
      elements: this.toElements(nodes, edges),
    };
  }

  // ────────────────────────────────────────────────────────────
  // Helpers
  // ────────────────────────────────────────────────────────────
  private toElements(nodes: NodeData[], edges: EdgeData[]): CytoscapeElement[] {
    return [
      ...nodes.map((n) => ({ data: n, classes: this.classFor(n) })),
      ...edges.map((e) => ({ data: e, classes: e.flagged ? 'flagged' : '' })),
    ];
  }

  private classFor(node: NodeData): string {
    const cls: string[] = [`type-${node.type}`];
    if (node.flagged) cls.push('flagged');
    if (node.cluster) cls.push(`cluster-${node.cluster}`);
    return cls.join(' ');
  }
}
