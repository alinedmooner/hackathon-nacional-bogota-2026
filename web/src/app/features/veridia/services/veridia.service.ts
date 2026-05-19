import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { RUNTIME_CONFIG } from '../../../core/config/runtime-config';
import {
  AlertaResumen,
  AlertType,
  Dashboard,
  GrafoResponse,
  ListaHallazgos,
  Perfil,
} from '../models/veridia.types';
import { VeridiaMockService } from './veridia-mock.service';

/**
 * Cliente del backend Veridia.
 * Si una llamada falla (red caída, 5xx, etc) cae al mock como fallback,
 * para que la demo funcione incluso si el backend no responde.
 */
@Injectable({ providedIn: 'root' })
export class VeridiaService {
  private readonly http = inject(HttpClient);
  private readonly config = inject(RUNTIME_CONFIG);
  private readonly mock = inject(VeridiaMockService);

  private get base(): string {
    return `${this.config.backendUrl}/veridia`;
  }

  // ── Dashboard ──────────────────────────────────────────────
  getDashboard(): Observable<Dashboard> {
    return this.http
      .get<Dashboard>(`${this.base}/dashboard`)
      .pipe(catchError(() => this.mock.getDashboard()));
  }

  // ── Alertas: resumen ──────────────────────────────────────
  getResumen(type: AlertType): Observable<AlertaResumen> {
    const path = this.toPath(type);
    return this.http
      .get<AlertaResumen>(`${this.base}/alertas/${path}/resumen`)
      .pipe(catchError(() => this.mock.getResumen(type)));
  }

  // ── Alertas: lista paginada ───────────────────────────────
  getHallazgos(
    type: AlertType,
    limit = 50,
    offset = 0,
    confianza?: 'alta' | 'media',
  ): Observable<ListaHallazgos> {
    const path = this.toPath(type);
    let params = new HttpParams().set('limit', limit).set('offset', offset);
    if (confianza) params = params.set('confianza', confianza);
    return this.http
      .get<ListaHallazgos>(`${this.base}/alertas/${path}`, { params })
      .pipe(catchError(() => this.mock.getHallazgos(type, limit, offset)));
  }

  // ── Perfil ────────────────────────────────────────────────
  getPerfil(documento: string): Observable<Perfil> {
    return this.http
      .get<Perfil>(`${this.base}/perfil/${documento}`)
      .pipe(catchError(() => this.mock.getPerfil(documento)));
  }

  // ── Grafo de entidad ──────────────────────────────────────
  getGrafo(nit: string, limit = 40): Observable<GrafoResponse> {
    const params = new HttpParams().set('limit', limit);
    return this.http
      .get<GrafoResponse>(`${this.base}/grafo/entidad/${nit}`, { params })
      .pipe(catchError(() => this.mock.getGrafo(nit, limit)));
  }

  // ── Helpers ───────────────────────────────────────────────
  private toPath(type: AlertType): string {
    return {
      sancionados: 'sancionados',
      multados: 'multados',
      puerta_giratoria: 'puerta-giratoria',
    }[type];
  }
}
