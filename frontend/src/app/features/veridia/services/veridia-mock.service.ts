import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';

import {
  AlertaResumen,
  AlertType,
  Dashboard,
  GrafoEdge,
  GrafoNode,
  GrafoResponse,
  Hallazgo,
  ListaHallazgos,
  Perfil,
} from '../models/veridia.types';

/**
 * Mock fallback que devuelve datos sintéticos en el formato del backend
 * real. Se invoca solo si la llamada al backend falla.
 *
 * Datos ficticios. NIT, cédulas y nombres son imaginarios.
 */
@Injectable({ providedIn: 'root' })
export class VeridiaMockService {

  // ────────────────────────────────────────────────────────────
  // Dashboard
  // ────────────────────────────────────────────────────────────
  getDashboard(): Observable<Dashboard> {
    return of<Dashboard>({
      sancionados_activos: {
        total_personas: 47,
        total_contratos: 184,
        valor_total_cop: 14_820_000_000,
        interpretacion:
          '47 personas inhabilitadas por la Procuraduría tienen contratos vigentes con entidades públicas (mock)',
      },
      multados_activos: {
        total_contratistas: 23,
        total_contratos: 76,
        valor_total_cop: 5_240_000_000,
        interpretacion:
          '23 contratistas multados en SECOP I siguen contratando posteriormente (mock)',
      },
      puerta_giratoria: {
        total_personas: 12,
        total_contratos: 38,
        valor_total_cop: 3_915_000_000,
        interpretacion:
          '12 ex-funcionarios contratan con su antigua entidad tras salir del cargo (mock)',
        nota: 'Datos sintéticos · backend no disponible',
      },
      disponibilidad_datasets: {
        secop: false,
        siri: false,
        multas_secop: false,
        patrimonio: false,
      },
    }).pipe(delay(150));
  }

  // ────────────────────────────────────────────────────────────
  // Resumen por tipo de alerta
  // ────────────────────────────────────────────────────────────
  getResumen(type: AlertType): Observable<AlertaResumen> {
    const map: Record<AlertType, AlertaResumen> = {
      sancionados: {
        total_personas: 47,
        total_contratos: 184,
        valor_total_cop: 14_820_000_000,
      },
      multados: {
        total_contratistas: 23,
        total_contratos: 76,
        valor_total_cop: 5_240_000_000,
      },
      puerta_giratoria: {
        total_personas: 12,
        total_contratos: 38,
        valor_total_cop: 3_915_000_000,
      },
    };
    return of(map[type]).pipe(delay(120));
  }

  // ────────────────────────────────────────────────────────────
  // Lista de hallazgos
  // ────────────────────────────────────────────────────────────
  getHallazgos(type: AlertType, limit = 50, offset = 0): Observable<ListaHallazgos> {
    const all = this.fakeHallazgos(type);
    const slice = all.slice(offset, offset + limit);
    return of<ListaHallazgos>({
      hallazgos: slice,
      limit,
      offset,
      total_pagina: slice.length,
    }).pipe(delay(180));
  }

  // ────────────────────────────────────────────────────────────
  // Perfil de persona / empresa
  // ────────────────────────────────────────────────────────────
  getPerfil(documento: string): Observable<Perfil> {
    return of<Perfil>({
      documento,
      nivel_alerta: 'rojo',
      secop: {
        total_contratos: 8,
        valor_total_cop: 2_180_000_000,
        contratos: [],
      },
      siri: [
        { sancion: 'Inhabilidad disciplinaria', desde: '2023-04', hasta: '2028-04' },
      ],
      multas: [],
      patrimonio: [],
    }).pipe(delay(150));
  }

  // ────────────────────────────────────────────────────────────
  // Grafo de entidad
  // ────────────────────────────────────────────────────────────
  getGrafo(nit: string, _limit = 40): Observable<GrafoResponse> {
    const entidadId = `e_${nit}`;
    const nodes: GrafoNode[] = [
      {
        id: entidadId,
        label: 'INVÍAS Cundinamarca',
        group: 'entidad',
        value: 80,
        title: '<b>Entidad pública</b><br/>NIT 800.215.807-2',
      },
      ...this.fakeProveedores(nit),
    ];
    const edges: GrafoEdge[] = nodes
      .filter((n) => n.group !== 'entidad')
      .map((n) => ({
        from: entidadId,
        to: n.id,
        value: Math.max(1, Math.floor(n.value / 5)),
        title: `<b>Contratos:</b> ${n.value}`,
      }));

    return of<GrafoResponse>({
      nodes,
      edges,
      meta: {
        entidad: 'INVÍAS Cundinamarca',
        nit,
        total_contratistas: nodes.length - 1,
        alertas_rojo: nodes.filter((n) => n.group === 'sancionado' || n.group === 'alto_riesgo').length,
        alertas_naranja: nodes.filter((n) => n.group === 'multado').length,
      },
    }).pipe(delay(220));
  }

  // ────────────────────────────────────────────────────────────
  // Helpers internos
  // ────────────────────────────────────────────────────────────
  private fakeHallazgos(type: AlertType): Hallazgo[] {
    const baseEntidades = [
      { nombre: 'INVÍAS Cundinamarca', nit: '800215807' },
      { nombre: 'Alcaldía de Soacha', nit: '800094391' },
      { nombre: 'Departamento Prosperidad Social', nit: '900477897' },
      { nombre: 'Hospital San Cristóbal', nit: '800130625' },
      { nombre: 'Gobernación de La Guajira', nit: '892115006' },
    ];

    return Array.from({ length: 12 }).map((_, i) => {
      const ent = baseEntidades[i % baseEntidades.length];
      const documento = `7983${(4221 + i).toString()}`;
      const valor = 350_000_000 + Math.floor(Math.random() * 1_500_000_000);
      const id_contrato = `CO1.PCCNTR.${7421809 + i}`;
      const base: Hallazgo = {
        documento,
        id_contrato,
        fecha_de_firma: `2025-0${(i % 9) + 1}-${(10 + i).toString().padStart(2, '0')}`,
        valor_contrato: valor,
        nombre_entidad: ent.nombre,
        nit_entidad: ent.nit,
        confianza: i % 3 === 0 ? 'alta' : 'media',
      };

      if (type === 'sancionados') {
        return {
          ...base,
          nombre_sancionado: `Sancionado ${i + 1}`,
          sanciones: 'Inhabilidad disciplinaria · Procuraduría',
          fecha_inicio_sancion: '2023-04',
          fecha_fin_sancion: '2028-04',
          url_evidencia: 'https://www.procuraduria.gov.co/',
        };
      }
      if (type === 'multados') {
        return {
          ...base,
          nombre_contratista: `Contratista S.A.S. ${i + 1}`,
          valor_sancion: 12_000_000 + Math.floor(Math.random() * 80_000_000),
          fecha_inicio_sancion: '2022-08',
          url_evidencia: 'https://www.colombiacompra.gov.co/',
        };
      }
      // puerta_giratoria
      return {
        ...base,
        nombre_declarante: `Ex-funcionario ${i + 1}`,
        nombre_contratista: `Consultoría ${i + 1} SAS`,
      };
    });
  }

  private fakeProveedores(_nit: string): GrafoNode[] {
    const nombres = [
      'Constructora Andina SAS', 'Servicios del Norte LTDA', 'Suministros Bolívar SAS',
      'Ingeniería Pacífico SAS', 'Logística Tropical SA', 'Distribuidora del Sur SAS',
      'Inversiones Atlántico SAS', 'Consultora del Oriente SAS',
    ];
    const groups: Array<GrafoNode['group']> = [
      'sancionado', 'contratista', 'multado', 'contratista',
      'alto_riesgo', 'contratista', 'multado', 'contratista',
    ];
    return nombres.map((label, i) => ({
      id: `p_${i + 1}`,
      label,
      group: groups[i],
      value: 10 + Math.floor(Math.random() * 60),
      title: `<b>${label}</b><br/>${groups[i]}`,
    }));
  }
}
