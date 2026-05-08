import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { RUNTIME_CONFIG } from '../config/runtime-config';

export interface UsageSeries {
  labels: string[];
  values: number[];
}

export interface UsageSnapshot {
  activeUsers: number;
  jobsProcessed: number;
  alerts: number;
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

  getWeeklyUsage(): Observable<UsageSeries> {
    return of({
      labels: ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom'],
      values: [120, 180, 90, 240, 260, 140, 200]
    });
  }

  getThroughput(): Observable<UsageSeries> {
    return of({
      labels: ['00h', '04h', '08h', '12h', '16h', '20h'],
      values: [20, 35, 60, 90, 70, 40]
    });
  }

  getSnapshot(): Observable<UsageSnapshot> {
    return of({
      activeUsers: 128,
      jobsProcessed: 842,
      alerts: 5
    });
  }

  getContratos(page = 1, pageSize = 20): Observable<PaginatedContratos> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    return this.http
      .get<PaginatedContratos>(`${this.config.backendUrl}/contratos`, { params })
      .pipe(catchError(() => of({ items: [], total: 0, page: 1, page_size: pageSize, pages: 0 })));
  }
}
