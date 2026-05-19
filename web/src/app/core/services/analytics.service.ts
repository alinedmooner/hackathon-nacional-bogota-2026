import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of, forkJoin } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { RUNTIME_CONFIG } from '../config/runtime-config';

export interface UsageSeries {
  labels: string[];
  values: number[];
}

export interface UsageSnapshot {
  totalContratos: number;
  contratosPyme: number;
  pagosAdelantados: number;
}

export interface GenderBreakdown {
  labels: string[];
  values: number[];
  counts: number[];
}

export interface EntidadDinero {
  posicion: number;
  entidad: string;
  valor_total: number;
}

export interface AnomaliaFinanciera {
  posicion: number;
  id_contrato: string;
  entidad: string;
  tipo: string;
  estado: string;
  valor: number;
  sustento: string;
}

export interface Paso2Extended {
  totalVariables: number;
  variables: string[];
  registros2025: number;
  obligacionesAmbientales: number;
  pctObligacionesAmbientales: number;
  paretoSeCumple: boolean;
  paretoSustento: string;
  paretoPctTop20: number;
}

export interface AnomaliaTipoDato {
  campo: string;
  tipo_almacenado: string;
  tipo_correcto: string;
  problema: string;
}

export interface Paso1Stats {
  totalRegistros: number;
  totalColumnas: number;
  columnas: string[];
  nulosDescripcion: number;
  pctNulosDescripcion: number;
  nulosProceso: number;
  pctNulosProceso: number;
  tamanoMax: number | null;
  tamanoMin: number | null;
  tamanoMedia: number | null;
  tamanoMediana: number | null;
  fechaMax: string;
  fechaMin: string;
  rangoDias: number | null;
  rangoTexto: string | null;
}

export type RecordEntry = Record<string, string | number | null>;

export interface PaginatedContratos {
  items: RecordEntry[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  private readonly http = inject(HttpClient);
  private readonly config = inject(RUNTIME_CONFIG);

  private paso2(path: string) {
    return `${this.config.backendUrl}/paso2/analytics/${path}`;
  }

  private paso1(path: string) {
    return `${this.config.backendUrl}/paso1/analytics/${path}`;
  }

  // ── Paso 2: Charts (existing) ──────────────────────────────

  getTopDepartamentos(): Observable<UsageSeries> {
    return this.http
      .get<{ top_10: { departamento: string; total: number }[] }>(this.paso2('top-departamentos'))
      .pipe(
        map((res) => ({
          labels: res.top_10.map((d) => d.departamento),
          values: res.top_10.map((d) => d.total),
        })),
        catchError(() => of({ labels: [], values: [] }))
      );
  }

  getTiposContrato(): Observable<UsageSeries> {
    return this.http
      .get<{ top_5: { tipo: string; total: number }[] }>(this.paso2('tipos-contrato'))
      .pipe(
        map((res) => ({
          labels: res.top_5.map((t) => t.tipo),
          values: res.top_5.map((t) => t.total),
        })),
        catchError(() => of({ labels: [], values: [] }))
      );
  }

  getBrechaGenero(): Observable<GenderBreakdown> {
    return this.http
      .get<{ por_genero: { genero: string; num_contratos: number; pct_valor: number }[] }>(
        this.paso2('brecha-genero')
      )
      .pipe(
        map((res) => ({
          labels: res.por_genero.map((g) => g.genero),
          values: res.por_genero.map((g) => g.pct_valor),
          counts: res.por_genero.map((g) => g.num_contratos),
        })),
        catchError(() => of({ labels: [], values: [], counts: [] }))
      );
  }

  getModalidades(): Observable<UsageSeries> {
    return this.http
      .get<{ top_5_modalidades: { modalidad: string; total: number }[] }>(
        this.paso2('modalidad-preferida')
      )
      .pipe(
        map((res) => ({
          labels: res.top_5_modalidades.map((m) => m.modalidad),
          values: res.top_5_modalidades.map((m) => m.total),
        })),
        catchError(() => of({ labels: [], values: [] }))
      );
  }

  getSnapshot(): Observable<UsageSnapshot> {
    return forkJoin({
      total: this.http
        .get<{ total_registros: number }>(this.paso2('total-registros'))
        .pipe(catchError(() => of({ total_registros: 0 }))),
      pymes: this.http
        .get<{ contratos_pyme: number }>(this.paso2('pymes'))
        .pipe(catchError(() => of({ contratos_pyme: 0 }))),
      pagos: this.http
        .get<{ con_pago_adelantado: number }>(this.paso2('pagos-adelantados'))
        .pipe(catchError(() => of({ con_pago_adelantado: 0 }))),
    }).pipe(
      map((res) => ({
        totalContratos: res.total.total_registros,
        contratosPyme: res.pymes.contratos_pyme,
        pagosAdelantados: res.pagos.con_pago_adelantado,
      }))
    );
  }

  // ── Paso 2: Extended analytics ─────────────────────────────

  getTopEntidadesDinero(): Observable<EntidadDinero[]> {
    return this.http
      .get<{ top_3: EntidadDinero[] }>(this.paso2('top-entidades-dinero'))
      .pipe(
        map((res) => res.top_3),
        catchError(() => of([]))
      );
  }

  getAnomalasFinancieras(): Observable<{
    estadisticas: { media: number; umbral_anomalia: number };
    anomalos: AnomaliaFinanciera[];
  }> {
    return this.http
      .get<{
        estadisticas: { media: number; umbral_anomalia: number };
        top_3_anomalos: AnomaliaFinanciera[];
      }>(this.paso2('anomalias-financieras'))
      .pipe(
        map((res) => ({ estadisticas: res.estadisticas, anomalos: res.top_3_anomalos })),
        catchError(() => of({ estadisticas: { media: 0, umbral_anomalia: 0 }, anomalos: [] }))
      );
  }

  getAnomalasTiposDatos(): Observable<AnomaliaTipoDato[]> {
    return this.http
      .get<{ anomalias: AnomaliaTipoDato[] }>(this.paso2('anomalias-tipos-datos'))
      .pipe(
        map((res) => res.anomalias),
        catchError(() => of([]))
      );
  }

  getPaso2Extended(): Observable<Paso2Extended> {
    return forkJoin({
      variables: this.http
        .get<{ total_variables: number; variables: string[] }>(this.paso2('total-variables'))
        .pipe(catchError(() => of({ total_variables: 0, variables: [] }))),
      registros2025: this.http
        .get<{ registros_2025: number }>(this.paso2('registros-2025'))
        .pipe(catchError(() => of({ registros_2025: 0 }))),
      ambientales: this.http
        .get<{ con_obligacion_ambiental: number; porcentaje: number }>(
          this.paso2('obligaciones-ambientales')
        )
        .pipe(catchError(() => of({ con_obligacion_ambiental: 0, porcentaje: 0 }))),
      pareto: this.http
        .get<{
          se_cumple_pareto: boolean;
          sustento: string;
          pct_valor_concentrado_en_top_20: number;
        }>(this.paso2('pareto'))
        .pipe(
          catchError(() =>
            of({ se_cumple_pareto: false, sustento: '', pct_valor_concentrado_en_top_20: 0 })
          )
        ),
    }).pipe(
      map((res) => ({
        totalVariables: res.variables.total_variables,
        variables: res.variables.variables,
        registros2025: res.registros2025.registros_2025,
        obligacionesAmbientales: res.ambientales.con_obligacion_ambiental,
        pctObligacionesAmbientales: res.ambientales.porcentaje,
        paretoSeCumple: res.pareto.se_cumple_pareto,
        paretoSustento: res.pareto.sustento,
        paretoPctTop20: res.pareto.pct_valor_concentrado_en_top_20,
      }))
    );
  }

  // ── Paso 1: Archivos ──────────────────────────────────────

  getPaso1Stats(): Observable<Paso1Stats> {
    return forkJoin({
      total: this.http
        .get<{ total_registros: number }>(this.paso1('total-registros'))
        .pipe(catchError(() => of({ total_registros: 0 }))),
      columnas: this.http
        .get<{ total_columnas: number; columnas: string[] }>(this.paso1('total-columnas'))
        .pipe(catchError(() => of({ total_columnas: 0, columnas: [] }))),
      nulosDesc: this.http
        .get<{ nulos: number; porcentaje_nulos: number }>(this.paso1('nulos-descripcion'))
        .pipe(catchError(() => of({ nulos: 0, porcentaje_nulos: 0 }))),
      nulosProc: this.http
        .get<{ nulos: number; porcentaje_nulos: number }>(this.paso1('nulos-proceso'))
        .pipe(catchError(() => of({ nulos: 0, porcentaje_nulos: 0 }))),
      tamano: this.http
        .get<{ max: number | null; min: number | null; media: number | null; mediana: number | null }>(
          this.paso1('stats-tamano-archivo')
        )
        .pipe(catchError(() => of({ max: null, min: null, media: null, mediana: null }))),
      fechas: this.http
        .get<{
          fecha_maxima: string;
          fecha_minima: string;
          rango_dias: number | null;
          rango: string | null;
        }>(this.paso1('rango-fecha-carga'))
        .pipe(
          catchError(() =>
            of({ fecha_maxima: '', fecha_minima: '', rango_dias: null, rango: null })
          )
        ),
    }).pipe(
      map((res) => ({
        totalRegistros: res.total.total_registros,
        totalColumnas: res.columnas.total_columnas,
        columnas: res.columnas.columnas,
        nulosDescripcion: res.nulosDesc.nulos,
        pctNulosDescripcion: res.nulosDesc.porcentaje_nulos,
        nulosProceso: res.nulosProc.nulos,
        pctNulosProceso: res.nulosProc.porcentaje_nulos,
        tamanoMax: res.tamano.max,
        tamanoMin: res.tamano.min,
        tamanoMedia: res.tamano.media,
        tamanoMediana: res.tamano.mediana,
        fechaMax: res.fechas.fecha_maxima,
        fechaMin: res.fechas.fecha_minima,
        rangoDias: res.fechas.rango_dias,
        rangoTexto: res.fechas.rango,
      }))
    );
  }

  // ── Contratos list ─────────────────────────────────────────

  getContratos(page = 1, pageSize = 20): Observable<PaginatedContratos> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    return this.http
      .get<PaginatedContratos>(`${this.config.backendUrl}/contratos`, { params })
      .pipe(catchError(() => of({ items: [], total: 0, page: 1, page_size: pageSize, pages: 0 })));
  }
}
